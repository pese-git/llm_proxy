import logging
import sys
import os

def setup_logging(level=logging.INFO):
    """Настройка логирования с детальным форматом и поддержкой file/stdout"""

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    handlers = [logging.StreamHandler(sys.stdout)]

    # Если хотим лог в файл
    logs_dir = os.path.join(os.getcwd(), "logs")
    try:
        os.makedirs(logs_dir, exist_ok=True)
        handlers.append(logging.FileHandler(os.path.join(logs_dir, "app.log"), encoding='utf-8'))
    except Exception as e:
        print("Не удалось создать директорию logs для логов:", e)

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers
    )
    
    # Настройка уровней для сторонних модулей (уменьшить шум)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    # Для разработки: можно снять ниже до DEBUG
    logging.getLogger("app.services.gptunnel").setLevel(logging.INFO)
    logging.getLogger("app.api.chat").setLevel(logging.INFO)
