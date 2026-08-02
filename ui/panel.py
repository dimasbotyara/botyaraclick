"""
botyaraclick - ui/panel.py
Панели для группировки UI элементов.
"""

import pygame


class Panel:
    """Панель — прямоугольная область с фоном, границей и заголовком."""

    def __init__(self, x, y, width, height,
                 bg_color=None, border_color=None, border_width=1,
                 border_radius=6, title="", title_font=None,
                 title_color=None, alpha=255, visible=True):
        """
        Параметры:
            x, y: позиция
            width, height: размер
            bg_color: цвет фона (None = из темы)
            border_color: цвет границы
            border_width: толщина границы
            border_radius: скругление
            title: заголовок панели
            title_font: шрифт заголовка
            title_color: цвет заголовка
            alpha: прозрачность (0-255)
            visible: видимость
        """
        self.rect = pygame.Rect(x, y, width, height)
        self._bg_color = bg_color
        self._border_color = border_color
        self.border_width = border_width
        self.border_radius = border_radius
        self.title = title
        self.title_font = title_font
        self._title_color = title_color
        self.alpha = alpha
        self.visible = visible

        # Дочерние элементы
        self.children = []

        # Кеш surface для прозрачности
        self._surface = None
        self._needs_redraw = True

    def set_position(self, x, y):
        """Изменяет позицию панели."""
        self.rect.x = x
        self.rect.y = y
        self._needs_redraw = True

    def set_size(self, width, height):
        """Изменяет размер панели."""
        self.rect.width = width
        self.rect.height = height
        self._surface = None
        self._needs_redraw = True

    def add_child(self, child):
        """Добавляет дочерний элемент."""
        self.children.append(child)

    def remove_child(self, child):
        """Удаляет дочерний элемент."""
        if child in self.children:
            self.children.remove(child)

    def get_colors(self, theme=None):
        """Получает цвета из темы или заданные."""
        if theme:
            bg = self._bg_color or theme.get("panel_color", (40, 40, 55))
            border = self._border_color or theme.get("panel_border", (60, 60, 80))
            title_c = self._title_color or theme.get("text_bright", (255, 255, 255))
        else:
            bg = self._bg_color or (40, 40, 55)
            border = self._border_color or (60, 60, 80)
            title_c = self._title_color or (255, 255, 255)
        return bg, border, title_c

    def draw(self, surface, theme=None, offset=(0, 0)):
        """Рисует панель."""
        if not self.visible:
            return

        bg_color, border_color, title_color = self.get_colors(theme)

        draw_rect = self.rect.copy()
        draw_rect.x += offset[0]
        draw_rect.y += offset[1]

        if self.alpha < 255:
            # Рисуем через промежуточную surface для прозрачности
            panel_surf = pygame.Surface(
                (draw_rect.width, draw_rect.height), pygame.SRCALPHA
            )
            bg_with_alpha = (*bg_color[:3], self.alpha)
            pygame.draw.rect(
                panel_surf, bg_with_alpha,
                (0, 0, draw_rect.width, draw_rect.height),
                border_radius=self.border_radius
            )
            if self.border_width > 0:
                border_with_alpha = (*border_color[:3], self.alpha)
                pygame.draw.rect(
                    panel_surf, border_with_alpha,
                    (0, 0, draw_rect.width, draw_rect.height),
                    width=self.border_width,
                    border_radius=self.border_radius
                )
            surface.blit(panel_surf, draw_rect.topleft)
        else:
            # Обычная отрисовка
            pygame.draw.rect(
                surface, bg_color, draw_rect,
                border_radius=self.border_radius
            )
            if self.border_width > 0:
                pygame.draw.rect(
                    surface, border_color, draw_rect,
                    width=self.border_width,
                    border_radius=self.border_radius
                )

        # Заголовок
        if self.title and self.title_font:
            title_surf = self.title_font.render(self.title, True, title_color)
            title_rect = title_surf.get_rect(
                midtop=(draw_rect.centerx, draw_rect.top + 8)
            )
            surface.blit(title_surf, title_rect)

    def get_content_rect(self):
        """Возвращает прямоугольник для контента (без заголовка)."""
        title_offset = 35 if self.title else 5
        return pygame.Rect(
            self.rect.x + 5,
            self.rect.y + title_offset,
            self.rect.width - 10,
            self.rect.height - title_offset - 5
        )

    def contains_point(self, pos):
        """Проверяет, содержит ли панель точку."""
        return self.rect.collidepoint(pos)


