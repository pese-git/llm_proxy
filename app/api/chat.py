from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from typing import Optional
import logging
import json
from app.services.gptunnel import GPTunnelService
from app.api.models import list_models
from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse

router = APIRouter()
logger = logging.getLogger(__name__)
gptunnel_service = GPTunnelService()

@router.post("/v1/chat/completions")
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
                        if chunk_count <= 5 or b"[DONE]" in chunk:
                            logger.debug(f"Sending chunk {chunk_count}: {chunk[:200]}")
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
                    "Content-Type": "text/event-stream",
                    "X-Accel-Buffering": "no",
                    "Transfer-Encoding": "chunked"
                }
            )

        # Обычный запрос (без streaming)
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
