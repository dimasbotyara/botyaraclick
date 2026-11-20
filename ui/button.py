"""
botyaraclick - ui/button.py
Универсальный класс кнопки с поддержкой:
- Анимации наведения и нажатия
- Отключённого состояния
- Иконок (текстовых emoji)
- Скруглённых углов
- Тултипов
"""

import pygame
import math
import time

from ui import style


class Button:
    """Универсальная кнопка с анимациями."""

    def __init__(self, x, y, width, height, text="",
                 color=None, hover_color=None, pressed_color=None,
                 disabled_color=None, text_color=None, text_color_disabled=None,
                 font=None, font_size=18, icon="",
                 border_radius=8, border_width=0, border_color=None,
                 enabled=True, visible=True, tooltip="",
                 on_click=None, tag=None,
                 anchor="topleft", padding_x=15, padding_y=8,
                 auto_width=False, min_width=0):
        """
        Параметры:
            x, y: позиция
            width, height: размер
            text: текст на кнопке
            color: цвет фона (по умолчанию из темы)
            hover_color: цвет при наведении
            pressed_color: цвет при нажатии
            disabled_color: цвет когда отключена
            text_color: цвет текста
            font: pygame.font.Font объект
            icon: текстовая иконка (emoji)
            border_radius: скругление углов
            border_width: толщина границы
            border_color: цвет границы
            enabled: активна ли кнопка
            visible: видима ли кнопка
            tooltip: текст подсказки
            on_click: callback функция при клике
            tag: любые пользовательские данные
            anchor: "topleft", "center", "midtop"
            padding_x, padding_y: внутренние отступы
            auto_width: автоматически подстраивать ширину под текст
            min_width: минимальная ширина при auto_width
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.icon = icon
        self.tooltip_text = tooltip
        self.on_click = on_click
        self.tag = tag
        self.anchor = anchor
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.auto_width = auto_width
        self.min_width = min_width

        # Цвета (None = будут заполнены из темы)
        self._color = color
        self._hover_color = hover_color
        self._pressed_color = pressed_color
        self._disabled_color = disabled_color
        self._text_color = text_color
        self._text_color_disabled = text_color_disabled
        self._border_color = border_color

        # Стиль
        self.border_radius = border_radius
        self.border_width = border_width
        self.font = font
        self.font_size = font_size

        # Состояние
        self.enabled = enabled
        self.visible = visible
        self.hovered = False
        self.pressed = False
        self._was_pressed = False

        # Анимации
        self._hover_progress = 0.0  # 0..1 плавное наведение
        self._press_scale = 1.0     # масштаб при нажатии
        self._press_target = 1.0
        self._glow_phase = 0.0      # фаза свечения

        # Кеш
        self._rect = None
        self._needs_update = True

        self._update_rect()

    def _update_rect(self):
        """Пересчитывает прямоугольник кнопки."""
        if self.anchor == "center":
            self._rect = pygame.Rect(0, 0, self.width, self.height)
            self._rect.center = (self.x, self.y)
        elif self.anchor == "midtop":
            self._rect = pygame.Rect(0, 0, self.width, self.height)
            self._rect.midtop = (self.x, self.y)
        elif self.anchor == "midbottom":
            self._rect = pygame.Rect(0, 0, self.width, self.height)
            self._rect.midbottom = (self.x, self.y)
        else:  # topleft
            self._rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def set_position(self, x, y):
        """Изменяет позицию кнопки."""
        self.x = x
        self.y = y
        self._update_rect()

    def set_size(self, width, height):
        """Изменяет размер кнопки."""
        self.width = width
        self.height = height
        self._update_rect()

    def set_text(self, text):
        """Изменяет текст кнопки."""
        self.text = text
        if self.auto_width and self.font:
            text_w = self.font.size(self.text)[0]
            icon_w = self.font.size(self.icon)[0] if self.icon else 0
            gap = 8 if self.icon else 0
            new_width = text_w + icon_w + gap + self.padding_x * 2
            self.width = max(new_width, self.min_width)
            self._update_rect()

    def get_colors(self, theme=None):
        """Возвращает актуальные цвета (из темы или заданные)."""
        if theme:
            color = self._color or theme.get("button_color", (50, 100, 200))
            hover = self._hover_color or theme.get("button_hover", (70, 130, 240))
            pressed = self._pressed_color or theme.get("button_pressed", (40, 80, 170))
            disabled = self._disabled_color or theme.get("button_disabled", (60, 60, 80))
            text = self._text_color or theme.get("text_bright", (255, 255, 255))
            text_dis = self._text_color_disabled or theme.get("text_dim", (150, 150, 170))
            border = self._border_color or theme.get("panel_border", (60, 60, 80))
        else:
            color = self._color or (50, 100, 200)
            hover = self._hover_color or (70, 130, 240)
            pressed = self._pressed_color or (40, 80, 170)
            disabled = self._disabled_color or (60, 60, 80)
            text = self._text_color or (255, 255, 255)
            text_dis = self._text_color_disabled or (150, 150, 170)
            border = self._border_color or (60, 60, 80)

        return color, hover, pressed, disabled, text, text_dis, border

    def update(self, dt, mouse_pos):
        """Обновляет состояние кнопки (анимации)."""
        if not self.visible:
            return

        # Проверяем наведение
        if self._rect and self.enabled:
            self.hovered = self._rect.collidepoint(mouse_pos)
        else:
            self.hovered = False

        # Плавное наведение
        target_hover = 1.0 if self.hovered else 0.0
        speed = 8.0 * dt
        if self._hover_progress < target_hover:
            self._hover_progress = min(self._hover_progress + speed, target_hover)
        else:
            self._hover_progress = max(self._hover_progress - speed, target_hover)

        # Анимация нажатия (пружинный масштаб)
        if self.pressed:
            self._press_target = 0.92
        else:
            self._press_target = 1.0

        diff = self._press_target - self._press_scale
        self._press_scale += diff * min(12.0 * dt, 1.0)

        # Свечение (для особых кнопок)
        self._glow_phase += dt * 2.0
        if self._glow_phase > math.pi * 2:
            self._glow_phase -= math.pi * 2

    def handle_event(self, event) -> bool:
        """
        Обрабатывает событие.
        Возвращает True если кнопка была нажата.
        """
        if not self.visible or not self.enabled:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._rect and self._rect.collidepoint(event.pos):
                self.pressed = True
                self._was_pressed = True
                return False  # ещё не клик, только нажатие

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._was_pressed:
                self._was_pressed = False
                self.pressed = False
                if self._rect and self._rect.collidepoint(event.pos):
                    # Клик произошёл!
                    if self.on_click:
                        self.on_click(self)
                    return True

        return False

    def draw(self, surface, theme=None, font_override=None, offset=(0, 0)):
        """Рисует кнопку на поверхности."""
        if not self.visible:
            return

        color, hover_color, pressed_color, disabled_color, \
            text_color, text_dis_color, border_color = self.get_colors(theme)

        # Определяем текущий цвет
        if not self.enabled:
            current_color = disabled_color
            current_text_color = text_dis_color
        elif self.pressed:
            current_color = pressed_color
            current_text_color = text_color
        else:
            # Интерполяция между обычным и hover цветом
            current_color = self._lerp_color(color, hover_color, self._hover_progress)
            current_text_color = text_color

        # Применяем масштаб нажатия
        draw_rect = self._rect.copy()
        draw_rect.x += offset[0]
        draw_rect.y += offset[1]

        if self._press_scale != 1.0:
            scaled_w = int(draw_rect.width * self._press_scale)
            scaled_h = int(draw_rect.height * self._press_scale)
            cx, cy = draw_rect.center
            draw_rect = pygame.Rect(0, 0, scaled_w, scaled_h)
            draw_rect.center = (cx, cy)

        # Мягкая тень при наведении
        if self.enabled and self._hover_progress > 0:
            style.draw_soft_rect(
                surface,
                pygame.Rect(draw_rect.x, draw_rect.y + 3,
                            draw_rect.width, draw_rect.height),
                (0, 0, 0), int(45 * self._hover_progress),
                radius=self.border_radius
            )

        # Фон кнопки: лёгкий вертикальный градиент вместо плоского цвета
        top_color = style.lighten(current_color, 0.10)
        bottom_color = style.darken(current_color, 0.12)
        radius = min(self.border_radius, min(draw_rect.width, draw_rect.height) // 2)

        panel = style.rounded_gradient(
            (max(1, draw_rect.width), max(1, draw_rect.height)),
            top_color, bottom_color, radius
        )
        surface.blit(panel, draw_rect.topleft)

        # Верхний блик для объёма
        if draw_rect.height > 10:
            style.draw_soft_rect(
                surface,
                pygame.Rect(draw_rect.x + 2, draw_rect.y + 1,
                            max(1, draw_rect.width - 4), 2),
                (255, 255, 255), 26, radius=1
            )

        # Рисуем границу
        if self.border_width > 0:
            pygame.draw.rect(
                surface, border_color, draw_rect,
                width=self.border_width,
                border_radius=radius
            )

        # Рисуем текст
        font = font_override or self.font
        if font and (self.text or self.icon):
            self._draw_text(surface, font, current_text_color, draw_rect)

    def _draw_text(self, surface, font, color, rect):
        """Рисует текст и иконку внутри кнопки."""
        shift = getattr(self, "text_shift_x", 0)
        if shift:
            rect = rect.move(shift, 0)

        if self.icon and self.text:
            # Иконка + текст
            icon_surf = font.render(self.icon, True, color)
            text_surf = font.render(self.text, True, color)
            gap = 8
            total_w = icon_surf.get_width() + gap + text_surf.get_width()
            start_x = rect.centerx - total_w // 2

            icon_y = rect.centery - icon_surf.get_height() // 2
            text_y = rect.centery - text_surf.get_height() // 2

            surface.blit(icon_surf, (start_x, icon_y))
            surface.blit(text_surf, (start_x + icon_surf.get_width() + gap, text_y))

        elif self.text:
            text_surf = font.render(self.text, True, color)
            text_rect = text_surf.get_rect(center=rect.center)
            surface.blit(text_surf, text_rect)

        elif self.icon:
            icon_surf = font.render(self.icon, True, color)
            icon_rect = icon_surf.get_rect(center=rect.center)
            surface.blit(icon_surf, icon_rect)

    @staticmethod
    def _lerp_color(c1, c2, t):
        """Линейная интерполяция между двумя цветами."""
        t = max(0.0, min(1.0, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )

    @property
    def rect(self):
        """Возвращает текущий прямоугольник кнопки."""
        return self._rect

    def contains_point(self, pos):
        """Проверяет, содержит ли кнопка точку."""
        if not self._rect:
            return False
        return self._rect.collidepoint(pos)


class ToggleButton(Button):
    """Кнопка-переключатель (вкл/выкл)."""

    def __init__(self, *args, toggled=False, toggle_color=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.toggled = toggled
        self._toggle_color = toggle_color

    def handle_event(self, event) -> bool:
        """При клике переключает состояние."""
        if not self.visible or not self.enabled:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._rect and self._rect.collidepoint(event.pos):
                self.pressed = True
                self._was_pressed = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._was_pressed:
                self._was_pressed = False
                self.pressed = False
                if self._rect and self._rect.collidepoint(event.pos):
                    self.toggled = not self.toggled
                    if self.on_click:
                        self.on_click(self)
                    return True

        return False

    def draw(self, surface, theme=None, font_override=None, offset=(0, 0)):
        """Рисует кнопку с учётом состояния toggle (со свитчем справа)."""
        # Текст центрируем в свободной части слева от свитча
        free_left = self._rect.left + 12 if self._rect else 0
        free_right = self._rect.right - 64 if self._rect else 0
        self.text_shift_x = (
            (free_left + free_right) // 2 - self._rect.centerx if self._rect else 0
        )

        if self.toggled and self._toggle_color:
            old_color = self._color
            self._color = style.mix(self._color, self._toggle_color, 0.45)
            super().draw(surface, theme, font_override, offset)
            self._color = old_color
        else:
            super().draw(surface, theme, font_override, offset)

        if not self._rect:
            return

        r = self._rect.copy()
        r.x += offset[0]
        r.y += offset[1]

        track_w, track_h = 42, 22
        track = pygame.Rect(
            r.right - track_w - 14, r.centery - track_h // 2,
            track_w, track_h
        )
        track_color = (74, 214, 128) if self.toggled else (104, 106, 128)
        style.draw_soft_rect(
            surface, track, track_color,
            235 if self.toggled else 150, radius=track_h // 2
        )

        knob_r = track_h // 2 - 4
        knob_x = (track.right - knob_r - 3) if self.toggled else (track.left + knob_r + 3)
        pygame.draw.circle(
            surface, (250, 252, 255), (knob_x, track.centery), knob_r
        )


class ImageButton(Button):
    """Кнопка с изображением/иконкой вместо текста."""

    def __init__(self, *args, image_surface=None, image_scale=0.7, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_surface = image_surface
        self.image_scale = image_scale

    def draw(self, surface, theme=None, font_override=None, offset=(0, 0)):
        """Рисует кнопку с изображением."""
        # Сначала рисуем базовую кнопку (без текста)
        old_text = self.text
        old_icon = self.icon
        self.text = ""
        self.icon = ""
        super().draw(surface, theme, font_override, offset)
        self.text = old_text
        self.icon = old_icon

        # Затем рисуем изображение
        if self.image_surface and self._rect:
            draw_rect = self._rect.copy()
            draw_rect.x += offset[0]
            draw_rect.y += offset[1]

            # Масштабируем
            img_w = int(draw_rect.width * self.image_scale)
            img_h = int(draw_rect.height * self.image_scale)
            scaled_img = pygame.transform.smoothscale(
                self.image_surface, (img_w, img_h)
            )
            img_rect = scaled_img.get_rect(center=draw_rect.center)
            surface.blit(scaled_img, img_rect)