class GradientPanel(Panel):
    """Панель с градиентным фоном."""

    def __init__(self, *args, gradient_top=None, gradient_bottom=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._gradient_top = gradient_top
        self._gradient_bottom = gradient_bottom
        self._gradient_surface = None

    def _create_gradient(self, width, height, top_color, bottom_color):
        """Создаёт градиентную поверхность."""
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        for y in range(height):
            t = y / max(height - 1, 1)
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
            a = self.alpha
            pygame.draw.line(surf, (r, g, b, a), (0, y), (width - 1, y))
        return surf

    def draw(self, surface, theme=None, offset=(0, 0)):
        """Рисует панель с градиентом."""
        if not self.visible:
            return

        _, border_color, title_color = self.get_colors(theme)

        draw_rect = self.rect.copy()
        draw_rect.x += offset[0]
        draw_rect.y += offset[1]

        # Градиент
        top = self._gradient_top
        bottom = self._gradient_bottom
        if theme and not top:
            top = theme.get("bg_gradient_top", (30, 30, 45))
        if theme and not bottom:
            bottom = theme.get("bg_gradient_bottom", (20, 20, 30))
        top = top or (30, 30, 45)
        bottom = bottom or (20, 20, 30)

        if (self._gradient_surface is None or
                self._gradient_surface.get_size() != (draw_rect.width, draw_rect.height)):
            self._gradient_surface = self._create_gradient(
                draw_rect.width, draw_rect.height, top, bottom
            )

        # Применяем скругление через маску
        mask_surf = pygame.Surface(
            (draw_rect.width, draw_rect.height), pygame.SRCALPHA
        )
        pygame.draw.rect(
            mask_surf, (255, 255, 255, 255),
            (0, 0, draw_rect.width, draw_rect.height),
            border_radius=self.border_radius
        )

        result = self._gradient_surface.copy()
        # Применяем маску: пиксели где маска прозрачна — тоже прозрачны
        for x_pos in range(draw_rect.width):
            for y_pos in range(draw_rect.height):
                mask_alpha = mask_surf.get_at((x_pos, y_pos))[3]
                if mask_alpha == 0:
                    result.set_at((x_pos, y_pos), (0, 0, 0, 0))

        surface.blit(result, draw_rect.topleft)

        # Граница
        if self.border_width > 0:
            pygame.draw.rect(
                surface, border_color, draw_rect,
                width=self.border_width,
                border_radius=self.border_radius
            )

        # Заголовок
        if self.title and self.title_font:
            title_surf = self.title_font.render(self.title, True, title_color)
            title_rect = title_surf.get_rect(
                midtop=(draw_rect.centerx, draw_rect.top + 8)
            )
            surface.blit(title_surf, title_rect)


class DarkOverlay:
    """Тёмное затемнение экрана (для пауз, попапов)."""

    def __init__(self, width, height, alpha=150):
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.alpha = alpha
        self.current_alpha = 0
        self.target_alpha = 0
        self.speed = 600  # альфа в секунду

    def show(self):
        """Показать затемнение."""
        self.target_alpha = self.alpha

    def hide(self):
        """Скрыть затемнение."""
        self.target_alpha = 0

    def update(self, dt):
        """Обновляет анимацию."""
        if self.current_alpha < self.target_alpha:
            self.current_alpha = min(
                self.current_alpha + self.speed * dt,
                self.target_alpha
            )
        elif self.current_alpha > self.target_alpha:
            self.current_alpha = max(
                self.current_alpha - self.speed * dt,
                self.target_alpha
            )

    def draw(self, surface):
        """Рисует затемнение."""
        if self.current_alpha > 0:
            self.surface.fill((0, 0, 0, int(self.current_alpha)))
            surface.blit(self.surface, (0, 0))

    @property
    def is_visible(self):
        return self.current_alpha > 0

    @property
    def is_fully_visible(self):
        return self.current_alpha >= self.alpha - 1

    def resize(self, width, height):
        """Изменяет размер оверлея."""
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
