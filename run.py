import uvicorn
import logging
from app.config import get_settings

from app.logging_config import setup_logging

# В начале файла
setup_logging(logging.DEBUG)  # Для отладки используйте DEBUG

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level="debug"
    )
