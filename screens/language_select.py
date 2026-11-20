"""
botyaraclick - screens/language_select.py
Экран выбора языка при первом запуске.
Простой, красивый экран с флагами/названиями языков.
"""

import pygame
import math

from ui.button import Button
from ui.panel import Panel
from ui.fonts import get_font


class LanguageSelectScreen:
    """Экран выбора языка."""

    def __init__(self, screen_width, screen_height, locale_manager, save_manager):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.locale = locale_manager
        self.save = save_manager

        self.selected_language = None
        self.finished = False

        # Анимации
        self._alpha = 0
        self._target_alpha = 255
        self._title_phase = 0

        # Шрифты (системные, т.к. тема ещё не выбрана)
        self._title_font = None
        self._subtitle_font = None
        self._button_font = None

        # Кнопки языков
        self._buttons = []
        self._initialized = False

    def _init_fonts(self):
        """Инициализирует шрифты."""
        try:
            self._title_font = get_font(52, bold=True)
            self._subtitle_font = get_font(28)
            self._button_font = get_font(32)
        except pygame.error:
            self._title_font = pygame.font.SysFont("arial", 48)
            self._subtitle_font = pygame.font.SysFont("arial", 24)
            self._button_font = pygame.font.SysFont("arial", 28)

    def _init_buttons(self):
        """Создаёт кнопки для каждого доступного языка."""
        if self._initialized:
            return

        self._init_fonts()

        # Получаем доступные языки
        languages = self.locale.get_available_languages()

        if not languages:
            # Если нет языковых файлов — по умолчанию английский
            self.selected_language = "en"
            self.finished = True
            return

        # Расположение кнопок
        btn_width = 300
        btn_height = 60
        gap = 15
        total_height = len(languages) * (btn_height + gap) - gap
        start_y = self.screen_height // 2 - total_height // 2 + 40

        for i, (code, name) in enumerate(languages):
            bx = self.screen_width // 2 - btn_width // 2
            by = start_y + i * (btn_height + gap)

            btn = Button(
                bx, by, btn_width, btn_height,
                text=name,
                font=self._button_font,
                color=(50, 80, 140),
                hover_color=(70, 110, 180),
                pressed_color=(40, 65, 120),
                text_color=(230, 230, 240),
                border_radius=12,
                border_width=2,
                border_color=(80, 120, 180),
                tag=code,
            )
            self._buttons.append(btn)

        self._initialized = True

    def handle_event(self, event):
        """Обрабатывает события."""
        self._init_buttons()

        for btn in self._buttons:
            if btn.handle_event(event):
                self.selected_language = btn.tag
                self._target_alpha = 0  # Начинаем затухание
                return True

        return False

    def update(self, dt):
        """Обновляет экран."""
        self._init_buttons()

        # Анимация появления/исчезновения
        speed = 400 * dt
        if self._alpha < self._target_alpha:
            self._alpha = min(self._alpha + speed, self._target_alpha)
        elif self._alpha > self._target_alpha:
            self._alpha = max(self._alpha - speed, self._target_alpha)

        # Если затухание завершено и язык выбран
        if self.selected_language and self._alpha <= 0:
            self.finished = True

        # Анимация заголовка
        self._title_phase += dt * 2

        # Обновляем кнопки
        mouse_pos = pygame.mouse.get_pos()
        for btn in self._buttons:
            btn.update(dt, mouse_pos)

    def draw(self, surface):
        """Рисует экран выбора языка."""
        self._init_buttons()

        alpha_ratio = self._alpha / 255.0

        # Фон — тёмный градиент
        surface.fill((20, 20, 35))

        # Декоративные линии кода на фоне
        self._draw_bg_decoration(surface, alpha_ratio)

        # Заголовок "botyaraclick"
        if self._title_font:
            # Пульсация
            pulse = math.sin(self._title_phase) * 5
            title_y = self.screen_height // 2 - 180 + pulse

            title_surf = self._title_font.render(
                "botyaraclick", True, (80, 160, 255)
            )
            title_surf.set_alpha(int(self._alpha))
            title_rect = title_surf.get_rect(
                center=(self.screen_width // 2, int(title_y))
            )
            surface.blit(title_surf, title_rect)

        # Подзаголовок
        if self._subtitle_font:
            # Два языка чтобы все поняли
            sub1 = self._subtitle_font.render(
                "Select Language", True, (180, 180, 200)
            )
            sub2 = self._subtitle_font.render(
                "Выберите язык", True, (150, 150, 170)
            )

            sub1.set_alpha(int(self._alpha))
            sub2.set_alpha(int(self._alpha))

            sub1_rect = sub1.get_rect(
                center=(self.screen_width // 2,
                        self.screen_height // 2 - 120)
            )
            sub2_rect = sub2.get_rect(
                center=(self.screen_width // 2,
                        self.screen_height // 2 - 90)
            )

            surface.blit(sub1, sub1_rect)
            surface.blit(sub2, sub2_rect)

        # Кнопки
        for btn in self._buttons:
            btn.draw(surface)

    def _draw_bg_decoration(self, surface, alpha_ratio):
        """Рисует декоративные элементы на фоне."""
        if alpha_ratio <= 0:
            return

        # Тонкие линии "кода" на фоне
        font = get_font(14, family="FiraCode")
        code_lines = [
            "import pygame", "def main():", "    game.run()",
            "class Clicker:", "    money += 1", "while True:",
            "if click:", "    earn()", "# botyaraclick",
            "upgrade.buy()", "prestige()", "save_game()",
        ]

        alpha = int(25 * alpha_ratio)
        if alpha <= 0:
            return

        for i, line in enumerate(code_lines):
            x = 30 + (i % 3) * (self.screen_width // 3)
            y = 50 + (i * 57) % (self.screen_height - 100)

            text_surf = font.render(line, True, (60, 60, 90))
            text_surf.set_alpha(alpha)
            surface.blit(text_surf, (x, y))

    def resize(self, width, height):
        """Обновляет размеры при изменении окна."""
        self.screen_width = width
        self.screen_height = height
        self._buttons.clear()
        self._initialized = False
