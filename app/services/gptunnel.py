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
        
        headers = self.headers.copy()
        if custom_headers:
            for key, value in custom_headers.items():
                if key.lower() != "authorization":
                    headers[key] = value
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=request.dict(exclude_none=True),
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
        Проксирует streaming запрос к GPTunnel API с правильной обработкой SSE
        """
        url = f"{self.base_url}/chat/completions"
        request.stream = True
        
        headers = self.headers.copy()
        headers["Accept"] = "text/event-stream"
        headers["Cache-Control"] = "no-cache"
        
        if custom_headers:
            for key, value in custom_headers.items():
                if key.lower() != "authorization":
                    headers[key] = value
        
        request_data = request.dict(exclude_none=True)
        logger.info(f"Sending streaming request to GPTunnel: {url}")
        logger.debug(f"Request data: {json.dumps(request_data, ensure_ascii=False)}")
        
        timeout = httpx.Timeout(timeout=120.0, connect=30.0, read=None)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                async with client.stream(
                    "POST",
                    url,
                    json=request_data,
                    headers=headers
                ) as response:
                    logger.info(f"Stream response status: {response.status_code}")
                    response.raise_for_status()
                    
                    chunk_count = 0
                    async for line in response.aiter_lines():
                        if line:
                            chunk_count += 1
                            logger.debug(f"Received chunk {chunk_count}: {line[:100]}...")
                            
                            # GPTunnel уже отправляет в формате SSE
                            if line.startswith("data: "):
                                yield f"{line}\n\n".encode('utf-8')
                            elif line == "[DONE]":
                                yield b"data: [DONE]\n\n"
                                break
                            else:
                                # Если строка не в формате SSE, форматируем её
                                yield f"data: {line}\n\n".encode('utf-8')
                    
                    logger.info(f"Stream completed. Total chunks: {chunk_count}")
                    
                    # Убедимся, что отправляем финальное сообщение
                    if chunk_count > 0:
                        yield b"data: [DONE]\n\n"
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error in stream: {e}")
                error_msg = {
                    "error": {
                        "message": str(e),
                        "type": "http_error",
                        "code": e.response.status_code if hasattr(e, 'response') else 500
                    }
                }
                yield f"data: {json.dumps(error_msg)}\n\n".encode('utf-8')
                yield b"data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Error in stream: {e}", exc_info=True)
                error_msg = {
                    "error": {
                        "message": str(e),
                        "type": "stream_error"
                    }
                }
                yield f"data: {json.dumps(error_msg)}\n\n".encode('utf-8')
                yield b"data: [DONE]\n\n"