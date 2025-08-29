from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logging
from app.api.chat import router as chat_router
from app.api.models import router as models_router
from app.api.health import router as health_router
from app.middleware.logging import log_requests

# Настройка логирования
setup_logging()

app = FastAPI(
    title="GPTunnel Proxy Service",
    description="Proxy service for GPTunnel API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Middleware логирования
app.middleware("http")(log_requests)

# Подключаем роутеры
app.include_router(health_router)
app.include_router(models_router)
app.include_router(chat_router)