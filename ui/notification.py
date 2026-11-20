"""
botyaraclick - ui/notification.py
Система уведомлений (достижения, покупки, ивенты).

Уведомления:
- появляются СНИЗУ (над нижней панелью), а не поверх верхней панели;
- живут недолго (1.5–3 сек) и не копятся пачками (максимум 3 на экране);
- закрываются кликом по самому уведомлению (или по крестику);
- пока курсор на уведомлении — таймер замирает, можно спокойно прочитать;
- одинаковые уведомления не дублируются, а обновляют таймер.
"""

import time

import pygame

from config import BOTTOM_PANEL_HEIGHT


class Notification:
    """Одно уведомление."""

    # Длительности по умолчанию (короткие, чтобы не раздражать)
    DEFAULT_DURATION = 2.0

    def __init__(self, text, icon="", color=None, duration=2.0,
                 sub_text="", importance="normal"):
        """
        Параметры:
            text: основной текст
            icon: иконка (emoji)
            color: акцентный цвет
            duration: длительность показа (секунды)
            sub_text: подтекст (меньшим шрифтом)
            importance: "normal", "achievement", "warning", "danger"
        """
        self.text = text
        self.icon = icon
        self.color = color
        self.duration = max(0.6, float(duration))
        self.sub_text = sub_text
        self.importance = importance

        # Состояние
        self.created_at = time.time()
        self.alive = True
        self.alpha = 0
        self.slide_y = 26.0      # смещение вниз (появление снизу)
        self.hovered = False
        self.remaining = self.duration
        self.rect = pygame.Rect(0, 0, 0, 0)

        self._phase = "enter"    # "enter", "show", "exit"

    def update(self, dt, hovered=False):
        """Обновляет анимацию и таймер."""
        self.hovered = hovered

        if self._phase == "enter":
            self.alpha = min(255, self.alpha + 1400 * dt)
            self.slide_y += (0 - self.slide_y) * min(1.0, 16.0 * dt)
            if self.alpha >= 250 and abs(self.slide_y) < 1.5:
                self.alpha = 255
                self.slide_y = 0
                self._phase = "show"

        elif self._phase == "show":
            self.alpha = 255
            self.slide_y = 0
            if not hovered:
                self.remaining -= dt
            if self.remaining <= 0:
                self._phase = "exit"

        else:  # exit
            self.alpha = max(0, self.alpha - 900 * dt)
            self.slide_y += (26.0 - self.slide_y) * min(1.0, 14.0 * dt)
            if self.alpha <= 0:
                self.alpha = 0
                self.alive = False

    def dismiss(self):
        """Начинает анимацию закрытия."""
        if self._phase != "exit":
            self._phase = "exit"

    @property
    def is_alive(self):
        return self.alive

    @property
    def progress(self):
        """Остаток времени 0..1 (для полоски таймера)."""
        if self.duration <= 0:
            return 0.0
        return max(0.0, min(1.0, self.remaining / self.duration))


