@echo off
chcp 65001 >nul
title botyaraclick

cd /d "%~dp0"

echo ==========================================
echo       Запуск игры botyaraclick...         
echo ==========================================

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ОШИБКА: Python не найден! Установите Python 3.8+ и добавьте его в PATH.
    pause
    exit /b 1
)

if not exist ".venv" if not exist "venv" (
    echo Создание виртуального окружения .venv...
    python -m venv .venv
)

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python -c "import pygame" >nul 2>nul
if %errorlevel% neq 0 (
    echo Установка зависимостей из requirements.txt...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
)

echo Запуск main.py...
python main.py

if %errorlevel% neq 0 (
    echo.
    echo Игра завершилась с ошибкой.
    pause
)
