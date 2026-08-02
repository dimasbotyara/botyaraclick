#!/usr/bin/env bash

# botyaraclick - Linux/macOS launcher script

cd "$(dirname "$0")"

echo "=========================================="
echo "      Запуск игры botyaraclick...         "
echo "=========================================="

# Поиск Python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "ОШИБКА: Python не найден! Установите Python 3.8+ и повторите попытку."
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

# Проверка / создание виртуального окружения
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo "Виртуальное окружение не найдено. Создание .venv..."
    $PYTHON_CMD -m venv .venv
fi

# Активация виртуального окружения
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Проверка зависимости pygame
python -c "import pygame" &>/dev/null
if [ $? -ne 0 ]; then
    echo "Установка зависимостей из requirements.txt..."
    python -m pip install --upgrade pip
    pip install -r requirements.txt
fi

# Запуск игры
echo "Запуск main.py..."
python main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Игра завершилась с ошибкой."
    read -p "Нажмите Enter для выхода..."
fi
