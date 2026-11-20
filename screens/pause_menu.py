"""
botyaraclick - screens/pause_menu.py
Меню паузы.

Содержит кнопки:
- Продолжить
- Сохранить игру
- Достижения
- Статистика
- Настройки
- Главное меню
"""

import pygame

from ui.button import Button
from ui.panel import Panel, DarkOverlay
from ui.popup import PopupManager
from locales.locale_manager import t
from economy import format_money, format_number, format_time, format_percent
from ui.fonts import get_font


class PauseMenuScreen:
    """Меню паузы."""

    def __init__(self, screen_width, screen_height,
                 save_manager, sound_manager, economy=None):
        self.sw = screen_width
        self.sh = screen_height
        self.save = save_manager
        self.sound = sound_manager
        self.economy = economy

        # Результат
        self.result = None
        # Возможные: "resume", "save", "achievements", "statistics",
        #            "settings", "main_menu", "quit_no_save"
        self.finished = False

        # UI
        self._buttons = {}
        self._back_button = None
        self._overlay = DarkOverlay(screen_width, screen_height, alpha=160)
        self._popup_manager = PopupManager(screen_width, screen_height)

        # Шрифты
        self._title_font = None
        self._button_font = None
        self._info_font = None
        self._small_font = None

        # Анимация
        self._panel_alpha = 0
        self._target_panel_alpha = 255

        # Раскладка панели (пересчитывается в _init_ui)
        self._panel_rect = pygame.Rect(0, 0, 0, 0)
        self._title_pos = (0, 0)

        # Субэкран: статистика / достижения
        self._sub_screen = None  # "statistics", "achievements"
        self._sub_scroll = 0

        self._initialized = False

    def init_fonts(self, fonts_dict=None):
        """Инициализирует шрифты."""
        if fonts_dict:
            self._title_font = fonts_dict.get("title")
            self._button_font = fonts_dict.get("button")
            self._info_font = fonts_dict.get("normal")
            self._small_font = fonts_dict.get("small")

        if not self._title_font:
            self._title_font = get_font(42, bold=True)
        if not self._button_font:
            self._button_font = get_font(26)
        if not self._info_font:
            self._info_font = get_font(20)
        if not getattr(self, "_small_font", None):
            self._small_font = get_font(16)

    def _init_ui(self):
        """Создаёт UI."""
        if self._initialized:
            return

        if not self._button_font:
            self.init_fonts()

        self._overlay.show()

        cx = self.sw // 2

        buttons_def = [
            ("resume", t("pause.resume"), (50, 140, 80), (60, 170, 95)),
            ("save", t("pause.save"), (50, 100, 160), (65, 120, 185)),
            ("achievements", t("pause.achievements"), (70, 70, 90), (90, 90, 115)),
            ("statistics", t("pause.statistics"), (70, 70, 90), (90, 90, 115)),
            ("settings", t("pause.settings"), (70, 70, 90), (90, 90, 115)),
            ("main_menu", t("pause.main_menu"), (140, 60, 50), (170, 75, 60)),
        ]

        # --- Раскладка: панель всегда вмещает ВСЕ кнопки ---
        btn_w = max(200, min(300, self.sw - 80))
        btn_h = 46
        gap = 10
        title_h = 66
        padding = 22

        def panel_height(bh, gp, th, pad):
            return th + len(buttons_def) * bh + (len(buttons_def) - 1) * gp + pad

        # Подгоняем под высоту окна (маленькие окна / низкое разрешение)
        available = self.sh - 40
        while panel_height(btn_h, gap, title_h, padding) > available and btn_h > 26:
            btn_h -= 2
            gap = max(5, gap - 1)
        if panel_height(btn_h, gap, title_h, padding) > available:
            title_h = max(40, title_h - 12)
            padding = max(10, padding - 6)
        if panel_height(btn_h, gap, title_h, padding) > available:
            # Совсем маленькое окно — ещё сильнее ужимаем кнопки
            btn_h = max(20, (available - title_h - padding) // len(buttons_def) - gap)

        panel_w = btn_w + padding * 2
        panel_h = panel_height(btn_h, gap, title_h, padding)
        panel_x = cx - panel_w // 2
        panel_y = max(8, (self.sh - panel_h) // 2)

        self._panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        self._title_pos = (cx, panel_y + title_h // 2 + 4)

        first_y = panel_y + title_h

        self._buttons.clear()
        for i, (bid, btext, bcol, bhov) in enumerate(buttons_def):
            btn = Button(
                cx - btn_w // 2,
                first_y + i * (btn_h + gap),
                btn_w, btn_h,
                text=btext,
                font=self._button_font,
                color=bcol,
                hover_color=bhov,
                text_color=(230, 230, 240),
                border_radius=10,
                tag=bid,
            )
            self._buttons[bid] = btn

        self._initialized = True

    def handle_event(self, event):
        """Обрабатывает события."""
        self._init_ui()

        # Попапы
        if self._popup_manager.has_popup:
            self._popup_manager.handle_event(event, self._button_font)
            return True

        # Субэкраны
        if self._sub_screen:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._sub_screen = None
                return True
            if event.type == pygame.MOUSEWHEEL:
                self._sub_scroll = max(0, self._sub_scroll - event.y * 34)
                return True
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._sub_screen = None
                self._sub_scroll = 0
                return True
            return True

        # ESC = resume
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.result = "resume"
            self._start_close()
            return True

        # Кнопки
        for btn_id, btn in self._buttons.items():
            if btn.handle_event(event):
                self._handle_button(btn_id)
                return True

        return True  # Пауза поглощает все события

    def _handle_button(self, btn_id):
        """Обрабатывает нажатие кнопки."""
        self.sound.play("click")

        if btn_id == "resume":
            self.result = "resume"
            self._start_close()

        elif btn_id == "save":
            success = self.save.save_current()
            if success:
                self.sound.play("save")
                self._popup_manager.show_info(
                    title=t("pause.save"),
                    message=t("pause.save_success"),
                )

        elif btn_id == "achievements":
            self._sub_screen = "achievements"
            self._sub_scroll = 0

        elif btn_id == "statistics":
            self._sub_screen = "statistics"
            self._sub_scroll = 0

        elif btn_id == "settings":
            self.result = "settings"
            self._start_close()

        elif btn_id == "main_menu":
            self._popup_manager.show_choice(
                title=t("pause.confirm_quit"),
                message=t("pause.unsaved_warning"),
                choices=[
                    {"text": t("pause.save_and_quit"), "value": "save_quit"},
                    {"text": t("pause.quit_no_save"), "value": "no_save"},
                    {"text": t("common.cancel"), "value": "cancel"},
                ],
                on_result=self._on_quit_choice,
            )

    def _on_quit_choice(self, result):
        """Обработчик выбора выхода."""
        if result == "save_quit":
            self.save.save_current()
            self.sound.play("save")
            self.result = "main_menu"
            self._start_close()
        elif result == "no_save":
            self.result = "main_menu"
            self._start_close()
        # cancel — ничего не делаем

    def _start_close(self):
        """Начинает анимацию закрытия."""
        self._overlay.hide()
        self._target_panel_alpha = 0

    def update(self, dt):
        """Обновляет экран."""
        self._init_ui()

        self._overlay.update(dt)
        self._popup_manager.update(dt, pygame.mouse.get_pos())

        # Анимация панели
        speed = 8.0 * dt
        diff_a = self._target_panel_alpha - self._panel_alpha
        self._panel_alpha += diff_a * min(speed, 1.0)

        # Закрытие
        if self.result and self._panel_alpha < 10 and not self._overlay.is_visible:
            self.finished = True

        # Кнопки
        mouse_pos = pygame.mouse.get_pos()
        if not self._sub_screen:
            for btn in self._buttons.values():
                btn.update(dt, mouse_pos)

    def draw(self, surface, theme=None):
        """Рисует меню паузы поверх игры."""
        self._init_ui()

        # Затемнение
        self._overlay.draw(surface)

        if self._sub_screen == "statistics":
            self._draw_statistics(surface, theme)
        elif self._sub_screen == "achievements":
            self._draw_achievements(surface, theme)
        else:
            self._draw_main_pause(surface, theme)

        # Попапы
        self._popup_manager.draw(surface, theme, self._button_font, self._title_font)

    def _draw_main_pause(self, surface, theme):
        """Рисует основное меню паузы."""
        alpha = max(0, min(255, int(self._panel_alpha)))
        if alpha <= 0:
            return

        rect = self._panel_rect
        if rect.width <= 0:
            return

        # Рисуем панель вместе с кнопками на отдельном слое — так всё
        # меню плавно появляется и исчезает целиком, и ничего не «вылезает».
        layer = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)

        bg_color = (35, 35, 50) if not theme else theme.get("panel_color", (35, 35, 50))
        border_color = (60, 60, 80) if not theme else theme.get("panel_border", (60, 60, 80))

        pygame.draw.rect(layer, (*bg_color, 252), rect, border_radius=16)
        pygame.draw.rect(layer, (*border_color, 255), rect, width=2, border_radius=16)

        # Заголовок
        if self._title_font:
            title_surf = self._title_font.render(
                t("pause.title"), True, (220, 220, 240)
            )
            title_rect = title_surf.get_rect(center=self._title_pos)
            layer.blit(title_surf, title_rect)

        # Кнопки
        for btn in self._buttons.values():
            btn.draw(layer, theme)

        layer.set_alpha(alpha)
        surface.blit(layer, (0, 0))

    def _draw_statistics(self, surface, theme):
        """Рисует экран статистики."""
        text_color = (220, 220, 240)
        dim_color = (150, 160, 180)
        money_color = (80, 220, 120)

        if theme:
            text_color = theme.get("text_color", text_color)
            dim_color = theme.get("text_dim", dim_color)
            money_color = theme.get("money_color", money_color)

        # Фон панели (не больше окна)
        panel_w = min(520, self.sw - 40)
        panel_h = min(500, self.sh - 60)
        px = self.sw // 2 - panel_w // 2
        py = self.sh // 2 - panel_h // 2

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg = theme.get("panel_color", (35, 35, 50)) if theme else (35, 35, 50)
        pygame.draw.rect(panel_surf, (*bg, 240), (0, 0, panel_w, panel_h), border_radius=12)
        surface.blit(panel_surf, (px, py))

        # Заголовок
        if self._title_font:
            title_surf = self._title_font.render(
                t("statistics.title"), True, text_color
            )
            title_rect = title_surf.get_rect(center=(self.sw // 2, py + 30))
            surface.blit(title_surf, title_rect)

        if not self._info_font:
            return

        num_fmt = self.save.get_setting("number_format", "short")

        stats = [
            (t("statistics.total_earned"),
             format_money(self.save.get_save_data("total_earned", 0), num_fmt)),
            (t("statistics.total_clicks"),
             format_number(self.save.get_save_data("total_clicks", 0), num_fmt)),
            (t("statistics.total_purchases"),
             str(self.save.get_save_data("total_purchases", 0))),
            (t("statistics.play_time"),
             format_time(self.save.get_save_data("play_time", 0))),
            (t("statistics.click_power"),
             format_money(self.economy.click_power, num_fmt) if self.economy else "?"),
            (t("statistics.passive_income"),
             (format_money(self.economy.passive_income, num_fmt) + "/s") if self.economy else "?"),
            (t("statistics.crit_chance"),
             format_percent(self.economy.crit_chance) if self.economy else "?"),
            (t("statistics.prestige_count"),
             str(self.save.get_save_data("prestige_count", 0))),
            (t("statistics.total_rp"),
             str(self.save.get_save_data("total_rp", 0))),
            (t("statistics.golden_caught"),
             str(self.save.get_save_data("golden_caught", 0))),
            (t("statistics.deals_won"),
             str(self.save.get_save_data("deals_won", 0))),
            (t("statistics.deals_lost"),
             str(self.save.get_save_data("deals_lost", 0))),
            (t("statistics.challenges_completed"),
             str(self.save.get_save_data("challenges_completed", 0))),
            (t("statistics.debuffs_survived"),
             str(self.save.get_save_data("debuffs_survived", 0))),
        ]

        row_h = max(20, min(28, (panel_h - 90) // max(1, len(stats))))
        cy = py + 60
        for label, value in stats:
            label_surf = self._info_font.render(label + ":", True, dim_color)
            value_surf = self._info_font.render(value, True, money_color)

            surface.blit(label_surf, (px + 25, cy))
            value_rect = value_surf.get_rect(right=px + panel_w - 25, top=cy)
            surface.blit(value_surf, value_rect)

            cy += row_h

        # Подсказка
        hint_surf = self._info_font.render(
            t("common.hint_close"), True, (100, 100, 120)
        )
        hint_rect = hint_surf.get_rect(center=(self.sw // 2, py + panel_h - 20))
        surface.blit(hint_surf, hint_rect)

    def _draw_achievements(self, surface, theme):
        """Рисует экран достижений."""
        from data.achievements import ACHIEVEMENTS, ACHIEVEMENT_CATEGORIES

        text_color = (220, 220, 240)
        dim_color = (150, 160, 180)
        unlock_color = (100, 220, 140)
        lock_color = (100, 100, 120)

        if theme:
            text_color = theme.get("text_color", text_color)
            dim_color = theme.get("text_dim", dim_color)

        panel_w = min(600, self.sw - 40)
        panel_h = min(560, self.sh - 60)
        px = self.sw // 2 - panel_w // 2
        py = self.sh // 2 - panel_h // 2

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg = theme.get("panel_color", (35, 35, 50)) if theme else (35, 35, 50)
        pygame.draw.rect(panel_surf, (*bg, 240), (0, 0, panel_w, panel_h), border_radius=12)
        surface.blit(panel_surf, (px, py))

        # Заголовок
        if self._title_font:
            unlocked_count = self.achievement_tracker_ref.get_unlocked_count() if hasattr(self, 'achievement_tracker_ref') else 0
            total_count = len(ACHIEVEMENTS)
            title_str = f"{t('achievements.title')} ({unlocked_count}/{total_count})"
            title_surf = self._title_font.render(title_str, True, text_color)
            title_rect = title_surf.get_rect(center=(self.sw // 2, py + 30))
            surface.blit(title_surf, title_rect)

        font = self._small_font or self._info_font
        if not font:
            return

        unlocked_ids = self.save.get_save_data("achievements", [])

        # Прокручиваемый список: все достижения доступны колесом мыши
        row_h = font.get_height() + 8
        list_top = py + 62
        list_bottom = py + panel_h - 36
        visible_h = max(1, list_bottom - list_top)
        max_scroll = max(0, len(ACHIEVEMENTS) * row_h - visible_h)
        self._sub_scroll = max(0, min(self._sub_scroll, max_scroll))

        surface.set_clip(pygame.Rect(px + 12, list_top, panel_w - 24, visible_h))

        cy = list_top - self._sub_scroll

        for ach in ACHIEVEMENTS:
            if cy + row_h < list_top:
                cy += row_h
                continue
            if cy > list_bottom:
                break

            is_unlocked = ach["id"] in unlocked_ids
            is_secret = ach.get("secret", False)

            if is_unlocked:
                name = t(f"achievements.{ach['id']}")
                icon = "✅"
                color = unlock_color
            elif is_secret:
                name = t("achievements.secret")
                icon = "❓"
                color = lock_color
            else:
                name = t(f"achievements.{ach['id']}")
                icon = "🔒"
                color = lock_color

            line = f"{icon} {name}"
            line_surf = font.render(line, True, color)
            surface.blit(line_surf, (px + 20, cy))
            cy += row_h

        surface.set_clip(None)

        # Индикатор прокрутки
        if max_scroll > 0:
            track_h = visible_h
            thumb_h = max(30, int(track_h * visible_h / (len(ACHIEVEMENTS) * row_h)))
            thumb_y = list_top + int((track_h - thumb_h) * (self._sub_scroll / max_scroll))
            pygame.draw.rect(
                surface, (70, 70, 95),
                (px + panel_w - 14, list_top, 5, track_h), border_radius=3
            )
            pygame.draw.rect(
                surface, (120, 120, 155),
                (px + panel_w - 14, thumb_y, 5, thumb_h), border_radius=3
            )

        # Подсказка
        hint_surf = self._info_font.render(
            t("common.hint_close"), True, (100, 100, 120)
        )
        hint_rect = hint_surf.get_rect(center=(self.sw // 2, py + panel_h - 20))
        surface.blit(hint_surf, hint_rect)

    def set_achievement_tracker(self, tracker):
        """Устанавливает ссылку на трекер достижений."""
        self.achievement_tracker_ref = tracker

    def reset(self):
        """Сбрасывает состояние."""
        self.result = None
        self.finished = False
        self._panel_alpha = 0
        self._target_panel_alpha = 255
        self._sub_screen = None
        self._sub_scroll = 0
        self._initialized = False
        self._overlay = DarkOverlay(self.sw, self.sh, alpha=160)

    def resize(self, width, height):
        """Обновляет размеры."""
        self.sw = width
        self.sh = height
        self._overlay.resize(width, height)
        self._popup_manager.resize(width, height)
        self._initialized = False
