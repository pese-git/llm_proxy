#!/bin/bash

# Скрипт запуска GPTunnel Proxy Service
echo "🚀 Запуск GPTunnel Proxy Service..."

# Активация виртуального окружения
if [ -d "venv" ]; then
    echo "📦 Активация виртуального окружения..."
    source venv/bin/activate
else
    echo "❌ Виртуальное окружение не найдено. Создайте его: python -m venv venv"
    exit 1
fi

# Проверка переменных окружения
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден"
    exit 1
fi

# Проверка зависимостей
echo "🔍 Проверка зависимостей..."
pip install -r requirements.txt

# Запуск сервиса
echo "🌐 Запуск сервера на http://localhost:8000"
echo "📖 Документация: http://localhost:8000/docs"
echo "🩺 Health check: http://localhost:8000/health"
echo "📋 Модели: http://localhost:8000/v1/models"
echo ""
echo "Для остановки нажмите Ctrl+C"

python run.py