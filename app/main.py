from fastapi import FastAPI, HTTPException, Header, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Any
import logging
import json  # <-- Добавьте этот импорт
import time  # <-- И этот тоже
from app.models import (
    ChatCompletionRequest, 
    ChatCompletionResponse,
    ModelsResponse
)
from app.services.gptunnel import GPTunnelService
from app.config import get_settings

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Инициализация приложения
app = FastAPI(
    title="GPTunnel Proxy Service",
    description="Proxy service for GPTunnel API",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Инициализация сервиса
gptunnel_service = GPTunnelService()

# Кэш для моделей (обновляется каждые 5 минут)
models_cache = {"data": None, "timestamp": 0}

@app.get("/")
async def root():
    return {
        "service": "GPTunnel Proxy",
        "status": "active",
        "endpoints": {
            "chat_completions": "/v1/chat/completions",
            "models": "/v1/models",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/v1/models", response_model=ModelsResponse)
async def list_models():
    """
    Получает и проксирует список доступных моделей из GPTunnel
    """
    try:
        current_time = time.time()
        
        # Проверяем кэш (обновляем каждые 5 минут)
        if models_cache["data"] and (current_time - models_cache["timestamp"]) < 300:
            logger.info("Returning cached models list")
            return models_cache["data"]
        
        # Получаем свежий список моделей
        logger.info("Fetching fresh models list from GPTunnel")
        models = await gptunnel_service.get_models()
        
        # Обновляем кэш
        models_cache["data"] = models
        models_cache["timestamp"] = current_time
        
        logger.info(f"Successfully fetched {len(models.data)} models")
        return models
        
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        # Возвращаем кэшированные данные, если они есть
        if models_cache["data"]:
            logger.info("Returning cached models due to error")
            return models_cache["data"]
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    """
    Получает информацию о конкретной модели
    """
    try:
        models = await list_models()
        for model in models.data:
            if model.id == model_id:
                return model
        
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching model {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/completions")
async def create_chat_completion(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Проксирует запросы к GPTunnel API для создания chat completion
    """
    try:
        body = await request.json()
        logger.info(f"Received request body: {json.dumps(body, ensure_ascii=False)[:500]}...")
        
        chat_request = ChatCompletionRequest(**body)
        
        # Проверяем, что модель доступна
        models = await list_models()
        model_ids = [m.id for m in models.data]
        
        if chat_request.model not in model_ids:
            logger.warning(f"Model {chat_request.model} not in available models: {model_ids}")
        
        logger.info(f"Processing request for model: {chat_request.model}")
        logger.info(f"Stream mode: {chat_request.stream}")
        logger.info(f"Messages count: {len(chat_request.messages)}")
        
        # Проверка на streaming
        if chat_request.stream:
            logger.info("Starting streaming response...")
            
            async def stream_generator():
                try:
                    logger.info("Stream generator started")
                    chunk_count = 0
                    
                    async for chunk in gptunnel_service.create_chat_completion_stream(chat_request):
                        chunk_count += 1
                        logger.debug(f"Sending chunk {chunk_count}: {chunk[:100] if len(chunk) > 100 else chunk}")
                        yield chunk
                        
                    logger.info(f"Stream generator completed. Total chunks sent: {chunk_count}")
                    
                except Exception as e:
                    logger.error(f"Error in stream generator: {e}", exc_info=True)
                    error_data = json.dumps({"error": {"message": str(e), "type": "stream_error"}})
                    yield f"data: {error_data}\n\n".encode('utf-8')
                    yield b"data: [DONE]\n\n"
            
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache, no-transform",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Content-Type": "text/event-stream"
                }
            )
        
        # Обычный запрос
        logger.info("Processing non-streaming request...")
        response = await gptunnel_service.create_chat_completion(chat_request)
        
        # Добавляем информацию о стоимости в логи
        if hasattr(response, 'usage'):
            logger.info(f"Request completed. Tokens: {response.usage.total_tokens}, Cost: {response.usage.total_cost}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Логируем запрос
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Обрабатываем запрос
    response = await call_next(request)
    
    # Логируем ответ и время выполнения
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - Time: {process_time:.3f}s")
    
    # Добавляем заголовок с временем обработки
    response.headers["X-Process-Time"] = str(process_time)
    
    return response