# botyaraclick - Windows PowerShell launcher script

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "      Запуск игры botyaraclick...         " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Проверка наличия Python
$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python -ErrorAction SilentlyContinue
}

if (-not $python) {
    Write-Host "ОШИБКА: Python не найден! Установите Python 3.8+ и добавьте его в PATH." -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода..."
    exit 1
}

# Проверка / создание виртуального окружения
if (-not (Test-Path ".venv") -and -not (Test-Path "venv")) {
    Write-Host "Создание виртуального окружения .venv..." -ForegroundColor Yellow
    & $python.Source -m venv .venv
}

# Активация venv
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
} elif (Test-Path "venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
}

# Проверка pygame
& python -c "import pygame" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Установка зависимостей из requirements.txt..." -ForegroundColor Yellow
    & python -m pip install --upgrade pip
    & pip install -r requirements.txt
}

Write-Host "Запуск main.py..." -ForegroundColor Green
& python main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Игра завершилась с ошибкой." -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода..."
}
