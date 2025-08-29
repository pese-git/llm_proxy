# Используем официальный Python базовый образ (рекомендуем Python 3.12)
FROM python:3.12-slim

WORKDIR /code

# Скопировать зависимости отдельно для кэширования слоев Docker
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем всё приложение
COPY ./app ./app
COPY .env ./

# Открываем порт
EXPOSE 8000

# Запуск FastAPI-прокси через Uvicorn
CMD [ "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" ]
