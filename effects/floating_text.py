"""
botyaraclick - effects/floating_text.py
Всплывающие числа и текст при кликах, покупках, ивентах.

Примеры:
- "+$1" — обычный клик
- "+$100" — мощный клик
- "CRIT! +$500" — критический удар
- "+$1,000" — покупка
- "-30% $/sec" — дебафф
"""

import pygame
import random
import math


class FloatingText:
    """Один всплывающий текст."""

    __slots__ = [
        'x', 'y', 'text', 'color', 'font_size',
        'vx', 'vy', 'lifetime', 'max_lifetime',
        'alpha', 'scale', 'target_scale',
        'gravity', 'style', 'outline_color',
        'wobble_speed', 'wobble_amp', 'wobble_phase'
    ]

    def __init__(self, x, y, text, color=(255, 255, 255),
                 font_size=18, style="normal"):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.font_size = font_size
        self.style = style

        # Начальные параметры зависят от стиля
        if style == "crit":
            self.vx = random.uniform(-30, 30)
            self.vy = -120
            self.lifetime = 1.5
            self.gravity = 50
            self.scale = 0.5
            self.target_scale = 1.8
            self.outline_color = (0, 0, 0)
            self.wobble_speed = 15
            self.wobble_amp = 3
        elif style == "big":
            self.vx = random.uniform(-20, 20)
            self.vy = -100
            self.lifetime = 1.2
            self.gravity = 40
            self.scale = 0.8
            self.target_scale = 1.3
            self.outline_color = (0, 0, 0)
            self.wobble_speed = 10
            self.wobble_amp = 2
        elif style == "event":
            self.vx = 0
            self.vy = -60
            self.lifetime = 2.0
            self.gravity = 10
            self.scale = 0.8
            self.target_scale = 1.1
            self.outline_color = (0, 0, 0)
            self.wobble_speed = 5
            self.wobble_amp = 1
        elif style == "negative":
            self.vx = random.uniform(-15, 15)
            self.vy = -80
            self.lifetime = 1.2
            self.gravity = 30
            self.scale = 1.0
            self.target_scale = 1.0
            self.outline_color = (80, 0, 0)
            self.wobble_speed = 8
            self.wobble_amp = 2
        else:  # normal
            self.vx = random.uniform(-40, 40)
            self.vy = random.uniform(-110, -70)
            self.lifetime = 0.9
            self.gravity = 30
            self.scale = 1.0
            self.target_scale = 1.0
            self.outline_color = None
            self.wobble_speed = 0
            self.wobble_amp = 0

        self.max_lifetime = self.lifetime
        self.alpha = 255
        self.wobble_phase = random.uniform(0, math.pi * 2)

    def update(self, dt):
        """Обновляет позицию и состояние."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.lifetime -= dt

        # Прозрачность
        life_ratio = max(0, self.lifetime / self.max_lifetime)
        if life_ratio < 0.3:
            self.alpha = int(255 * (life_ratio / 0.3))
        else:
            self.alpha = 255

        # Масштаб (плавное увеличение)
        diff = self.target_scale - self.scale
        self.scale += diff * min(8.0 * dt, 1.0)

        # Покачивание
        if self.wobble_amp > 0:
            self.wobble_phase += self.wobble_speed * dt

    @property
    def alive(self):
        return self.lifetime > 0


class FloatingTextManager:
    """
    Менеджер всплывающих текстов.
    Создаёт, обновляет и рисует всплывающие числа.
    """

    def __init__(self, max_texts=50, enabled=True):
        """
        Параметры:
            max_texts: максимум одновременных текстов
            enabled: включены ли эффекты
        """
        self.texts = []
        self.max_texts = max_texts
        self.enabled = enabled

        # Кеш шрифтов по размерам
        self._font_cache = {}
        self._base_font_name = None

    def set_font(self, font_name_or_path):
        """Устанавливает базовый шрифт."""
        self._base_font_name = font_name_or_path
        self._font_cache.clear()

    def _get_font(self, size):
        """Получает шрифт нужного размера из кеша."""
        size = max(8, int(size))
        if size not in self._font_cache:
            try:
                if self._base_font_name:
                    self._font_cache[size] = pygame.font.Font(
                        self._base_font_name, size
                    )
                else:
                    self._font_cache[size] = pygame.font.Font(None, size)
            except (pygame.error, FileNotFoundError):
                self._font_cache[size] = pygame.font.Font(None, size)
        return self._font_cache[size]

    def add_click(self, x, y, amount, is_crit=False, colors=None):
        """Добавляет текст при клике."""
        if not self.enabled:
            return

        if is_crit:
            text = f"CRIT! +${self._format_number(amount)}"
            color = (255, 200, 0) if not colors else colors[0]
            style = "crit"
            font_size = 28
        else:
            text = f"+${self._format_number(amount)}"
            if colors:
                color = colors[0]
            else:
                color = (80, 220, 120)
            style = "normal"
            font_size = 18

            # Размер шрифта зависит от суммы
            if amount >= 1_000_000:
                font_size = 24
                style = "big"
            elif amount >= 10_000:
                font_size = 22
                style = "big"
            elif amount >= 100:
                font_size = 20

        self._add(x, y, text, color, font_size, style)

    def add_passive(self, x, y, amount):
        """Добавляет текст от пассивного дохода (менее заметный)."""
        if not self.enabled:
            return

        text = f"+${self._format_number(amount)}"
        self._add(x, y, text, (100, 180, 100), 14, "normal")

    def add_event_text(self, x, y, text, positive=True):
        """Добавляет текст при ивенте."""
        if not self.enabled:
            return

        if positive:
            color = (100, 255, 150)
        else:
            color = (255, 100, 100)

        self._add(x, y, text, color, 22, "event")

    def add_negative(self, x, y, text):
        """Добавляет текст для негативных эффектов."""
        if not self.enabled:
            return

        self._add(x, y, text, (255, 80, 80), 20, "negative")

    def add_custom(self, x, y, text, color=(255, 255, 255),
                   font_size=18, style="normal"):
        """Добавляет произвольный текст."""
        if not self.enabled:
            return

        self._add(x, y, text, color, font_size, style)

    def _add(self, x, y, text, color, font_size, style):
        """Внутреннее добавление текста."""
        ft = FloatingText(x, y, text, color, font_size, style)

        if len(self.texts) >= self.max_texts:
            self.texts.pop(0)

        self.texts.append(ft)

    def update(self, dt):
        """Обновляет все тексты."""
        for ft in self.texts:
            ft.update(dt)

        self.texts = [ft for ft in self.texts if ft.alive]

    def draw(self, surface):
        """Рисует все тексты."""
        for ft in self.texts:
            if ft.alpha <= 0:
                continue

            font = self._get_font(ft.font_size * ft.scale)
            if not font:
                continue

            # Покачивание
            wobble_x = 0
            if ft.wobble_amp > 0:
                wobble_x = math.sin(ft.wobble_phase) * ft.wobble_amp

            draw_x = int(ft.x + wobble_x)
            draw_y = int(ft.y)

            # Обводка (для crit и big)
            if ft.outline_color:
                outline_surf = font.render(ft.text, True, ft.outline_color)
                outline_surf.set_alpha(max(0, ft.alpha - 30))
                for ox, oy in [(-1, -1), (1, -1), (-1, 1), (1, 1), (-2, 0), (2, 0), (0, -2), (0, 2)]:
                    outline_rect = outline_surf.get_rect(
                        center=(draw_x + ox, draw_y + oy)
                    )
                    surface.blit(outline_surf, outline_rect)

            # Основной текст
            text_surf = font.render(ft.text, True, ft.color)
            text_surf.set_alpha(max(0, ft.alpha))
            text_rect = text_surf.get_rect(center=(draw_x, draw_y))
            surface.blit(text_surf, text_rect)

    def _format_number(self, number):
        """Форматирует число для отображения."""
        if number >= 1_000_000_000_000:
            return f"{number / 1_000_000_000_000:.1f}T"
        elif number >= 1_000_000_000:
            return f"{number / 1_000_000_000:.1f}B"
        elif number >= 1_000_000:
            return f"{number / 1_000_000:.1f}M"
        elif number >= 1_000:
            return f"{number / 1_000:.1f}K"
        elif number >= 10:
            return f"{number:.0f}"
        elif number >= 1:
            return f"{number:.1f}"
        else:
            return f"{number:.2f}"

    def clear(self):
        """Удаляет все тексты."""
        self.texts.clear()

    @property
    def count(self):
        return len(self.texts)
