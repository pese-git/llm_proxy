import httpx
import json
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from app.config import get_settings
from app.models import ChatCompletionRequest, ChatCompletionResponse, ModelsResponse
import logging

logger = logging.getLogger(__name__)

class GPTunnelService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.gptunnel_base_url
        self.headers = {
            "Authorization": self.settings.gptunnel_api_key,
            "Content-Type": "application/json"
        }
    
    async def get_models(self) -> ModelsResponse:
        """Получает список доступных моделей из GPTunnel API"""
        url = f"{self.base_url}/models"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return ModelsResponse(**response.json())
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred while fetching models: {e}")
                raise Exception(f"GPTunnel API error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"Error fetching models: {e}")
                raise
    
    async def create_chat_completion(
        self, 
        request: ChatCompletionRequest,
        custom_headers: Optional[Dict[str, str]] = None
    ) -> ChatCompletionResponse:
        """Проксирует запрос к GPTunnel API"""
        url = f"{self.base_url}/chat/completions"
        
        # Убираем stream из запроса для обычного режима
        request_data = request.dict(exclude_none=True)
        request_data['stream'] = False
        
        headers = self.headers.copy()
        if custom_headers:
            for key, value in custom_headers.items():
                if key.lower() != "authorization":
                    headers[key] = value
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=request_data,
                    headers=headers,
                    timeout=60.0
                )
                response.raise_for_status()
                return ChatCompletionResponse(**response.json())
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred: {e}")
                raise Exception(f"GPTunnel API error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                raise

    async def create_chat_completion_stream(
        self,
        request: ChatCompletionRequest,
        custom_headers: Optional[Dict[str, str]] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Создает streaming ответ, получая полный ответ от GPTunnel и эмулируя streaming
        """
        try:
            # Получаем полный ответ от GPTunnel (так как их API не поддерживает настоящий streaming)
            logger.info("Getting full response from GPTunnel to simulate streaming...")
            
            # Делаем обычный запрос
            url = f"{self.base_url}/chat/completions"
            request_data = request.dict(exclude_none=True)
            request_data['stream'] = False  # GPTunnel не поддерживает настоящий streaming
            
            headers = self.headers.copy()
            if custom_headers:
                for key, value in custom_headers.items():
                    if key.lower() != "authorization":
                        headers[key] = value
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    json=request_data,
                    headers=headers
                )
                response.raise_for_status()
                full_response = response.json()
            
            logger.info(f"Got response from GPTunnel: {json.dumps(full_response, ensure_ascii=False)[:500]}...")
            
            # Проверяем наличие контента
            if not full_response.get("choices") or not full_response["choices"][0].get("message"):
                logger.error("No content in response")
                yield f"data: {json.dumps({'error': 'No content in response'})}\n\n".encode('utf-8')
                yield b"data: [DONE]\n\n"
                return
            
            content = full_response["choices"][0]["message"]["content"]
            model = full_response.get("model", request.model)
            response_id = full_response.get("id", "chatcmpl-proxy")
            created = full_response.get("created", 1234567890)
            
            logger.info(f"Streaming content length: {len(content)} characters")
            
            # Эмулируем streaming, отправляя текст частями
            # Разбиваем по словам для более естественного streaming
            words = content.split(' ')
            chunk_size = 3  # Отправляем по 3 слова за раз
            
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:min(i + chunk_size, len(words))]
                chunk_text = ' '.join(chunk_words)
                
                # Добавляем пробел после каждого чанка, кроме последнего
                if i + chunk_size < len(words):
                    chunk_text += ' '
                
                # Формируем chunk в формате OpenAI streaming
                chunk_data = {
                    "id": response_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "content": chunk_text
                            },
                            "finish_reason": None
                        }
                    ]
                }
                
                yield f"data: {json.dumps(chunk_data)}\n\n".encode('utf-8')
                await asyncio.sleep(0.01)  # Небольшая задержка для эмуляции streaming
            
            # Отправляем финальный chunk с finish_reason
            final_chunk = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }
                ]
            }
            
            yield f"data: {json.dumps(final_chunk)}\n\n".encode('utf-8')
            
            # Отправляем [DONE]
            yield b"data: [DONE]\n\n"
            
            logger.info("Streaming completed successfully")
            
        except Exception as e:
            logger.error(f"Error in streaming: {e}", exc_info=True)
            error_chunk = {
                "error": {
                    "message": str(e),
                    "type": "stream_error"
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n".encode('utf-8')
            yield b"data: [DONE]\n\n"