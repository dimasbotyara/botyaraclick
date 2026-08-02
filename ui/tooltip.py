"""
botyaraclick - ui/tooltip.py
Система всплывающих подсказок.
"""

import pygame
import time


class TooltipManager:
    """
    Менеджер тултипов.
    Показывает подсказку при наведении на элемент.
    """

    def __init__(self, font=None, delay=0.5):
        """
        Параметры:
            font: шрифт для тултипа
            delay: задержка перед показом (секунды)
        """
        self.font = font
        self.delay = delay

        # Состояние
        self._current_text = ""
        self._current_pos = (0, 0)
        self._hover_start = 0
        self._visible = False
        self._alpha = 0
        self._target_alpha = 0
        self._last_text = ""

        # Стиль
        self.padding = 8
        self.max_width = 300
        self.border_radius = 4
        self.offset_y = -10  # смещение вверх от курсора

    def show(self, text, pos):
        """Запрашивает показ тултипа."""
        if text != self._last_text:
            self._hover_start = time.time()
            self._last_text = text
            self._visible = False
            self._alpha = 0

        self._current_text = text
        self._current_pos = pos

        # Проверяем задержку
        if time.time() - self._hover_start >= self.delay:
            self._target_alpha = 230
            self._visible = True

    def hide(self):
        """Скрывает тултип."""
        self._target_alpha = 0
        self._last_text = ""
        self._hover_start = 0

    def update(self, dt):
        """Обновляет анимацию прозрачности."""
        speed = 800 * dt
        if self._alpha < self._target_alpha:
            self._alpha = min(self._alpha + speed, self._target_alpha)
        elif self._alpha > self._target_alpha:
            self._alpha = max(self._alpha - speed, self._target_alpha)

        if self._alpha <= 0:
            self._visible = False

    def draw(self, surface, theme=None):
        """Рисует тултип."""
        if not self._visible or self._alpha <= 0 or not self._current_text:
            return
        if not self.font:
            return

        # Цвета
        if theme:
            bg_color = (20, 20, 30)
            text_color = theme.get("text_bright", (255, 255, 255))
            border_color = theme.get("panel_border", (60, 60, 80))
        else:
            bg_color = (20, 20, 30)
            text_color = (255, 255, 255)
            border_color = (60, 60, 80)

        # Разбиваем текст на строки
        lines = self._wrap_text(self._current_text)

        # Рассчитываем размер
        line_surfaces = [self.font.render(line, True, text_color) for line in lines]
        if not line_surfaces:
            return

        max_line_w = max(s.get_width() for s in line_surfaces)
        total_h = sum(s.get_height() for s in line_surfaces) + 2 * (len(lines) - 1)

        tooltip_w = max_line_w + self.padding * 2
        tooltip_h = total_h + self.padding * 2

        # Позиция (над курсором, не выходя за экран)
        mx, my = self._current_pos
        tx = mx - tooltip_w // 2
        ty = my - tooltip_h + self.offset_y

        screen_w, screen_h = surface.get_size()

        # Корректируем чтобы не выходил за экран
        if tx < 5:
            tx = 5
        if tx + tooltip_w > screen_w - 5:
            tx = screen_w - tooltip_w - 5
        if ty < 5:
            ty = my + 20  # показываем под курсором если не влезает сверху
        if ty + tooltip_h > screen_h - 5:
            ty = screen_h - tooltip_h - 5

        # Рисуем фон
        tooltip_surf = pygame.Surface(
            (tooltip_w, tooltip_h), pygame.SRCALPHA
        )
        alpha = int(self._alpha)
        pygame.draw.rect(
            tooltip_surf, (*bg_color, alpha),
            (0, 0, tooltip_w, tooltip_h),
            border_radius=self.border_radius
        )
        pygame.draw.rect(
            tooltip_surf, (*border_color, alpha),
            (0, 0, tooltip_w, tooltip_h),
            width=1, border_radius=self.border_radius
        )

        # Рисуем текст
        current_y = self.padding
        for line_surf in line_surfaces:
            # Применяем альфа к тексту
            temp = line_surf.copy()
            temp.set_alpha(alpha)
            tooltip_surf.blit(temp, (self.padding, current_y))
            current_y += line_surf.get_height() + 2

        surface.blit(tooltip_surf, (tx, ty))

    def _wrap_text(self, text):
        """Разбивает текст на строки по ширине."""
        if not self.font:
            return [text]

        # Сначала разбиваем по \n
        paragraphs = text.split('\n')
        lines = []

        for paragraph in paragraphs:
            if not paragraph:
                lines.append("")
                continue

            words = paragraph.split(' ')
            current_line = ""

            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if self.font.size(test_line)[0] <= self.max_width - self.padding * 2:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

        return lines if lines else [""]
