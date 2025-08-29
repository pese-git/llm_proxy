# GPTunnel Proxy Service

FastAPI-прокси для взаимодействия с GPTunnel API. Позволяет безопасно и удобно коммуницировать с внешним API (для интеграций, разработки собственных UI и др.).

## Возможности
- Совместимость с REST API openai/gptunnel (stream и обычные запросы)
- Асинхронная обработка
- Быстрый запуск (через Docker или обычный Python)
- Модульная архитектура для расширения (middleware: логирование, авторизация и др.)

---

## Как развернуть проект

### 1. Клонировать проект

```shell
git clone <URL-ВАШЕГО-РЕПОЗИТОРИЯ>
cd llm_proxy
```

### 2. Заполнить `.env`

Пример:
```
GPTUNNEL_API_KEY=ВАШ_API_КЛЮЧ_ОТ_GPTUNNEL
GPTUNNEL_BASE_URL=https://gptunnel.ru/v1
PORT=8000
HOST=0.0.0.0
```

---

### **Вариант A. Запуск через Docker (рекомендуется)**

```shell
docker-compose up --build
```
API будет доступен на http://localhost:8000

---

### **Вариант B. Локальная разработка**

#### 1. Создайте виртуальное окружение (Python 3.12/3.11!):

```shell
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. Запуск сервера (разработка):

```shell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Production-запуск:
```shell
python run.py
```

---

### Тестирование

Для ручной проверки:
```shell
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
или
```shell
python tests/test_proxy.py
python tests/test_streaming.py
```

---

## Структура проекта

```
llm_proxy/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── chat.py
│   │   ├── health.py
│   │   └── models.py
│   ├── core/
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   └── logging.py
│   ├── middleware/
│   │   └── logging.py
│   ├── schemas/
│   │   ├── chat.py
│   │   └── model.py
│   ├── services/
│   │   └── gptunnel.py
│   └── utils/
│       └── cache.py
├── tests/
│   ├── test_proxy.py
│   └── test_streaming.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── README.md
└── ...
```

---

## Примечания

- Впервые указывайте актуальный API-ключ GPTunnel в .env
- Документация OpenAPI для интерфейса доступна на [`/docs`](http://localhost:8000/docs) после запуска сервера
- Для работы нужен Python версии **3.12 или 3.11** (3.13 не поддерживается в pydantic-core)

---

**Удачной интеграции!**
