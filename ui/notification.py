"""
botyaraclick - ui/notification.py
Система уведомлений (достижения, покупки, ивенты).
"""

import pygame
import time


class Notification:
    """Одно уведомление."""

    def __init__(self, text, icon="", color=None, duration=3.0,
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
        self.duration = duration
        self.sub_text = sub_text
        self.importance = importance

        # Состояние
        self.created_at = time.time()
        self.alive = True
        self.alpha = 0
        self.target_alpha = 255
        self.slide_x = 0  # смещение для анимации выезда
        self.target_slide_x = 0

        # Анимация
        self._phase = "enter"  # "enter", "show", "exit"
        self._show_start = 0

    def update(self, dt):
        """Обновляет анимацию."""
        now = time.time()
        age = now - self.created_at

        if self._phase == "enter":
            # Выезжаем справа
            self.target_alpha = 255
            self.target_slide_x = 0
            speed = 12.0 * dt
            self.alpha = min(self.alpha + 800 * dt, 255)
            self.slide_x += (self.target_slide_x - self.slide_x) * min(speed, 1.0)

            if self.alpha >= 250 and abs(self.slide_x) < 2:
                self._phase = "show"
                self._show_start = now

        elif self._phase == "show":
            self.alpha = 255
            self.slide_x = 0
            if now - self._show_start >= self.duration:
                self._phase = "exit"

        elif self._phase == "exit":
            self.target_alpha = 0
            self.target_slide_x = 350  # уезжаем вправо
            speed = 8.0 * dt
            self.alpha = max(self.alpha - 600 * dt, 0)
            self.slide_x += (self.target_slide_x - self.slide_x) * min(speed, 1.0)

            if self.alpha <= 0:
                self.alive = False

    @property
    def is_alive(self):
        return self.alive


class NotificationManager:
    """Менеджер уведомлений — управляет очередью и отрисовкой."""

    def __init__(self, screen_width, screen_height,
                 font=None, small_font=None,
                 max_visible=5, position="top_right"):
        """
        Параметры:
            screen_width, screen_height: размер экрана
            font: основной шрифт
            small_font: мелкий шрифт
            max_visible: максимум одновременно видимых
            position: "top_right", "top_left", "bottom_right"
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = font
        self.small_font = small_font
        self.max_visible = max_visible
        self.position = position

        # Очередь уведомлений
        self.notifications = []
        self.queue = []  # ожидающие показа

        # Стиль
        self.notif_width = 320
        self.notif_height = 60
        self.notif_height_with_sub = 80
        self.margin = 10
        self.padding = 12
        self.border_radius = 8
        self.start_slide_x = 350  # начальное смещение вправо

    def add(self, text, icon="", color=None, duration=3.0,
            sub_text="", importance="normal"):
        """Добавляет уведомление."""
        notif = Notification(
            text=text, icon=icon, color=color,
            duration=duration, sub_text=sub_text,
            importance=importance
        )
        notif.slide_x = self.start_slide_x

        # Если слишком много на экране — в очередь
        active_count = len([n for n in self.notifications if n.alive])
        if active_count >= self.max_visible:
            self.queue.append(notif)
        else:
            self.notifications.append(notif)

    def add_achievement(self, name, description=""):
        """Добавляет уведомление о достижении."""
        self.add(
            text=name,
            icon="🏆",
            sub_text=description,
            duration=4.0,
            importance="achievement"
        )

    def add_purchase(self, name):
        """Добавляет уведомление о покупке."""
        self.add(
            text=name,
            icon="🛒",
            duration=2.0,
            importance="normal"
        )

    def add_event(self, text, icon="🎲", positive=True):
        """Добавляет уведомление о событии."""
        importance = "normal" if positive else "warning"
        self.add(
            text=text,
            icon=icon,
            duration=3.0,
            importance=importance
        )

    def update(self, dt):
        """Обновляет все уведомления."""
        # Обновляем активные
        for notif in self.notifications:
            notif.update(dt)

        # Удаляем мёртвые
        self.notifications = [n for n in self.notifications if n.alive]

        # Добавляем из очереди
        active_count = len(self.notifications)
        while self.queue and active_count < self.max_visible:
            notif = self.queue.pop(0)
            notif.slide_x = self.start_slide_x
            notif.created_at = time.time()
            self.notifications.append(notif)
            active_count += 1

    def draw(self, surface, theme=None):
        """Рисует все уведомления."""
        if not self.notifications:
            return

        for i, notif in enumerate(self.notifications):
            if not notif.alive:
                continue
            self._draw_notification(surface, notif, i, theme)

    def _draw_notification(self, surface, notif, index, theme=None):
        """Рисует одно уведомление."""
        # Цвета
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

        # Цвет акцента по важности
        if notif.importance == "achievement":
            accent_color = (255, 200, 0)
        elif notif.importance == "warning":
            accent_color = (240, 180, 40)
        elif notif.importance == "danger":
            accent_color = (220, 60, 60)
        else:
            accent_color = notif.color or accent

        # Определяем высоту
        height = self.notif_height_with_sub if notif.sub_text else self.notif_height

        # Позиция
        if self.position == "top_right":
            x = self.screen_width - self.notif_width - self.margin + notif.slide_x
            y = self.margin + index * (height + self.margin) + 70  # +70 чтобы не перекрывать верхнюю панель
        elif self.position == "top_left":
            x = self.margin - notif.slide_x
            y = self.margin + index * (height + self.margin) + 70
        else:  # bottom_right
            x = self.screen_width - self.notif_width - self.margin + notif.slide_x
            y = self.screen_height - (index + 1) * (height + self.margin) - self.margin

        # Рисуем
        alpha = int(notif.alpha)
        if alpha <= 0:
            return

        notif_surf = pygame.Surface(
            (self.notif_width, height), pygame.SRCALPHA
        )

        # Фон
        pygame.draw.rect(
            notif_surf, (*bg_color, alpha),
            (0, 0, self.notif_width, height),
            border_radius=self.border_radius
        )

        # Акцентная полоска слева
        accent_with_alpha = (*accent_color, alpha)
        pygame.draw.rect(
            notif_surf, accent_with_alpha,
            (0, 0, 4, height),
            border_radius=2
        )

        # Иконка и текст
        if self.font:
            content_x = self.padding + 4  # после акцентной полоски

            if notif.icon:
                icon_surf = self.font.render(notif.icon, True, text_color)
                icon_surf.set_alpha(alpha)
                notif_surf.blit(icon_surf, (content_x, self.padding))
                content_x += icon_surf.get_width() + 8

            # Основной текст
            text_surf = self.font.render(notif.text, True, text_color)
            text_surf.set_alpha(alpha)
            if notif.sub_text:
                notif_surf.blit(text_surf, (content_x, self.padding - 2))
            else:
                text_y = height // 2 - text_surf.get_height() // 2
                notif_surf.blit(text_surf, (content_x, text_y))

            # Подтекст
            if notif.sub_text and self.small_font:
                sub_surf = self.small_font.render(notif.sub_text, True, sub_color)
                sub_surf.set_alpha(alpha)
                notif_surf.blit(
                    sub_surf,
                    (content_x, self.padding + text_surf.get_height() + 4)
                )

        surface.blit(notif_surf, (x, y))

    def resize(self, screen_width, screen_height):
        """Обновляет размеры экрана."""
        self.screen_width = screen_width
        self.screen_height = screen_height

    def clear(self):
        """Очищает все уведомления."""
        self.notifications.clear()
        self.queue.clear()
