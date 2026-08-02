"""
botyaraclick - ui/scrollbar.py
Область с прокруткой и скроллбаром.
"""

import pygame


class ScrollArea:
    """
    Область с вертикальной прокруткой.
    Содержит содержимое, которое может быть больше видимой области.
    """

    def __init__(self, x, y, width, height,
                 content_height=0,
                 scroll_speed=30,
                 scrollbar_width=8,
                 bg_color=None,
                 scrollbar_bg_color=None,
                 scrollbar_thumb_color=None,
                 visible=True):
        """
        Параметры:
            x, y: позиция видимой области
            width, height: размер видимой области
            content_height: полная высота содержимого
            scroll_speed: скорость прокрутки (px за один скролл)
            scrollbar_width: ширина скроллбара
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.content_height = content_height
        self.scroll_speed = scroll_speed
        self.scrollbar_width = scrollbar_width
        self._bg_color = bg_color
        self._scrollbar_bg = scrollbar_bg_color
        self._scrollbar_thumb = scrollbar_thumb_color
        self.visible = visible

        # Состояние прокрутки
        self.scroll_y = 0.0
        self.target_scroll_y = 0.0
        self.scroll_smooth_speed = 15.0

        # Скроллбар
        self._dragging = False
        self._drag_offset = 0
        self._scrollbar_hovered = False

        # Поверхность для рендера содержимого
        self._content_surface = None
        self._update_content_surface()

    def _update_content_surface(self):
        """Создаёт поверхность для содержимого."""
        h = max(self.content_height, self.rect.height)
        if (self._content_surface is None or
                self._content_surface.get_size() != (self.rect.width - self.scrollbar_width - 2, h)):
            self._content_surface = pygame.Surface(
                (self.rect.width - self.scrollbar_width - 2, h),
                pygame.SRCALPHA
            )

    def set_content_height(self, height):
        """Устанавливает высоту содержимого."""
        self.content_height = height
        self._update_content_surface()
        # Корректируем прокрутку
        self._clamp_scroll()

    def _clamp_scroll(self):
        """Ограничивает прокрутку допустимыми значениями."""
        max_scroll = max(0, self.content_height - self.rect.height)
        self.target_scroll_y = max(0, min(self.target_scroll_y, max_scroll))
        self.scroll_y = max(0, min(self.scroll_y, max_scroll))

    def _get_scrollbar_rect(self):
        """Возвращает прямоугольник фона скроллбара."""
        return pygame.Rect(
            self.rect.right - self.scrollbar_width,
            self.rect.top,
            self.scrollbar_width,
            self.rect.height
        )

    def _get_thumb_rect(self):
        """Возвращает прямоугольник ползунка скроллбара."""
        if self.content_height <= self.rect.height:
            return pygame.Rect(
                self.rect.right - self.scrollbar_width,
                self.rect.top,
                self.scrollbar_width,
                self.rect.height
            )

        # Размер ползунка пропорционален видимой области
        visible_ratio = self.rect.height / self.content_height
        thumb_height = max(30, int(self.rect.height * visible_ratio))

        # Позиция ползунка
        max_scroll = self.content_height - self.rect.height
        if max_scroll > 0:
            scroll_ratio = self.scroll_y / max_scroll
        else:
            scroll_ratio = 0

        available_space = self.rect.height - thumb_height
        thumb_y = self.rect.top + int(available_space * scroll_ratio)

        return pygame.Rect(
            self.rect.right - self.scrollbar_width,
            thumb_y,
            self.scrollbar_width,
            thumb_height
        )

    @property
    def needs_scrollbar(self):
        """Нужен ли скроллбар."""
        return self.content_height > self.rect.height

    def handle_event(self, event) -> bool:
        """Обрабатывает события прокрутки."""
        if not self.visible:
            return False

        # Прокрутка колёсиком мыши
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.target_scroll_y -= event.y * self.scroll_speed
                self._clamp_scroll()
                return True

        # Перетаскивание скроллбара
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.needs_scrollbar:
                thumb_rect = self._get_thumb_rect()
                scrollbar_rect = self._get_scrollbar_rect()

                if thumb_rect.collidepoint(event.pos):
                    self._dragging = True
                    self._drag_offset = event.pos[1] - thumb_rect.top
                    return True
                elif scrollbar_rect.collidepoint(event.pos):
                    # Клик по полосе — прыжок к позиции
                    self._jump_to_position(event.pos[1])
                    return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._dragging:
                self._dragging = False
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self._dragging:
                self._drag_to_position(event.pos[1])
                return True

            # Hover скроллбара
            if self.needs_scrollbar:
                thumb_rect = self._get_thumb_rect()
                self._scrollbar_hovered = thumb_rect.collidepoint(event.pos)

        return False

    def _jump_to_position(self, mouse_y):
        """Прыгает к позиции по клику на полосе скроллбара."""
        if self.content_height <= self.rect.height:
            return

        relative_y = mouse_y - self.rect.top
        ratio = relative_y / self.rect.height
        max_scroll = self.content_height - self.rect.height
        self.target_scroll_y = ratio * max_scroll
        self._clamp_scroll()

    def _drag_to_position(self, mouse_y):
        """Перетаскивание ползунка."""
        if self.content_height <= self.rect.height:
            return

        thumb_height = self._get_thumb_rect().height
        available_space = self.rect.height - thumb_height

        if available_space <= 0:
            return

        relative_y = mouse_y - self._drag_offset - self.rect.top
        ratio = max(0, min(1, relative_y / available_space))
        max_scroll = self.content_height - self.rect.height
        self.target_scroll_y = ratio * max_scroll
        self.scroll_y = self.target_scroll_y
        self._clamp_scroll()

    def update(self, dt):
        """Обновляет плавную прокрутку."""
        if not self.visible:
            return

        # Плавная прокрутка
        diff = self.target_scroll_y - self.scroll_y
        if abs(diff) > 0.5:
            self.scroll_y += diff * min(self.scroll_smooth_speed * dt, 1.0)
        else:
            self.scroll_y = self.target_scroll_y

    def get_content_surface(self):
        """
        Возвращает поверхность для рисования содержимого.
        Рисуйте содержимое на этой поверхности, начиная с (0, 0).
        """
        self._update_content_surface()
        self._content_surface.fill((0, 0, 0, 0))
        return self._content_surface

    def draw(self, surface, theme=None, content_draw_func=None):
        """
        Рисует область прокрутки.

        content_draw_func: функция(surface, scroll_y) для рисования содержимого
                          surface — поверхность содержимого
                          scroll_y — текущее смещение прокрутки
        """
        if not self.visible:
            return

        # Цвета
        if theme:
            sb_bg = self._scrollbar_bg or theme.get("scrollbar_bg", (80, 80, 100))
            sb_thumb = self._scrollbar_thumb or theme.get("scrollbar_thumb", (120, 120, 150))
        else:
            sb_bg = self._scrollbar_bg or (80, 80, 100)
            sb_thumb = self._scrollbar_thumb or (120, 120, 150)

        # Фон области (опционально)
        if self._bg_color:
            pygame.draw.rect(surface, self._bg_color, self.rect)

        # Содержимое через clip
        content_width = self.rect.width
        if self.needs_scrollbar:
            content_width -= self.scrollbar_width + 2

        # Создаём clip-область
        clip_rect = pygame.Rect(
            self.rect.x, self.rect.y,
            content_width, self.rect.height
        )

        if content_draw_func:
            # Устанавливаем clip
            old_clip = surface.get_clip()
            surface.set_clip(clip_rect)

            # Вызываем функцию отрисовки с учётом скролла
            content_draw_func(surface, int(self.scroll_y))

            # Восстанавливаем clip
            surface.set_clip(old_clip)

        # Рисуем скроллбар
        if self.needs_scrollbar:
            scrollbar_rect = self._get_scrollbar_rect()
            thumb_rect = self._get_thumb_rect()

            # Фон скроллбара
            pygame.draw.rect(
                surface, sb_bg, scrollbar_rect,
                border_radius=self.scrollbar_width // 2
            )

            # Ползунок
            thumb_color = sb_thumb
            if self._dragging:
                thumb_color = tuple(min(c + 40, 255) for c in sb_thumb)
            elif self._scrollbar_hovered:
                thumb_color = tuple(min(c + 20, 255) for c in sb_thumb)

            pygame.draw.rect(
                surface, thumb_color, thumb_rect,
                border_radius=self.scrollbar_width // 2
            )

    def scroll_to_top(self):
        """Прокручивает наверх."""
        self.target_scroll_y = 0

    def scroll_to_bottom(self):
        """Прокручивает вниз."""
        self.target_scroll_y = max(0, self.content_height - self.rect.height)

    def scroll_to(self, y):
        """Прокручивает к определённой позиции."""
        self.target_scroll_y = y
        self._clamp_scroll()

    def get_visible_range(self):
        """Возвращает (start_y, end_y) видимой области содержимого."""
        return int(self.scroll_y), int(self.scroll_y) + self.rect.height

    def set_position(self, x, y):
        """Перемещает область."""
        self.rect.x = x
        self.rect.y = y

    def set_size(self, width, height):
        """Изменяет размер."""
        self.rect.width = width
        self.rect.height = height
        self._content_surface = None
        self._clamp_scroll()
