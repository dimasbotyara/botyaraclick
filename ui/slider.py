"""
botyaraclick - ui/slider.py
Ползунок для настроек (громкость и т.д.).
"""

import pygame


class Slider:
    """Горизонтальный ползунок для выбора значения 0.0-1.0."""

    def __init__(self, x, y, width, height=6,
                 value=0.5, min_value=0.0, max_value=1.0,
                 label="", label_font=None,
                 track_color=None, fill_color=None, thumb_color=None,
                 label_color=None, value_format="{:.0%}",
                 on_change=None, enabled=True, visible=True):
        """
        Параметры:
            x, y: позиция
            width: ширина
            height: высота трека
            value: начальное значение
            min_value, max_value: диапазон
            label: подпись слева
            label_font: шрифт подписи
            track_color: цвет трека
            fill_color: цвет заполненной части
            thumb_color: цвет ползунка
            value_format: формат отображения значения
            on_change: callback(value) при изменении
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.value = value
        self.min_value = min_value
        self.max_value = max_value
        self.label = label
        self.label_font = label_font
        self._track_color = track_color
        self._fill_color = fill_color
        self._thumb_color = thumb_color
        self._label_color = label_color
        self.value_format = value_format
        self.on_change = on_change
        self.enabled = enabled
        self.visible = visible

        # Состояние
        self._dragging = False
        self._hovered = False
        self._thumb_radius = max(height, 8)

        # Полная высота (с учётом подписи)
        self.total_height = height + 25  # место для подписи

    def _get_track_rect(self):
        """Прямоугольник трека."""
        label_offset = 0
        if self.label and self.label_font:
            label_offset = self.label_font.size(self.label)[0] + 15

        return pygame.Rect(
            self.x + label_offset,
            self.y + self._thumb_radius - self.height // 2,
            self.width - label_offset,
            self.height
        )

    def _get_thumb_pos(self):
        """Позиция центра ползунка."""
        track = self._get_track_rect()
        ratio = (self.value - self.min_value) / (self.max_value - self.min_value)
        thumb_x = track.x + int(track.width * ratio)
        thumb_y = track.centery
        return thumb_x, thumb_y

    def _get_thumb_rect(self):
        """Прямоугольник ползунка для проверки попадания."""
        tx, ty = self._get_thumb_pos()
        r = self._thumb_radius
        return pygame.Rect(tx - r, ty - r, r * 2, r * 2)

    def _pos_to_value(self, mouse_x):
        """Преобразует позицию мыши в значение."""
        track = self._get_track_rect()
        ratio = (mouse_x - track.x) / max(track.width, 1)
        ratio = max(0.0, min(1.0, ratio))
        return self.min_value + ratio * (self.max_value - self.min_value)

    def handle_event(self, event) -> bool:
        """Обрабатывает события."""
        if not self.visible or not self.enabled:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            thumb_rect = self._get_thumb_rect()
            track_rect = self._get_track_rect()

            # Расширяем зону клика
            expanded_track = track_rect.inflate(0, 20)

            if thumb_rect.collidepoint(event.pos):
                self._dragging = True
                return True
            elif expanded_track.collidepoint(event.pos):
                # Клик по треку — прыжок к позиции
                self._dragging = True
                self.value = self._pos_to_value(event.pos[0])
                if self.on_change:
                    self.on_change(self.value)
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._dragging:
                self._dragging = False
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self._dragging:
                new_value = self._pos_to_value(event.pos[0])
                if new_value != self.value:
                    self.value = new_value
                    if self.on_change:
                        self.on_change(self.value)
                return True

            # Hover
            thumb_rect = self._get_thumb_rect()
            self._hovered = thumb_rect.collidepoint(event.pos)

        return False

    def update(self, dt):
        """Обновляет состояние."""
        pass  # Анимации можно добавить позже

    def draw(self, surface, theme=None):
        """Рисует ползунок."""
        if not self.visible:
            return

        # Цвета
        if theme:
            track_c = self._track_color or theme.get("scrollbar_bg", (80, 80, 100))
            fill_c = self._fill_color or theme.get("accent_color", (50, 150, 255))
            thumb_c = self._thumb_color or theme.get("text_bright", (255, 255, 255))
            label_c = self._label_color or theme.get("text_color", (230, 230, 240))
        else:
            track_c = self._track_color or (80, 80, 100)
            fill_c = self._fill_color or (50, 150, 255)
            thumb_c = self._thumb_color or (255, 255, 255)
            label_c = self._label_color or (230, 230, 240)

        if not self.enabled:
            fill_c = track_c

        track_rect = self._get_track_rect()
        thumb_x, thumb_y = self._get_thumb_pos()

        # Подпись
        if self.label and self.label_font:
            label_surf = self.label_font.render(self.label, True, label_c)
            label_rect = label_surf.get_rect(
                midleft=(self.x, track_rect.centery)
            )
            surface.blit(label_surf, label_rect)

        # Трек (фон)
        pygame.draw.rect(
            surface, track_c, track_rect,
            border_radius=self.height // 2
        )

        # Заполненная часть
        fill_rect = pygame.Rect(
            track_rect.x, track_rect.y,
            thumb_x - track_rect.x, track_rect.height
        )
        if fill_rect.width > 0:
            pygame.draw.rect(
                surface, fill_c, fill_rect,
                border_radius=self.height // 2
            )

        # Ползунок
        radius = self._thumb_radius
        if self._dragging:
            radius = int(radius * 1.3)
        elif self._hovered:
            radius = int(radius * 1.15)

        # Тень ползунка
        pygame.draw.circle(surface, (0, 0, 0, 50), (thumb_x, thumb_y + 1), radius)
        # Основной ползунок
        pygame.draw.circle(surface, thumb_c, (thumb_x, thumb_y), radius)
        # Обводка
        pygame.draw.circle(surface, fill_c, (thumb_x, thumb_y), radius, 2)

        # Отображение значения справа
        if self.label_font:
            if self.value_format:
                try:
                    value_text = self.value_format.format(self.value)
                except (ValueError, KeyError):
                    value_text = f"{self.value:.2f}"
            else:
                value_text = f"{self.value:.2f}"
            value_surf = self.label_font.render(value_text, True, label_c)
            value_rect = value_surf.get_rect(
                midleft=(track_rect.right + 10, track_rect.centery)
            )
            surface.blit(value_surf, value_rect)
