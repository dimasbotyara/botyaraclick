"""
botyaraclick - screens/settings.py
Экран настроек: аудио, визуал, геймплей, справка, кредиты.
"""

import pygame

from ui.button import Button, ToggleButton
from ui.slider import Slider
from ui.panel import Panel
from ui.scrollbar import ScrollArea
from locales.locale_manager import t


class SettingsScreen:
    """Экран настроек."""

    # Вкладки
    TAB_AUDIO = "audio"
    TAB_VISUALS = "visuals"
    TAB_GAMEPLAY = "gameplay"
    TAB_HELP = "help"
    TAB_CREDITS = "credits"

    def __init__(self, screen_width, screen_height,
                 save_manager, sound_manager, locale_manager):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.save = save_manager
        self.sound = sound_manager
        self.locale = locale_manager

        self.result = None  # "back", "language_changed", "theme_changed"
        self.finished = False

        # Текущая вкладка
        self.current_tab = self.TAB_AUDIO

        # Шрифты
        self._title_font = None
        self._tab_font = None
        self._label_font = None
        self._small_font = None
        self._body_font = None

        # UI элементы
        self._tab_buttons = {}
        self._back_button = None

        # Аудио
        self._music_slider = None
        self._sfx_slider = None
        self._mute_toggle = None

        # Визуал
        self._number_format_buttons = {}
        self._particles_toggle = None
        self._floating_text_toggle = None

        # Геймплей
        self._language_buttons = []

        # Скролл для справки и кредитов
        self._help_scroll = None
        self._credits_scroll = None

        # Анимации
        self._alpha = 0
        self._target_alpha = 255

        self._initialized = False

    def init_fonts(self, fonts_dict=None):
        """Инициализирует шрифты."""
        if fonts_dict:
            self._title_font = fonts_dict.get("title")
            self._tab_font = fonts_dict.get("button")
            self._label_font = fonts_dict.get("normal")
            self._small_font = fonts_dict.get("small")
            self._body_font = fonts_dict.get("normal")

        if not self._title_font:
            self._title_font = pygame.font.Font(None, 42)
        if not self._tab_font:
            self._tab_font = pygame.font.Font(None, 24)
        if not self._label_font:
            self._label_font = pygame.font.Font(None, 22)
        if not self._small_font:
            self._small_font = pygame.font.Font(None, 18)
        if not self._body_font:
            self._body_font = pygame.font.Font(None, 20)

    def _init_ui(self):
        """Создаёт все UI элементы."""
        if self._initialized:
            return

        if not self._tab_font:
            self.init_fonts()

        # === Вкладки ===
        tabs = [
            (self.TAB_AUDIO, t("settings.audio")),
            (self.TAB_VISUALS, t("settings.visuals")),
            (self.TAB_GAMEPLAY, t("settings.gameplay")),
            (self.TAB_HELP, t("settings.help")),
            (self.TAB_CREDITS, t("settings.credits")),
        ]

        tab_w = 150
        tab_h = 40
        tab_gap = 5
        total_tabs_w = len(tabs) * (tab_w + tab_gap) - tab_gap
        tab_start_x = self.screen_width // 2 - total_tabs_w // 2

        for i, (tab_id, tab_name) in enumerate(tabs):
            btn = Button(
                tab_start_x + i * (tab_w + tab_gap),
                100,
                tab_w, tab_h,
                text=tab_name,
                font=self._tab_font,
                color=(55, 55, 75) if tab_id != self.current_tab else (60, 100, 180),
                hover_color=(75, 75, 100),
                border_radius=8,
                tag=tab_id,
            )
            self._tab_buttons[tab_id] = btn

        # === Кнопка Назад ===
        self._back_button = Button(
            self.screen_width // 2 - 100,
            self.screen_height - 70,
            200, 45,
            text=t("settings.back"),
            font=self._tab_font,
            color=(80, 80, 100),
            hover_color=(100, 100, 125),
            border_radius=8,
            tag="back",
        )

        # === Контент вкладок ===
        content_y = 160
        content_x = self.screen_width // 2 - 250

        # --- АУДИО ---
        music_vol = self.save.get_setting("music_volume", 0.7)
        sfx_vol = self.save.get_setting("sfx_volume", 0.7)
        muted = self.save.get_setting("mute_all", False)

        self._music_slider = Slider(
            content_x, content_y + 30, 400, 6,
            value=music_vol,
            label=t("settings.music_volume"),
            label_font=self._label_font,
            on_change=self._on_music_volume_change,
        )

        self._sfx_slider = Slider(
            content_x, content_y + 90, 400, 6,
            value=sfx_vol,
            label=t("settings.sfx_volume"),
            label_font=self._label_font,
            on_change=self._on_sfx_volume_change,
        )

        self._mute_toggle = ToggleButton(
            content_x, content_y + 150, 200, 40,
            text=t("settings.mute_all"),
            font=self._label_font,
            toggled=muted,
            color=(70, 70, 90),
            toggle_color=(140, 50, 50),
            border_radius=8,
            on_click=self._on_mute_toggle,
        )

        # --- ВИЗУАЛ ---
        current_fmt = self.save.get_setting("number_format", "short")
        formats = [
            ("standard", t("settings.format_standard")),
            ("short", t("settings.format_short")),
            ("scientific", t("settings.format_scientific")),
        ]

        for i, (fmt_id, fmt_name) in enumerate(formats):
            btn = Button(
                content_x, content_y + 30 + i * 50,
                400, 40,
                text=fmt_name,
                font=self._label_font,
                color=(60, 100, 160) if fmt_id == current_fmt else (55, 55, 75),
                hover_color=(80, 120, 180),
                border_radius=8,
                tag=fmt_id,
            )
            self._number_format_buttons[fmt_id] = btn

        particles_on = self.save.get_setting("particles_enabled", True)
        float_text_on = self.save.get_setting("floating_text_enabled", True)

        self._particles_toggle = ToggleButton(
            content_x, content_y + 200, 250, 40,
            text=t("settings.particles"),
            font=self._label_font,
            toggled=particles_on,
            color=(55, 55, 75),
            toggle_color=(50, 120, 80),
            border_radius=8,
            on_click=self._on_particles_toggle,
        )

        self._floating_text_toggle = ToggleButton(
            content_x, content_y + 250, 250, 40,
            text=t("settings.floating_text"),
            font=self._label_font,
            toggled=float_text_on,
            color=(55, 55, 75),
            toggle_color=(50, 120, 80),
            border_radius=8,
            on_click=self._on_floating_text_toggle,
        )

        # --- ГЕЙМПЛЕЙ ---
        languages = self.locale.get_available_languages()
        current_lang = self.save.get_language()

        self._language_buttons.clear()
        for i, (code, name) in enumerate(languages):
            btn = Button(
                content_x, content_y + 30 + i * 55,
                300, 45,
                text=name,
                font=self._label_font,
                color=(60, 100, 160) if code == current_lang else (55, 55, 75),
                hover_color=(80, 120, 180),
                border_radius=8,
                tag=code,
            )
            self._language_buttons.append(btn)

        # --- СПРАВКА ---
        self._help_scroll = ScrollArea(
            content_x - 20, content_y,
            540, self.screen_height - content_y - 90,
            content_height=500,
        )

        # --- КРЕДИТЫ ---
        self._credits_scroll = ScrollArea(
            content_x - 20, content_y,
            540, self.screen_height - content_y - 90,
            content_height=300,
        )

        self._initialized = True

    # === Callbacks ===

    def _on_music_volume_change(self, value):
        self.save.set_setting("music_volume", value)
        self.sound.set_music_volume(value)

    def _on_sfx_volume_change(self, value):
        self.save.set_setting("sfx_volume", value)
        self.sound.set_sfx_volume(value)

    def _on_mute_toggle(self, btn):
        self.save.set_setting("mute_all", btn.toggled)
        self.sound.set_muted(btn.toggled)

    def _on_particles_toggle(self, btn):
        self.save.set_setting("particles_enabled", btn.toggled)

    def _on_floating_text_toggle(self, btn):
        self.save.set_setting("floating_text_enabled", btn.toggled)

    def _switch_tab(self, tab_id):
        """Переключает вкладку."""
        self.current_tab = tab_id
        # Обновляем цвета кнопок вкладок
        for tid, btn in self._tab_buttons.items():
            if tid == tab_id:
                btn._color = (60, 100, 180)
            else:
                btn._color = (55, 55, 75)

    def handle_event(self, event):
        """Обрабатывает события."""
        self._init_ui()

        # Назад
        if self._back_button and self._back_button.handle_event(event):
            self.result = "back"
            self._target_alpha = 0
            self.sound.play("click")
            return True

        # ESC
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.result = "back"
            self._target_alpha = 0
            return True

        # Вкладки
        for tab_id, btn in self._tab_buttons.items():
            if btn.handle_event(event):
                self._switch_tab(tab_id)
                self.sound.play("click")
                return True

        # Контент текущей вкладки
        if self.current_tab == self.TAB_AUDIO:
            if self._music_slider and self._music_slider.handle_event(event):
                return True
            if self._sfx_slider and self._sfx_slider.handle_event(event):
                return True
            if self._mute_toggle and self._mute_toggle.handle_event(event):
                return True

        elif self.current_tab == self.TAB_VISUALS:
            for fmt_id, btn in self._number_format_buttons.items():
                if btn.handle_event(event):
                    self.save.set_setting("number_format", fmt_id)
                    # Обновляем цвета
                    for fid, fbtn in self._number_format_buttons.items():
                        fbtn._color = (60, 100, 160) if fid == fmt_id else (55, 55, 75)
                    self.sound.play("click")
                    return True

            if self._particles_toggle and self._particles_toggle.handle_event(event):
                return True
            if self._floating_text_toggle and self._floating_text_toggle.handle_event(event):
                return True

        elif self.current_tab == self.TAB_GAMEPLAY:
            for btn in self._language_buttons:
                if btn.handle_event(event):
                    new_lang = btn.tag
                    self.save.set_language(new_lang)
                    self.locale.load_locale(new_lang)
                    # Обновляем цвета
                    for lb in self._language_buttons:
                        lb._color = (60, 100, 160) if lb.tag == new_lang else (55, 55, 75)
                    self.result = "language_changed"
                    self.sound.play("click")
                    # Нужно пересоздать UI с новым языком
                    self._initialized = False
                    return True

        elif self.current_tab == self.TAB_HELP:
            if self._help_scroll:
                self._help_scroll.handle_event(event)

        elif self.current_tab == self.TAB_CREDITS:
            if self._credits_scroll:
                self._credits_scroll.handle_event(event)

        return False

    def update(self, dt):
        """Обновляет экран."""
        self._init_ui()

        # Альфа
        speed = 400 * dt
        if self._alpha < self._target_alpha:
            self._alpha = min(self._alpha + speed, self._target_alpha)
        elif self._alpha > self._target_alpha:
            self._alpha = max(self._alpha - speed, self._target_alpha)

        if self.result == "back" and self._alpha <= 0:
            self.finished = True

        # Кнопки
        mouse_pos = pygame.mouse.get_pos()
        for btn in self._tab_buttons.values():
            btn.update(dt, mouse_pos)
        if self._back_button:
            self._back_button.update(dt, mouse_pos)

        # Контент вкладок
        if self.current_tab == self.TAB_AUDIO:
            if self._music_slider:
                self._music_slider.update(dt)
            if self._sfx_slider:
                self._sfx_slider.update(dt)
            if self._mute_toggle:
                self._mute_toggle.update(dt, mouse_pos)

        elif self.current_tab == self.TAB_VISUALS:
            for btn in self._number_format_buttons.values():
                btn.update(dt, mouse_pos)
            if self._particles_toggle:
                self._particles_toggle.update(dt, mouse_pos)
            if self._floating_text_toggle:
                self._floating_text_toggle.update(dt, mouse_pos)

        elif self.current_tab == self.TAB_GAMEPLAY:
            for btn in self._language_buttons:
                btn.update(dt, mouse_pos)

        elif self.current_tab == self.TAB_HELP:
            if self._help_scroll:
                self._help_scroll.update(dt)

        elif self.current_tab == self.TAB_CREDITS:
            if self._credits_scroll:
                self._credits_scroll.update(dt)

    def draw(self, surface, theme=None):
        """Рисует экран настроек."""
        self._init_ui()

        # Фон
        bg_color = (25, 25, 38)
        if theme:
            bg_color = theme.get("bg_color", bg_color)
        surface.fill(bg_color)

        # Заголовок
        if self._title_font:
            title_surf = self._title_font.render(
                t("settings.title"), True, (200, 210, 230)
            )
            title_surf.set_alpha(int(self._alpha))
            title_rect = title_surf.get_rect(
                center=(self.screen_width // 2, 50)
            )
            surface.blit(title_surf, title_rect)

        # Вкладки
        for btn in self._tab_buttons.values():
            btn.draw(surface, theme)

        # Контент
        content_y = 160
        content_x = self.screen_width // 2 - 250

        if self.current_tab == self.TAB_AUDIO:
            self._draw_audio_tab(surface, content_x, content_y, theme)
        elif self.current_tab == self.TAB_VISUALS:
            self._draw_visuals_tab(surface, content_x, content_y, theme)
        elif self.current_tab == self.TAB_GAMEPLAY:
            self._draw_gameplay_tab(surface, content_x, content_y, theme)
        elif self.current_tab == self.TAB_HELP:
            self._draw_help_tab(surface, content_x, content_y, theme)
        elif self.current_tab == self.TAB_CREDITS:
            self._draw_credits_tab(surface, content_x, content_y, theme)

        # Назад
        if self._back_button:
            self._back_button.draw(surface, theme)

    def _draw_audio_tab(self, surface, x, y, theme):
        """Рисует вкладку аудио."""
        if self._music_slider:
            self._music_slider.draw(surface, theme)
        if self._sfx_slider:
            self._sfx_slider.draw(surface, theme)
        if self._mute_toggle:
            self._mute_toggle.draw(surface, theme)

    def _draw_visuals_tab(self, surface, x, y, theme):
        """Рисует вкладку визуала."""
        # Заголовок секции
        if self._label_font:
            sec_surf = self._label_font.render(
                t("settings.number_format"), True, (180, 180, 200)
            )
            surface.blit(sec_surf, (x, y + 5))

        for btn in self._number_format_buttons.values():
            btn.draw(surface, theme)

        # Разделитель
        if self._label_font:
            eff_surf = self._label_font.render(
                t("settings.effects_enabled"), True, (180, 180, 200)
            )
            surface.blit(eff_surf, (x, y + 175))

        if self._particles_toggle:
            self._particles_toggle.draw(surface, theme)
        if self._floating_text_toggle:
            self._floating_text_toggle.draw(surface, theme)

    def _draw_gameplay_tab(self, surface, x, y, theme):
        """Рисует вкладку геймплея."""
        if self._label_font:
            lang_surf = self._label_font.render(
                t("settings.language"), True, (180, 180, 200)
            )
            surface.blit(lang_surf, (x, y + 5))

        for btn in self._language_buttons:
            btn.draw(surface, theme)

    def _draw_help_tab(self, surface, x, y, theme):
        """Рисует вкладку справки."""
        text_color = (200, 210, 230)
        if theme:
            text_color = theme.get("text_color", text_color)

        if self._help_scroll and self._body_font:
            def draw_help_content(surf, scroll_y):
                cy = y - scroll_y

                sections = [
                    (t("help.intro"), True),
                    (t("help.goal"), False),
                    ("", False),
                    (t("help.basics"), True),
                    (t("help.basics_text"), False),
                    ("", False),
                    (t("help.upgrades_help"), True),
                    (t("help.upgrades_text"), False),
                    ("", False),
                    (t("help.events_help"), True),
                    (t("help.events_text"), False),
                    ("", False),
                    (t("help.prestige_help"), True),
                    (t("help.prestige_text"), False),
                    ("", False),
                    (t("help.hotkeys"), True),
                    (t("help.hotkeys_text"), False),
                ]

                for text, is_header in sections:
                    if not text:
                        cy += 10
                        continue

                    font = self._label_font if is_header else self._body_font
                    color = (100, 180, 255) if is_header else text_color

                    # Перенос строк
                    lines = text.split('\n')
                    for line in lines:
                        # Разбиваем длинные строки
                        words = line.split(' ')
                        current_line = ""
                        for word in words:
                            test = current_line + (" " if current_line else "") + word
                            if font.size(test)[0] < 500:
                                current_line = test
                            else:
                                if current_line:
                                    line_surf = font.render(current_line, True, color)
                                    surf.blit(line_surf, (x, cy))
                                    cy += line_surf.get_height() + 3
                                current_line = word
                        if current_line:
                            line_surf = font.render(current_line, True, color)
                            surf.blit(line_surf, (x, cy))
                            cy += line_surf.get_height() + 3

                # Обновляем высоту контента
                self._help_scroll.set_content_height(cy - y + scroll_y + 20)

            self._help_scroll.draw(surface, theme, draw_help_content)

    def _draw_credits_tab(self, surface, x, y, theme):
        """Рисует вкладку кредитов."""
        text_color = (200, 210, 230)
        if theme:
            text_color = theme.get("text_color", text_color)

        if self._credits_scroll and self._body_font:
            def draw_credits_content(surf, scroll_y):
                cy = y - scroll_y + 20

                lines = [
                    (t("credits.title"), self._title_font, (100, 180, 255)),
                    ("", None, None),
                    (t("credits.creator"), self._label_font, text_color),
                    ("", None, None),
                    (t("credits.engine"), self._body_font, (150, 160, 180)),
                    ("", None, None),
                    ("", None, None),
                    (t("credits.thanks"), self._label_font, (180, 200, 120)),
                ]

                for text, font, color in lines:
                    if not text or not font:
                        cy += 15
                        continue

                    line_surf = font.render(text, True, color)
                    line_rect = line_surf.get_rect(
                        center=(self.screen_width // 2, cy)
                    )
                    surf.blit(line_surf, line_rect)
                    cy += line_surf.get_height() + 8

                self._credits_scroll.set_content_height(cy - y + scroll_y + 20)

            self._credits_scroll.draw(surface, theme, draw_credits_content)

    def reset(self):
        """Сбрасывает экран."""
        self.result = None
        self.finished = False
        self._alpha = 0
        self._target_alpha = 255
        self._initialized = False

    def resize(self, width, height):
        """Обновляет размеры."""
        self.screen_width = width
        self.screen_height = height
        self._initialized = False
