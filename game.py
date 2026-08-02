"""
botyaraclick - game.py
Главный класс Game — управляет всеми экранами, переходами,
инициализацией систем и главным игровым циклом.

Состояния игры (стейт-машина):
- LANGUAGE_SELECT: выбор языка (первый запуск)
- MAIN_MENU: главное меню
- SAVE_SELECT: выбор слота сохранения
- PLAYING: основной игровой процесс
- PAUSED: пауза
- SETTINGS: настройки (из меню или паузы)
- UPGRADE_TREE: дерево улучшений
- THEMES_SHOP: магазин тем
- PRESTIGE: экран престижа
- ACHIEVEMENTS: достижения (будущее)
- STATISTICS: статистика (будущее)
"""

import pygame
import os
import sys

from config import (
    GAME_TITLE, DEFAULT_WIDTH, DEFAULT_HEIGHT, FPS,
    FULLSCREEN_DEFAULT, FONTS_DIR, HOTKEY_FULLSCREEN,
    BASE_DIR
)

from core.save_manager import SaveManager
from core.sound_manager import SoundManager
from locales.locale_manager import locale, t

from screens.language_select import LanguageSelectScreen
from screens.main_menu import MainMenuScreen
from screens.save_load import SaveLoadScreen
from screens.settings import SettingsScreen
from screens.game_screen import GameScreen
from screens.pause_menu import PauseMenuScreen
from screens.upgrade_tree import UpgradeTreeScreen
from screens.themes_shop import ThemesShopScreen
from screens.prestige_screen import PrestigeScreen

from data.themes import get_theme, THEME_FONTS


class GameState:
    """Перечисление состояний игры."""
    LANGUAGE_SELECT = "language_select"
    MAIN_MENU = "main_menu"
    SAVE_SELECT = "save_select"
    PLAYING = "playing"
    PAUSED = "paused"
    SETTINGS = "settings"
    SETTINGS_FROM_PAUSE = "settings_from_pause"
    UPGRADE_TREE = "upgrade_tree"
    THEMES_SHOP = "themes_shop"
    PRESTIGE = "prestige"
    QUITTING = "quitting"


