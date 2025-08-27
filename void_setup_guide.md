# Настройка Void IDE для работы с GPTunnel Proxy

## 🚀 Быстрый старт

1. **Запустите прокси сервис:**
   ```bash
   ./start.sh
   ```

2. **В Void IDE добавьте новую модель:**
   - Откройте настройки Void IDE
   - Перейдите в раздел "AI Providers"
   - Добавьте новую кастомную модель

3. **Настройки для Void IDE:**
   ```
   API Type: OpenAI Compatible
   Base URL: http://localhost:8000/v1
   API Key: ваш-gptunnel-api-key (из .env файла)
   Model: gpt-4o-mini (или любая другая из списка)
   ```

## 📋 Доступные модели

Сервис поддерживает множество моделей, вот рекомендуемые:

- **gpt-4o-mini** - быстрая и недорогая
- **gpt-4o** - более мощная версия  
- **gpt-3.5-turbo** - классическая модель
- **llama4-maverick** - мощная open-source модель
- **qwen3-8b** - компактная и эффективная
- **deepseek-3.1** - хорошая для кодирования

## ⚙️ Конфигурация Void IDE

### Вариант 1: Через UI
1. Settings → AI Providers → Add Custom Provider
2. Заполните поля:
   - Name: `GPTunnel Local`
   - API Base: `http://localhost:8000/v1`
   - API Key: `ваш-api-key-из-.env`
   - Select Model: выберите нужную модель

### Вариант 2: Через конфиг файл
Добавьте в конфигурацию Void IDE:
```json
{
  "ai": {
    "providers": [
      {
        "name": "GPTunnel Local",
        "type": "openai",
        "baseURL": "http://localhost:8000/v1",
        "apiKey": "ваш-api-key-из-.env",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
      }
    ]
  }
}
```

## 🧪 Тестирование подключения

Проверьте, что все работает:

```bash
# Проверка здоровья
curl http://localhost:8000/health

# Список моделей
curl http://localhost:8000/v1/models

# Тестовый запрос
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Привет"}]
  }'
```

## 🔧 Возможные проблемы

### ❌ Connection refused
Убедитесь, что сервис запущен:
```bash
./start.sh
```

### ❌ Invalid API Key
Проверьте файл `.env` - API ключ должен быть правильным

### ❌ Model not available
Проверьте список доступных моделей:
```bash
curl http://localhost:8000/v1/models
```

## 💡 Особенности работы

- **Streaming поддержка**: Void IDE будет получать ответы по мере генерации
- **Кэширование**: Список моделей кэшируется на 5 минут
- **Логирование**: Все запросы логируются в `logs/app.log`
- **CORS**: Настроен для работы из браузера

## 📊 Мониторинг

Сервис предоставляет:
- Документация API: http://localhost:8000/docs
- Health check: http://localhost:8000/health  
- Логи: смотрите в папке `logs/`

Теперь вы можете использовать все возможности GPTunnel через Void IDE с локальным прокси! 🎉