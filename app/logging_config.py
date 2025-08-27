import logging
import sys

def setup_logging(level=logging.INFO):
    """Настройка логирования с детальным форматом"""
    
    # Формат логов
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Настройка корневого логгера
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/app.log", encoding='utf-8')
        ]
    )
    
    # Настройка уровней для различных модулей
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Для отладки streaming установите DEBUG
    logging.getLogger("app.services.gptunnel").setLevel(logging.DEBUG)
    logging.getLogger("app.main").setLevel(logging.DEBUG)