class Game:
    """
    Главный класс игры.
    Управляет всем: инициализация, экраны, переходы, ввод.
    """

    def __init__(self):
        # === Pygame ===
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        # === Окно ===
        self.fullscreen = FULLSCREEN_DEFAULT
        self._display_flags = pygame.RESIZABLE

        if self.fullscreen:
            info = pygame.display.Info()
            self.screen_width = info.current_w
            self.screen_height = info.current_h
            self._display_flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        else:
            self.screen_width = DEFAULT_WIDTH
            self.screen_height = DEFAULT_HEIGHT

        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            self._display_flags
        )
        pygame.display.set_caption(GAME_TITLE)

        self.clock = pygame.time.Clock()
        self.running = True

        # === Системы ===
        self.save_manager = SaveManager()
        self.sound_manager = SoundManager()
        self.sound_manager.load_all_sounds()

        # Загружаем глобальные настройки аудио
        self.sound_manager.set_music_volume(
            self.save_manager.get_setting("music_volume", 0.7)
        )
        self.sound_manager.set_sfx_volume(
            self.save_manager.get_setting("sfx_volume", 0.7)
        )
        self.sound_manager.set_muted(
            self.save_manager.get_setting("mute_all", False)
        )

        # === Шрифты ===
        self._fonts = {}
        self._current_font_family = "Montserrat"
        self._load_fonts("Montserrat")

        # === Локализация ===
        locale._discover_locales()
        saved_lang = self.save_manager.get_language()
        if saved_lang:
            locale.load_locale(saved_lang)

        # === Состояние ===
        self.state = GameState.LANGUAGE_SELECT if self.save_manager.is_first_launch() else GameState.MAIN_MENU
        self._previous_state = None
        self._return_to_state = None  # куда вернуться после настроек

        # === Экраны ===
        self._screens = {}
        self._current_screen = None
        self._init_screens()

        # === Музыка ===
        if self.state == GameState.MAIN_MENU:
            self.sound_manager.play_music("menu_theme")

    def _load_fonts(self, font_family):
        """Загружает набор шрифтов для текущей темы."""
        font_info = THEME_FONTS.get(font_family, THEME_FONTS.get("Montserrat", {}))
        regular_file = font_info.get("regular", "Montserrat-Regular.ttf")
        bold_file = font_info.get("bold", "Montserrat-Bold.ttf")

        regular_path = os.path.join(FONTS_DIR, regular_file)
        bold_path = os.path.join(FONTS_DIR, bold_file)

        # Проверяем существование файлов
        if not os.path.exists(regular_path):
            regular_path = None  # Будет использовать системный шрифт
        if not os.path.exists(bold_path):
            bold_path = regular_path  # Используем regular вместо bold

        def make_font(path, size):
            try:
                if path:
                    return pygame.font.Font(path, size)
                else:
                    return pygame.font.Font(None, size)
            except (pygame.error, FileNotFoundError, OSError):
                return pygame.font.Font(None, size)

        self._fonts = {
            "title": make_font(bold_path, 36),
            "large": make_font(bold_path, 30),
            "money_big": make_font(bold_path, 32),
            "button": make_font(regular_path, 24),
            "subtitle": make_font(regular_path, 22),
            "normal": make_font(regular_path, 20),
            "click_text": make_font(bold_path, 42),
            "small": make_font(regular_path, 16),
            "tiny": make_font(regular_path, 14),
        }

        self._current_font_family = font_family

    def _reload_fonts_for_theme(self):
        """Перезагружает шрифты если тема изменилась."""
        if self.save_manager.save_data:
            theme_id = self.save_manager.get_save_data("current_theme", "default")
        else:
            theme_id = "default"

        theme_data = get_theme(theme_id)
        font_family = theme_data.get("font_file", "Montserrat")

        if font_family != self._current_font_family:
            self._load_fonts(font_family)
            self._reinit_screens()

    def _init_screens(self):
        """Инициализирует все экраны."""
        sw, sh = self.screen_width, self.screen_height

        self._screens = {
            GameState.LANGUAGE_SELECT: LanguageSelectScreen(
                sw, sh, locale, self.save_manager
            ),
            GameState.MAIN_MENU: MainMenuScreen(
                sw, sh, self.save_manager, self.sound_manager
            ),
            GameState.SAVE_SELECT: SaveLoadScreen(
                sw, sh, self.save_manager, self.sound_manager
            ),
            GameState.SETTINGS: SettingsScreen(
                sw, sh, self.save_manager, self.sound_manager, locale
            ),
            GameState.SETTINGS_FROM_PAUSE: SettingsScreen(
                sw, sh, self.save_manager, self.sound_manager, locale
            ),
        }

        # Экраны, зависящие от загруженного сохранения, создаются позже
        self._screens[GameState.PLAYING] = None
        self._screens[GameState.PAUSED] = None
        self._screens[GameState.UPGRADE_TREE] = None
        self._screens[GameState.THEMES_SHOP] = None
        self._screens[GameState.PRESTIGE] = None

        # Инициализируем шрифты для начальных экранов
        for key, screen in self._screens.items():
            if screen and hasattr(screen, 'init_fonts'):
                screen.init_fonts(self._fonts)

    def _reinit_screens(self):
        """Переинициализирует шрифты на всех экранах."""
        for key, screen in self._screens.items():
            if screen and hasattr(screen, 'init_fonts'):
                screen.init_fonts(self._fonts)
            if screen and hasattr(screen, '_initialized'):
                screen._initialized = False

    def _create_game_screens(self):
        """Создаёт игровые экраны (после загрузки сохранения)."""
        sw, sh = self.screen_width, self.screen_height

        # Игровой экран
        game_screen = GameScreen(
            sw, sh, self.save_manager, self.sound_manager, locale
        )
        game_screen.init_fonts(self._fonts)
        self._screens[GameState.PLAYING] = game_screen

        # Пауза
        pause_screen = PauseMenuScreen(
            sw, sh, self.save_manager, self.sound_manager,
            economy=game_screen.economy
        )
        pause_screen.init_fonts(self._fonts)
        pause_screen.set_achievement_tracker(game_screen.achievement_tracker)
        self._screens[GameState.PAUSED] = pause_screen

        # Дерево улучшений
        tree_screen = UpgradeTreeScreen(
            sw, sh, self.save_manager, self.sound_manager,
            game_screen.economy
        )
        tree_screen.init_fonts(self._fonts)
        self._screens[GameState.UPGRADE_TREE] = tree_screen

        # Магазин тем
        themes_screen = ThemesShopScreen(
            sw, sh, self.save_manager, self.sound_manager
        )
        themes_screen.init_fonts(self._fonts)
        self._screens[GameState.THEMES_SHOP] = themes_screen

        # Престиж
        prestige_screen = PrestigeScreen(
            sw, sh, self.save_manager, self.sound_manager
        )
        prestige_screen.init_fonts(self._fonts)
        self._screens[GameState.PRESTIGE] = prestige_screen

    def _switch_state(self, new_state):
        """Переключает состояние игры."""
        old_state = self.state
        self._previous_state = old_state
        self.state = new_state

        # Сбрасываем новый экран
        screen = self._screens.get(new_state)
        if screen and hasattr(screen, 'reset'):
            screen.reset()
            if hasattr(screen, 'init_fonts'):
                screen.init_fonts(self._fonts)

        # Музыка
        if new_state == GameState.MAIN_MENU:
            self.sound_manager.play_music("menu_theme")
        elif new_state == GameState.PLAYING:
            self.sound_manager.play_music("game_theme")

    # ================================================================
    # ГЛАВНЫЙ ЦИКЛ
    # ================================================================

    def run(self):
        """Запускает главный игровой цикл."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)  # Ограничиваем dt чтобы не было прыжков

            # Обработка событий
            self._handle_events()

            # Обновление
            self._update(dt)

            # Отрисовка
            self._draw()

            pygame.display.flip()

        # Выход
        self._cleanup()

    def _handle_events(self):
        """Обрабатывает все события pygame."""
        for event in pygame.event.get():
            # === Системные события ===
            if event.type == pygame.QUIT:
                self._handle_quit(shift_held=False)
                continue

            if event.type == pygame.VIDEORESIZE:
                if not self.fullscreen:
                    self.screen_width = event.w
                    self.screen_height = event.h
                    self.screen = pygame.display.set_mode(
                        (self.screen_width, self.screen_height),
                        pygame.RESIZABLE
                    )
                    self._on_resize()
                continue

            # === Горячие клавиши ===
            if event.type == pygame.KEYDOWN:
                # F11 — полный экран
                if event.key == HOTKEY_FULLSCREEN:
                    self._toggle_fullscreen()
                    continue

                # Shift+Esc или Alt+F4 — выход с предупреждением
                if event.key == pygame.K_ESCAPE:
                    mods = pygame.key.get_mods()
                    if mods & pygame.KMOD_SHIFT and self.state == GameState.PLAYING:
                        self._handle_quit(shift_held=True)
                        continue

            # === Передаём событие текущему экрану ===
            self._handle_screen_event(event)

    def _handle_screen_event(self, event):
        """Передаёт событие текущему экрану и обрабатывает результаты."""
        screen = self._screens.get(self.state)
        if not screen:
            return

        screen.handle_event(event)

    def _handle_quit(self, shift_held=False):
        """Обрабатывает выход из игры."""
        if self.state == GameState.PLAYING and self.save_manager.save_data:
            if shift_held:
                # Shift+выход — показываем предупреждение через паузу
                self._switch_state(GameState.PAUSED)
                return
            else:
                # Обычный выход — сохраняем и выходим
                self.save_manager.save_current()
                self.running = False
        else:
            self.running = False

    def _toggle_fullscreen(self):
        """Переключает полноэкранный режим."""
        self.fullscreen = not self.fullscreen

        if self.fullscreen:
            info = pygame.display.Info()
            self.screen_width = info.current_w
            self.screen_height = info.current_h
            self.screen = pygame.display.set_mode(
                (self.screen_width, self.screen_height),
                pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
            )
        else:
            self.screen_width = DEFAULT_WIDTH
            self.screen_height = DEFAULT_HEIGHT
            self.screen = pygame.display.set_mode(
                (self.screen_width, self.screen_height),
                pygame.RESIZABLE
            )

        self._on_resize()

    def _on_resize(self):
        """Обрабатывает изменение размера окна."""
        sw, sh = self.screen_width, self.screen_height
        for key, screen in self._screens.items():
            if screen and hasattr(screen, 'resize'):
                screen.resize(sw, sh)

    # ================================================================
    # ОБНОВЛЕНИЕ
    # ================================================================

    def _update(self, dt):
        """Обновляет текущий экран и обрабатывает переходы."""
        screen = self._screens.get(self.state)
        if not screen:
            return

        screen.update(dt)

        # Обрабатываем результаты экранов
        if hasattr(screen, 'finished') and screen.finished:
            self._process_screen_result()

        # Специальные проверки для игрового экрана
        if self.state == GameState.PLAYING:
            game_screen = self._screens.get(GameState.PLAYING)
            if game_screen:
                if game_screen.wants_pause:
                    game_screen.wants_pause = False
                    self._switch_state(GameState.PAUSED)

                elif game_screen.result:
                    result = game_screen.result
                    game_screen.result = None

                    if result == "tree":
                        self._switch_state(GameState.UPGRADE_TREE)
                    elif result == "achievements":
                        # Открываем через паузу
                        self._switch_state(GameState.PAUSED)
                    elif result == "themes":
                        self._switch_state(GameState.THEMES_SHOP)
                    elif result == "statistics":
                        self._switch_state(GameState.PAUSED)
                    elif result == "prestige":
                        self._switch_state(GameState.PRESTIGE)

    def _process_screen_result(self):
        """Обрабатывает результат завершённого экрана."""
        screen = self._screens.get(self.state)
        if not screen:
            return

        result = getattr(screen, 'result', None)

        # ============================================================
        # LANGUAGE SELECT
        # ============================================================
        if self.state == GameState.LANGUAGE_SELECT:
            lang = screen.selected_language
            if lang:
                locale.load_locale(lang)
                self.save_manager.set_language(lang)
                self.save_manager.set_first_launch_done()
                self._switch_state(GameState.MAIN_MENU)
                self.sound_manager.play_music("menu_theme")

        # ============================================================
        # MAIN MENU
        # ============================================================
        elif self.state == GameState.MAIN_MENU:
            if result == "play":
                self._switch_state(GameState.SAVE_SELECT)
            elif result == "continue":
                # Загружаем последний слот
                last_slot = self.save_manager.get_setting("last_slot")
                if last_slot and self.save_manager.slot_exists(last_slot):
                    self.save_manager.load_game(last_slot)
                    self._reload_fonts_for_theme()
                    self._create_game_screens()
                    self._switch_state(GameState.PLAYING)
                else:
                    self._switch_state(GameState.SAVE_SELECT)
            elif result == "settings":
                self._return_to_state = GameState.MAIN_MENU
                self._switch_state(GameState.SETTINGS)
            elif result == "quit":
                self.running = False

        # ============================================================
        # SAVE SELECT
        # ============================================================
        elif self.state == GameState.SAVE_SELECT:
            if result == "back":
                self._switch_state(GameState.MAIN_MENU)
            elif isinstance(result, dict):
                action = result.get("action")
                slot = result.get("slot")

                if action == "new":
                    self.save_manager.new_game(slot)
                    self._reload_fonts_for_theme()
                    self._create_game_screens()
                    self._switch_state(GameState.PLAYING)
                elif action == "load":
                    self.save_manager.load_game(slot)
                    self._reload_fonts_for_theme()
                    self._create_game_screens()
                    self._switch_state(GameState.PLAYING)

        # ============================================================
        # SETTINGS
        # ============================================================
        elif self.state in (GameState.SETTINGS, GameState.SETTINGS_FROM_PAUSE):
            if result == "back":
                return_to = self._return_to_state or GameState.MAIN_MENU
                self._switch_state(return_to)
                self._return_to_state = None
            elif result == "language_changed":
                # Переинициализируем всё с новым языком
                self._reinit_screens()
                # Не выходим из настроек — просто обновляем

        # ============================================================
        # PAUSED
        # ============================================================
        elif self.state == GameState.PAUSED:
            if result == "resume":
                self.state = GameState.PLAYING
            elif result == "settings":
                self._return_to_state = GameState.PAUSED
                self._switch_state(GameState.SETTINGS_FROM_PAUSE)
            elif result == "main_menu":
                # Сохранение уже обработано в pause_menu
                self._screens[GameState.PLAYING] = None
                self._screens[GameState.PAUSED] = None
                self._switch_state(GameState.MAIN_MENU)

        # ============================================================
        # UPGRADE TREE
        # ============================================================
        elif self.state == GameState.UPGRADE_TREE:
            if result == "back":
                self.state = GameState.PLAYING
                # Пересчитываем экономику
                game_screen = self._screens.get(GameState.PLAYING)
                if game_screen:
                    ach_bonuses = game_screen.achievement_tracker.get_achievement_bonuses()
                    game_screen.economy.recalculate(ach_bonuses)

        # ============================================================
        # THEMES SHOP
        # ============================================================
        elif self.state == GameState.THEMES_SHOP:
            themes_screen = self._screens.get(GameState.THEMES_SHOP)
            if result == "back":
                self.state = GameState.PLAYING
                # Если тема изменилась — перезагружаем
                if themes_screen and themes_screen.theme_changed:
                    self._reload_fonts_for_theme()
                    game_screen = self._screens.get(GameState.PLAYING)
                    if game_screen:
                        game_screen.reload_theme()
                        game_screen._initialized = False

        # ============================================================
        # PRESTIGE
        # ============================================================
        elif self.state == GameState.PRESTIGE:
            if result == "back":
                self.state = GameState.PLAYING
            elif result == "prestige_done":
                # Пересоздаём игровые экраны после престижа
                self._reload_fonts_for_theme()
                self._create_game_screens()
                self._switch_state(GameState.PLAYING)

    # ================================================================
    # ОТРИСОВКА
    # ================================================================

    def _draw(self):
        """Рисует текущий экран."""
        # Получаем текущую тему
        theme = None
        if self.save_manager.save_data:
            theme_id = self.save_manager.get_save_data("current_theme", "default")
            theme = get_theme(theme_id)

        # Рисуем в зависимости от состояния
        if self.state == GameState.LANGUAGE_SELECT:
            screen = self._screens.get(GameState.LANGUAGE_SELECT)
            if screen:
                screen.draw(self.screen)

        elif self.state == GameState.MAIN_MENU:
            screen = self._screens.get(GameState.MAIN_MENU)
            if screen:
                screen.draw(self.screen)

        elif self.state == GameState.SAVE_SELECT:
            screen = self._screens.get(GameState.SAVE_SELECT)
            if screen:
                screen.draw(self.screen, theme)

        elif self.state in (GameState.SETTINGS, GameState.SETTINGS_FROM_PAUSE):
            screen = self._screens.get(self.state)
            if screen:
                screen.draw(self.screen, theme)

        elif self.state == GameState.PLAYING:
            screen = self._screens.get(GameState.PLAYING)
            if screen:
                screen.draw(self.screen)

        elif self.state == GameState.PAUSED:
            # Рисуем игру за паузой
            game_screen = self._screens.get(GameState.PLAYING)
            if game_screen:
                game_screen.draw(self.screen)
            # Поверх — пауза
            pause_screen = self._screens.get(GameState.PAUSED)
            if pause_screen:
                pause_screen.draw(self.screen, theme)

        elif self.state == GameState.UPGRADE_TREE:
            screen = self._screens.get(GameState.UPGRADE_TREE)
            if screen:
                screen.draw(self.screen, theme)

        elif self.state == GameState.THEMES_SHOP:
            screen = self._screens.get(GameState.THEMES_SHOP)
            if screen:
                screen.draw(self.screen, theme)

        elif self.state == GameState.PRESTIGE:
            screen = self._screens.get(GameState.PRESTIGE)
            if screen:
                screen.draw(self.screen, theme)

    # ================================================================
    # CLEANUP
    # ================================================================

    def _cleanup(self):
        """Завершение работы."""
        # Сохраняем если есть активная игра
        if self.save_manager.save_data and self.save_manager.current_slot:
            self.save_manager.save_current()

        self.save_manager.save_global()
        self.sound_manager.stop_music(fadeout_ms=500)
        pygame.mixer.quit()
        pygame.quit()
