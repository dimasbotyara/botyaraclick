"""
botyaraclick - ui/popup.py
Всплывающие диалоговые окна (подтверждения, выбор, информация).
"""

import pygame
from ui.button import Button
from ui.panel import DarkOverlay


class Popup:
    """Одно всплывающее окно."""

    def __init__(self, title="", message="", popup_type="info",
                 buttons=None, width=450, height=250,
                 on_result=None):
        """
        Параметры:
            title: заголовок
            message: текст сообщения
            popup_type: "info", "confirm", "choice", "input"
            buttons: список кнопок [{"text": "OK", "value": "ok"}, ...]
            width, height: размер окна
            on_result: callback(value) при нажатии кнопки
        """
        self.title = title
        self.message = message
        self.popup_type = popup_type
        self.width = width
        self.height = height
        self.on_result = on_result

        self.alive = True
        self.result = None

        # Анимация
        self._scale = 0.5
        self._alpha = 0
        self._target_scale = 1.0
        self._target_alpha = 255

        # Кнопки
        self._buttons = []
        if buttons:
            self._create_buttons(buttons)
        elif popup_type == "confirm":
            self._create_buttons([
                {"text": "Yes", "value": "yes"},
                {"text": "No", "value": "no"},
            ])
        else:
            self._create_buttons([
                {"text": "OK", "value": "ok"},
            ])

    def _create_buttons(self, button_defs):
        """Создаёт кнопки из описаний."""
        self._button_defs = button_defs
        # Кнопки создадим при первой отрисовке, когда знаем шрифт

    def _ensure_buttons(self, font, screen_w, screen_h, theme=None):
        """Создаёт кнопки если ещё не созданы."""
        if self._buttons:
            return

        btn_count = len(self._button_defs)
        btn_width = min(120, (self.width - 40) // max(btn_count, 1) - 10)
        btn_height = 40
        total_btn_width = btn_count * btn_width + (btn_count - 1) * 10

        popup_x = screen_w // 2 - self.width // 2
        popup_y = screen_h // 2 - self.height // 2
        start_x = popup_x + self.width // 2 - total_btn_width // 2

        for i, btn_def in enumerate(self._button_defs):
            bx = start_x + i * (btn_width + 10)
            by = popup_y + self.height - btn_height - 20

            # Первая кнопка — акцентная, остальные — обычные
            if i == 0 and theme:
                color = theme.get("accent_color", (50, 150, 255))
            else:
                color = None

            btn = Button(
                bx, by, btn_width, btn_height,
                text=btn_def.get("text", ""),
                font=font,
                color=color,
                border_radius=6,
                tag=btn_def.get("value", ""),
            )
            self._buttons.append(btn)

    def update(self, dt, mouse_pos):
        """Обновляет анимации."""
        # Масштаб
        diff = self._target_scale - self._scale
        self._scale += diff * min(12.0 * dt, 1.0)

        # Альфа
        diff_a = self._target_alpha - self._alpha
        if abs(diff_a) > 1:
            self._alpha += diff_a * min(10.0 * dt, 1.0)
        else:
            self._alpha = self._target_alpha

        # Кнопки
        for btn in self._buttons:
            btn.update(dt, mouse_pos)

        # Закрытие
        if self._target_alpha <= 0 and self._alpha < 5:
            self.alive = False

    def handle_event(self, event, font=None, screen_w=0, screen_h=0, theme=None):
        """Обрабатывает события."""
        if font:
            self._ensure_buttons(font, screen_w, screen_h, theme)

        for btn in self._buttons:
            if btn.handle_event(event):
                self.result = btn.tag
                if self.on_result:
                    self.on_result(self.result)
                self.close()
                return True

        # ESC закрывает с результатом "cancel"
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.result = "cancel"
            if self.on_result:
                self.on_result(self.result)
            self.close()
            return True

        # Клик вне попапа — ничего не делаем (модальное окно)
        return False

    def close(self):
        """Начинает анимацию закрытия."""
        self._target_alpha = 0
        self._target_scale = 0.8

    def draw(self, surface, theme=None, font=None, title_font=None):
        """Рисует попап."""
        if not self.alive:
            return

        screen_w, screen_h = surface.get_size()

        if font:
            self._ensure_buttons(font, screen_w, screen_h, theme)

        # Цвета
        if theme:
            bg_color = theme.get("panel_color", (40, 40, 55))
            border_color = theme.get("panel_border", (60, 60, 80))
            title_color = theme.get("text_bright", (255, 255, 255))
            text_color = theme.get("text_color", (230, 230, 240))
        else:
            bg_color = (40, 40, 55)
            border_color = (60, 60, 80)
            title_color = (255, 255, 255)
            text_color = (230, 230, 240)

        alpha = int(max(0, min(255, self._alpha)))
        if alpha <= 0:
            return

        # Рассчитываем размер с учётом масштаба
        scaled_w = int(self.width * self._scale)
        scaled_h = int(self.height * self._scale)
        popup_x = screen_w // 2 - scaled_w // 2
        popup_y = screen_h // 2 - scaled_h // 2

        # Создаём поверхность попапа
        popup_surf = pygame.Surface((scaled_w, scaled_h), pygame.SRCALPHA)

        # Фон
        pygame.draw.rect(
            popup_surf, (*bg_color, alpha),
            (0, 0, scaled_w, scaled_h),
            border_radius=10
        )

        # Граница
        pygame.draw.rect(
            popup_surf, (*border_color, alpha),
            (0, 0, scaled_w, scaled_h),
            width=2, border_radius=10
        )

        # Масштаб для текста
        scale = self._scale

        # Заголовок
        t_font = title_font or font
        if t_font and self.title:
            title_surf = t_font.render(self.title, True, title_color)
            title_surf.set_alpha(alpha)
            if scale < 1.0:
                new_w = max(1, int(title_surf.get_width() * scale))
                new_h = max(1, int(title_surf.get_height() * scale))
                title_surf = pygame.transform.smoothscale(title_surf, (new_w, new_h))
            title_rect = title_surf.get_rect(midtop=(scaled_w // 2, int(20 * scale)))
            popup_surf.blit(title_surf, title_rect)

        # Сообщение
        if font and self.message:
            # Переносим текст по строкам
            lines = self._wrap_message(font, self.message, scaled_w - 40)
            msg_y = int(60 * scale)
            for line in lines:
                line_surf = font.render(line, True, text_color)
                line_surf.set_alpha(alpha)
                if scale < 1.0:
                    new_w = max(1, int(line_surf.get_width() * scale))
                    new_h = max(1, int(line_surf.get_height() * scale))
                    line_surf = pygame.transform.smoothscale(line_surf, (new_w, new_h))
                line_rect = line_surf.get_rect(midtop=(scaled_w // 2, msg_y))
                popup_surf.blit(line_surf, line_rect)
                msg_y += line_surf.get_height() + 4

        surface.blit(popup_surf, (popup_x, popup_y))

        # Рисуем кнопки (поверх попапа, на основной surface)
        if self._scale > 0.9:  # показываем кнопки только когда попап почти раскрылся
            for btn in self._buttons:
                btn.draw(surface, theme, font)

    def _wrap_message(self, font, text, max_width):
        """Разбивает сообщение на строки."""
        paragraphs = text.split('\n')
        lines = []
        for para in paragraphs:
            if not para:
                lines.append("")
                continue
            words = para.split(' ')
            current = ""
            for word in words:
                test = current + (" " if current else "") + word
                if font.size(test)[0] <= max_width:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    current = word
            if current:
                lines.append(current)
        return lines


class PopupManager:
    """Менеджер попапов."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.popups = []
        self.overlay = DarkOverlay(screen_width, screen_height, alpha=150)

    @property
    def has_popup(self):
        """Есть ли активные попапы."""
        return len(self.popups) > 0

    def show_info(self, title, message, on_result=None):
        """Показывает информационное окно."""
        popup = Popup(
            title=title, message=message,
            popup_type="info", on_result=on_result
        )
        self.popups.append(popup)
        self.overlay.show()

    def show_confirm(self, title, message, on_result=None,
                     yes_text="Yes", no_text="No"):
        """Показывает окно подтверждения."""
        popup = Popup(
            title=title, message=message,
            popup_type="confirm",
            buttons=[
                {"text": yes_text, "value": "yes"},
                {"text": no_text, "value": "no"},
            ],
            on_result=on_result
        )
        self.popups.append(popup)
        self.overlay.show()

    def show_choice(self, title, message, choices, on_result=None):
        """Показывает окно с несколькими вариантами выбора."""
        popup = Popup(
            title=title, message=message,
            popup_type="choice",
            buttons=choices,
            on_result=on_result,
            width=500
        )
        self.popups.append(popup)
        self.overlay.show()

    def update(self, dt, mouse_pos):
        """Обновляет все попапы."""
        self.overlay.update(dt)

        for popup in self.popups:
            popup.update(dt, mouse_pos)

        # Удаляем мёртвые
        self.popups = [p for p in self.popups if p.alive]

        if not self.popups:
            self.overlay.hide()

    def handle_event(self, event, font=None, theme=None) -> bool:
        """
        Обрабатывает события.
        Возвращает True если событие было обработано попапом
        (чтобы нижележащие элементы его не получили).
        """
        if not self.popups:
            return False

        # Обрабатываем только верхний попап
        top_popup = self.popups[-1]
        top_popup.handle_event(
            event, font,
            self.screen_width, self.screen_height, theme
        )

        # Попап поглощает все события
        return True

    def draw(self, surface, theme=None, font=None, title_font=None):
        """Рисует оверлей и все попапы."""
        if not self.popups and not self.overlay.is_visible:
            return

        self.overlay.draw(surface)

        for popup in self.popups:
            popup.draw(surface, theme, font, title_font)

    def resize(self, screen_width, screen_height):
        """Обновляет размеры экрана."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.overlay.resize(screen_width, screen_height)

    def close_all(self):
        """Закрывает все попапы."""
        for popup in self.popups:
            popup.close()
