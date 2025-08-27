# GPTunnel Proxy Service

Этот проект представляет собой FastAPI-прокси для взаимодействия с GPTunnel API. Он позволяет безопасно и удобно коммуницировать с внешним API (например, для интеграций на стороне клиента, разработки собственных UI и др.)

## Основные возможности
- REST API с поддержкой stream- и обычных запросов openai/gptunnel-совместимого формата
- Асинхронная работа
- Простой старт и подключение
- Возможность быстрого расширения middleware (логирование, авторизация и пр.)

---

## Как развернуть проект

### 1. Клонируйте репозиторий (или скачайте проект)

```bash
git clone <URL-ВАШЕГО-РЕПОЗИТОРИЯ>
cd llm_proxy
```

### 2. Создайте виртуальное окружение

В MacOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```
В Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Установите зависимости

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Заполните файл переменных окружения `.env`

Пример содержимого файла `.env`:
```
GPTUNNEL_API_KEY=ВАШ_API_КЛЮЧ_ОТ_GPTUNNEL
GPTUNNEL_BASE_URL=https://gptunnel.ru/v1
PORT=8000
HOST=0.0.0.0
```

- Получить API-ключ можно в сервисе GPTunnel.

### 5. Запустите сервер (разработка)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Запуск для production

```bash
python run.py
```

---

## Тестирование

Пример запроса через curl:
```bash
curl --request POST \
  --url http://localhost:8000/v1/chat/completions \
  --header 'Content-Type: application/json' \
  --data '{
    "model": "gpt-3.5-turbo",
    "max_tokens": 100,
    "messages": [
        {"role": "system", "content": "My name is Robert."},
        {"role": "user", "content": "как тебя зовут"}
    ]
}'
```

Или выполните тестовый python-скрипт:
```bash
python test_proxy.py
```

---

## Структура проекта

```
llm_proxy/
 ├── app/
 │     ├── __init__.py
 │     ├── main.py
 │     ├── models.py
 │     ├── config.py
 │     └── services/
 │           ├── __init__.py
 │           └── gptunnel.py
 ├── .env
 ├── requirements.txt
 ├── run.py
 ├── test_proxy.py
 └── README.md
```

---

## Примечания
- При первом запуске удостоверьтесь, что указали актуальный API-ключ GPTunnel
- Для production-релиза рекомендуется запуск через `run.py` (там используются переменные окружения из .env)
- Документация по доступным эндпоинтам автоматически доступна по адресу [`/docs`](http://localhost:8000/docs) после старта сервера

---

**Удачного использования!**
