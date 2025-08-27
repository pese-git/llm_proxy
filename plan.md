# Пошаговая инструкция разработки proxy-сервиса для GPTunnel на Python (FastAPI)

## Шаг 1: Настройка окружения

### 1.1 Создание виртуального окружения
```bash
python -m venv venv
# Активация на Windows
venv\Scripts\activate
# Активация на Linux/Mac
source venv/bin/activate
```

### 1.2 Установка зависимостей
```bash
pip install fastapi uvicorn httpx python-dotenv pydantic
```

## Шаг 2: Структура проекта

Создайте следующую структуру файлов:
```
gptunnel-proxy/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── config.py
│   └── services/
│       ├── __init__.py
│       └── gptunnel.py
├── .env
├── requirements.txt
└── README.md
```

## Шаг 3: Создание файла конфигурации

### 3.1 Файл `.env`
```env
GPTUNNEL_API_KEY=YOUR_API_KEY_HERE
GPTUNNEL_BASE_URL=https://gptunnel.ru/v1
PORT=8000
HOST=0.0.0.0
```

### 3.2 Файл `app/config.py`
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    gptunnel_api_key: str
    gptunnel_base_url: str = "https://gptunnel.ru/v1"
    port: int = 8000
    host: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
```

## Шаг 4: Создание моделей данных

### Файл `app/models.py`
```python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class MessageRole(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"

class Message(BaseModel):
    role: MessageRole
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-3.5-turbo"
    messages: List[Message]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    user: Optional[str] = None

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_cost: float
    completion_cost: float
    total_cost: float

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Usage
```

## Шаг 5: Создание сервиса для работы с GPTunnel API

### Файл `app/services/gptunnel.py`
```python
import httpx
from typing import Optional, Dict, Any
from app.config import get_settings
from app.models import ChatCompletionRequest, ChatCompletionResponse
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
    
    async def create_chat_completion(
        self, 
        request: ChatCompletionRequest,
        custom_headers: Optional[Dict[str, str]] = None
    ) -> ChatCompletionResponse:
        """
        Проксирует запрос к GPTunnel API
        """
        url = f"{self.base_url}/chat/completions"
        
        # Объединяем заголовки
        headers = self.headers.copy()
        if custom_headers:
            # Добавляем кастомные заголовки, кроме Authorization
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
    ):
        """
        Проксирует streaming запрос к GPTunnel API
        """
        url = f"{self.base_url}/chat/completions"
        request.stream = True
        
        headers = self.headers.copy()
        if custom_headers:
            for key, value in custom_headers.items():
                if key.lower() != "authorization":
                    headers[key] = value
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                url,
                json=request.dict(exclude_none=True),
                headers=headers,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk
```

## Шаг 6: Создание основного приложения FastAPI

### Файл `app/main.py`
```python
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import logging
from app.models import ChatCompletionRequest, ChatCompletionResponse
from app.services.gptunnel import GPTunnelService
from app.config import get_settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
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
)

# Инициализация сервиса
gptunnel_service = GPTunnelService()

@app.get("/")
async def root():
    return {
        "service": "GPTunnel Proxy",
        "status": "active",
        "endpoints": {
            "chat_completions": "/v1/chat/completions",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
):
    """
    Проксирует запросы к GPTunnel API для создания chat completion
    """
    try:
        # Можно добавить свою логику авторизации здесь
        custom_headers = {}
        
        # Если нужно передать дополнительные заголовки
        if x_api_key:
            custom_headers["X-API-Key"] = x_api_key
        
        # Проверка на streaming
        if request.stream:
            stream_generator = gptunnel_service.create_chat_completion_stream(
                request, 
                custom_headers
            )
            return StreamingResponse(
                stream_generator,
                media_type="text/event-stream"
            )
        
        # Обычный запрос
        response = await gptunnel_service.create_chat_completion(
            request,
            custom_headers
        )
        
        logger.info(f"Successfully processed request for model: {request.model}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/completions/stream")
async def create_chat_completion_stream(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Endpoint специально для streaming запросов
    """
    try:
        request.stream = True
        stream_generator = gptunnel_service.create_chat_completion_stream(request)
        
        return StreamingResponse(
            stream_generator,
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"Error in streaming: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response
```

## Шаг 7: Создание файла requirements.txt

### Файл `requirements.txt`
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.1
python-dotenv==1.0.0
pydantic==2.4.2
pydantic-settings==2.0.3
```

## Шаг 8: Запуск сервиса

### 8.1 Для разработки
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 8.2 Создание файла для production запуска `run.py`
```python
import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level="info"
    )
```

## Шаг 9: Тестирование proxy-сервиса

### 9.1 Создание файла `test_proxy.py`
```python
import httpx
import asyncio
import json

async def test_proxy():
    url = "http://localhost:8000/v1/chat/completions"
    
    payload = {
        "model": "gpt-3.5-turbo",
        "max_tokens": 100,
        "messages": [
            {
                "role": "system",
                "content": "My name is Robert."
            },
            {
                "role": "user",
                "content": "как тебя зовут"
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(test_proxy())
```

### 9.2 Тестирование через curl
```bash
curl --request POST \
  --url http://localhost:8000/v1/chat/completions \
  --header 'Content-Type: application/json' \
  --data '{
    "model": "gpt-3.5-turbo",
    "max_tokens": 100,
    "messages": [
        {
            "role": "system",
            "content": "My name is Robert."
        },
        {
            "role": "user",
            "content": "как тебя зовут"
        }
    ]
}'
```

## Шаг 10: Дополнительные улучшения (опционально)

### 10.1 Добавление кэширования
```python
from functools import lru_cache
import hashlib
import json

class CacheService:
    def __init__(self):
        self.cache = {}
    
    def get_cache_key(self, request: ChatCompletionRequest) -> str:
        request_str = json.dumps(request.dict(), sort_keys=True)
        return hashlib.md5(request_str.encode()).hexdigest()
    
    def get(self, key: str):
        return self.cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        self.cache[key] = value
```

### 10.2 Добавление rate limiting
```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/v1/chat/completions")
@limiter.limit("10/minute")
async def create_chat_completion(request: Request, ...):
    # ваш код
```

Готово! Теперь у вас есть полнофункциональный proxy-сервис для GPTunnel API на FastAPI.