class NotificationManager:
    """Менеджер уведомлений — очередь, анимации, клики."""

    def __init__(self, screen_width, screen_height,
                 font=None, small_font=None,
                 max_visible=3, position="bottom_right"):
        """
        Параметры:
            screen_width, screen_height: размер экрана
            font: основной шрифт
            small_font: мелкий шрифт
            max_visible: максимум одновременно видимых
            position: "bottom_right", "bottom_left", "bottom_center"
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = font
        self.small_font = small_font
        self.max_visible = max_visible
        self.position = position

        # Очередь: новые — первыми (рисуются у нижнего края)
        self.notifications = []
        self.queue = []

        # Стиль
        self.notif_width = 320
        self.margin = 12
        self.gap = 8
        self.padding = 12
        self.border_radius = 10
        self.close_size = 22
        self.bottom_offset = BOTTOM_PANEL_HEIGHT + 10

        self._line_cache = {}

    # ================================================================
    # ДОБАВЛЕНИЕ
    # ================================================================

    def add(self, text, icon="", color=None, duration=None,
            sub_text="", importance="normal"):
        """Добавляет уведомление."""
        if duration is None:
            duration = Notification.DEFAULT_DURATION

        # Не дублируем одинаковые уведомления — просто продлеваем таймер
        for notif in self.notifications:
            if (notif.alive and notif._phase != "exit"
                    and notif.text == text and notif.icon == icon):
                notif.remaining = max(notif.remaining, min(duration, 2.5))
                notif._phase = "show"
                return notif

        notif = Notification(
            text=text, icon=icon, color=color,
            duration=duration, sub_text=sub_text,
            importance=importance
        )
        notif.slide_y = 26.0

        active_count = len(self.notifications)
        if active_count >= self.max_visible:
            self.queue.append(notif)
        else:
            self.notifications.insert(0, notif)
        return notif

    def add_achievement(self, name, description=""):
        """Короткое уведомление о достижении."""
        return self.add(
            text=name,
            icon="🏆",
            sub_text=description,
            duration=3.0,
            importance="achievement",
        )

    def add_purchase(self, name):
        """Уведомление о покупке."""
        return self.add(
            text=name,
            icon="🛒",
            duration=1.5,
            importance="normal",
        )

    def add_event(self, text, icon="🎲", positive=True):
        """Уведомление о событии."""
        importance = "normal" if positive else "warning"
        return self.add(
            text=text,
            icon=icon,
            duration=2.2,
            importance=importance,
        )

    # ================================================================
    # ОБНОВЛЕНИЕ
    # ================================================================

    def update(self, dt):
        """Обновляет все уведомления и раскладку."""
        mouse_pos = pygame.mouse.get_pos()

        for notif in self.notifications:
            hovered = notif.rect.collidepoint(mouse_pos) and notif.alpha > 0
            notif.update(dt, hovered)

        self.notifications = [n for n in self.notifications if n.alive]

        active_count = len(self.notifications)
        while self.queue and active_count < self.max_visible:
            notif = self.queue.pop(0)
            notif.created_at = time.time()
            self.notifications.insert(0, notif)
            active_count += 1

        self._layout()

    def _layout(self):
        """Пересчитывает прямоугольники (снизу вверх)."""
        bottom = self.screen_height - self.bottom_offset
        y = bottom
        for notif in self.notifications:
            height = self._height_for(notif)
            y -= height
            x = self._x_for(notif)
            notif.rect = pygame.Rect(
                int(x), int(y + notif.slide_y), self.notif_width, height
            )
            y -= self.gap

    def _x_for(self, notif):
        if self.position == "bottom_left":
            return self.margin
        if self.position == "bottom_center":
            return (self.screen_width - self.notif_width) // 2
        return self.screen_width - self.notif_width - self.margin

    # ================================================================
    # СОБЫТИЯ (клик — закрыть)
    # ================================================================

    def handle_event(self, event):
        """
        Обрабатывает клики по уведомлениям.

        Возвращает True, если клик был по уведомлению
        (чтобы он не провалился в игру).
        """
        if not self.notifications:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for notif in list(self.notifications):
                if notif.alpha <= 0:
                    continue
                if notif.rect.collidepoint(event.pos):
                    notif.dismiss()
                    return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for notif in self.notifications:
                if notif.rect.collidepoint(event.pos):
                    return True

        return False

    def dismiss_all(self):
        """Закрывает все уведомления."""
        for notif in self.notifications:
            notif.dismiss()
        self.queue.clear()

    # ================================================================
    # ОТРИСОВКА
    # ================================================================

    def draw(self, surface, theme=None):
        """Рисует все уведомления."""
        if not self.notifications:
            return

        for notif in self.notifications:
            if notif.alive:
                self._draw_notification(surface, notif, theme)

    def _height_for(self, notif):
        if notif.sub_text and self.small_font:
            return 72
        return 54

    def _colors(self, notif, theme):
        if theme:
            bg_color = theme.get("panel_color", (40, 40, 55))
            text_color = theme.get("text_bright", (255, 255, 255))
            sub_color = theme.get("text_dim", (150, 150, 170))
            accent = theme.get("accent_color", (50, 150, 255))
        else:
            bg_color = (40, 40, 55)
            text_color = (255, 255, 255)
            sub_color = (150, 150, 170)
            accent = (50, 150, 255)

        if notif.importance == "achievement":
            accent_color = (255, 200, 0)
        elif notif.importance == "warning":
            accent_color = (240, 180, 40)
        elif notif.importance == "danger":
            accent_color = (220, 60, 60)
        else:
            accent_color = notif.color or accent

        return bg_color, text_color, sub_color, accent_color

    def _draw_notification(self, surface, notif, theme=None):
        """Рисует одно уведомление."""
        alpha = int(notif.alpha)
        if alpha <= 0:
            return

        bg_color, text_color, sub_color, accent_color = self._colors(notif, theme)
        rect = notif.rect
        if rect.width <= 0 or rect.height <= 0:
            return

        # Тень
        shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow, (0, 0, 0, int(alpha * 0.35)),
            (0, 0, rect.width, rect.height), border_radius=self.border_radius
        )
        surface.blit(shadow, (rect.x, rect.y + 3))

        # Панель
        panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(
            panel, (*bg_color, int(alpha * 0.96)),
            (0, 0, rect.width, rect.height), border_radius=self.border_radius
        )
        pygame.draw.rect(
            panel, (*accent_color, alpha),
            (0, 0, rect.width, rect.height),
            width=1, border_radius=self.border_radius
        )

        # Акцентная полоска слева
        pygame.draw.rect(
            panel, (*accent_color, alpha), (0, 0, 4, rect.height),
            border_top_left_radius=self.border_radius,
            border_bottom_left_radius=self.border_radius
        )

        # Полоска оставшегося времени
        bar_w = max(0, int((rect.width - 2) * notif.progress))
        if bar_w > 2 and notif._phase == "show":
            pygame.draw.rect(
                panel, (*accent_color, int(alpha * 0.55)),
                (1, rect.height - 3, bar_w, 2), border_radius=1
            )

        content_x = self.padding + 2

        # Иконка
        if notif.icon and self.font:
            icon_surf = self.font.render(notif.icon, True, text_color)
            icon_surf.set_alpha(alpha)
            icon_y = rect.height // 2 - icon_surf.get_height() // 2
            if notif.sub_text:
                icon_y = self.padding - 1
            panel.blit(icon_surf, (content_x, icon_y))
            content_x += icon_surf.get_width() + 8

        text_area_w = rect.width - content_x - self.padding - self.close_size - 6

        # Основной текст
        if self.font and notif.text:
            max_lines = 1 if not notif.sub_text else 1
            line_h = self.font.get_height()
            lines = self._wrap(notif.text, self.font, text_area_w, max_lines)
            text_y = (rect.height - len(lines) * line_h) // 2
            if notif.sub_text:
                text_y = self.padding - 2
            for line in lines:
                line_surf = self.font.render(line, True, text_color)
                line_surf.set_alpha(alpha)
                panel.blit(line_surf, (content_x, text_y))
                text_y += line_h

            # Подтекст
            if notif.sub_text and self.small_font:
                sub_text = self._ellipsize(notif.sub_text, self.small_font, text_area_w)
                sub_surf = self.small_font.render(sub_text, True, sub_color)
                sub_surf.set_alpha(alpha)
                panel.blit(sub_surf, (content_x, rect.height - self.padding - sub_surf.get_height()))

        # Крестик закрытия — рисуем линиями, чтобы не зависеть от глифов
        close_color = (255, 255, 255, alpha) if notif.hovered else (*sub_color, alpha)
        cx_close = rect.width - self.padding - 8
        cy_close = rect.height // 2
        half = 4
        if notif.hovered:
            pygame.draw.circle(
                panel, (*sub_color, int(alpha * 0.25)),
                (cx_close, cy_close), half + 5
            )
        pygame.draw.line(
            panel, close_color,
            (cx_close - half, cy_close - half),
            (cx_close + half, cy_close + half), 2
        )
        pygame.draw.line(
            panel, close_color,
            (cx_close - half, cy_close + half),
            (cx_close + half, cy_close - half), 2
        )

        surface.blit(panel, (rect.x, rect.y))

    # --- вспомогательное -------------------------------------------

    def _wrap(self, text, font, max_width, max_lines=1):
        """Переносит текст по словам, добавляя «…» если не влез."""
        if not text:
            return [""]
        if max_width <= 10:
            return [self._ellipsize(text, font, max(10, max_width))]

        cache_key = (
            text,
            getattr(font, "size_px", None) or id(font),
            getattr(font, "path", None),
            max_width,
            max_lines,
        )
        cached = self._line_cache.get(cache_key)
        if cached is not None:
            return cached

        words = text.split(" ")
        lines = []
        current = ""
        idx = 0

        while idx < len(words) and len(lines) < max_lines:
            word = words[idx]
            candidate = word if not current else current + " " + word
            if font.size(candidate)[0] <= max_width:
                current = candidate
                idx += 1
            elif current:
                lines.append(current)
                current = ""
            else:
                # Одно слово шире строки — обрезаем его
                lines.append(self._ellipsize(word, font, max_width))
                idx += 1
                break

        if current and len(lines) < max_lines:
            lines.append(current)

        if idx < len(words):
            # Остаток не поместился — ставим многоточие
            rest = " ".join(words[idx:])
            if lines:
                lines[-1] = self._ellipsize(lines[-1] + " " + rest, font, max_width)
            else:
                lines.append(self._ellipsize(rest, font, max_width))

        if not lines:
            lines = [self._ellipsize(text, font, max_width)]

        if len(self._line_cache) > 512:
            self._line_cache.clear()
        self._line_cache[cache_key] = lines
        return lines

    @staticmethod
    def _ellipsize(text, font, max_width):
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "…"
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text.rstrip() + ellipsis

    # ================================================================
    # ПРОЧЕЕ
    # ================================================================

    def resize(self, screen_width, screen_height):
        """Обновляет размеры экрана."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self._layout()

    def clear(self):
        """Очищает все уведомления."""
        self.notifications.clear()
        self.queue.clear()
