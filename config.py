"""
botyaraclick - config.py
Глобальные константы и настройки игры.
"""

import os
import sys

# === ПУТИ ===
# Все пути относительно директории скриптов
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")
SAVES_DIR = os.path.join(BASE_DIR, "saves")
LOCALES_DIR = os.path.join(BASE_DIR, "locales")

# Создаём директории если не существуют
for d in [ASSETS_DIR, FONTS_DIR, SOUNDS_DIR, MUSIC_DIR, SAVES_DIR, LOCALES_DIR]:
    os.makedirs(d, exist_ok=True)

# === ОКНО ===
GAME_TITLE = "botyaraclick"
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
FPS = 60
FULLSCREEN_DEFAULT = True

# === ЦВЕТА (дефолтная тема "Business") ===
COLOR_BG = (30, 30, 40)
COLOR_PANEL = (40, 40, 55)
COLOR_PANEL_DARK = (25, 25, 35)
COLOR_PANEL_LIGHT = (55, 55, 75)
COLOR_BUTTON = (50, 100, 200)
COLOR_BUTTON_HOVER = (70, 130, 240)
COLOR_BUTTON_PRESSED = (40, 80, 170)
COLOR_BUTTON_DISABLED = (60, 60, 80)
COLOR_TEXT = (230, 230, 240)
COLOR_TEXT_DIM = (150, 150, 170)
COLOR_TEXT_BRIGHT = (255, 255, 255)
COLOR_MONEY = (80, 220, 120)
COLOR_ACCENT = (50, 150, 255)
COLOR_DANGER = (220, 60, 60)
COLOR_WARNING = (240, 180, 40)
COLOR_SUCCESS = (60, 200, 100)
COLOR_CRIT = (255, 200, 0)
COLOR_SCROLLBAR = (80, 80, 100)
COLOR_SCROLLBAR_THUMB = (120, 120, 150)
COLOR_TOOLTIP_BG = (20, 20, 30, 220)
COLOR_OVERLAY = (0, 0, 0, 150)

# === ЭКОНОМИКА ===
STARTING_MONEY = 0.0
STARTING_CLICK_POWER = 1.0
PRICE_MULTIPLIER = 1.15  # множитель роста цен
CRIT_BASE_CHANCE = 0.0  # базовый шанс крита (0%)
CRIT_BASE_MULTIPLIER = 2.0  # базовый множитель крита

# === ПРЕСТИЖ ===
PRESTIGE_THRESHOLD = 500_000_000  # $500M для первого престижа
PRESTIGE_FORMULA_DIVISOR = 500_000_000  # RP = floor(sqrt(total / divisor))

# === ИВЕНТЫ ===
EVENT_MIN_INTERVAL = 45  # секунд минимум между ивентами
EVENT_MAX_INTERVAL = 120  # секунд максимум
EVENT_GOLDEN_DURATION = 3.0  # секунд на поимку золотого объекта
EVENT_BUFF_SHORT = 15  # короткий бафф
EVENT_BUFF_MEDIUM = 30  # средний бафф
EVENT_BUFF_LONG = 60  # длинный бафф
EVENT_DEBUFF_SHORT = 10  # короткий дебафф
EVENT_DEBUFF_MEDIUM = 15  # средний дебафф
EVENT_DEBUFF_LONG = 20  # длинный дебафф

# === СОХРАНЕНИЕ ===
MAX_SAVE_SLOTS = 5
AUTOSAVE_INTERVAL = 30  # секунд
GLOBAL_SAVE_FILE = "global.json"

# === UI РАЗМЕРЫ ===
TOP_PANEL_HEIGHT = 60
BOTTOM_PANEL_HEIGHT = 50
SIDE_PANEL_WIDTH = 320
BUTTON_HEIGHT = 45
BUTTON_PADDING = 8
SCROLL_SPEED = 30
TOOLTIP_DELAY = 0.5  # секунд до показа тултипа
NOTIFICATION_DURATION = 3.0  # секунд
NOTIFICATION_SLIDE_SPEED = 5  # пикселей за кадр

# === АНИМАЦИИ ===
CLICK_SCALE_AMOUNT = 0.9  # сжатие при клике (90%)
CLICK_SCALE_SPEED = 0.15  # скорость восстановления
PARTICLE_LIFETIME = 1.0  # секунд жизни частицы
PARTICLE_COUNT = 8  # частиц за клик
FLOATING_TEXT_SPEED = 2.0  # скорость подъёма текста
FLOATING_TEXT_LIFETIME = 1.0  # секунд жизни текста
ERA_TRANSITION_DURATION = 3.0  # секунд анимация смены эры

# === ШРИФТЫ (размеры) ===
FONT_SIZE_SMALL = 14
FONT_SIZE_NORMAL = 18
FONT_SIZE_MEDIUM = 22
FONT_SIZE_LARGE = 28
FONT_SIZE_TITLE = 36
FONT_SIZE_HUGE = 48
FONT_SIZE_MEGA = 72

# === ГОРЯЧИЕ КЛАВИШИ ===
import pygame
HOTKEY_PAUSE = pygame.K_ESCAPE
HOTKEY_CLICK = pygame.K_SPACE
HOTKEY_SAVE = pygame.K_F5
HOTKEY_FULLSCREEN = pygame.K_F11

# === ФОРМАТЫ ЧИСЕЛ ===
NUMBER_FORMAT_STANDARD = "standard"  # 1,000,000
NUMBER_FORMAT_SHORT = "short"  # 1.00M
NUMBER_FORMAT_SCIENTIFIC = "scientific"  # 1.00e6

NUMBER_SUFFIXES = [
    "", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc",
    "No", "Dc", "UDc", "DDc", "TDc", "QaDc", "QiDc", "SxDc",
    "SpDc", "OcDc", "NoDc", "Vg"
]

# === ЭРЫ ===
ERA_COUNT = 7
