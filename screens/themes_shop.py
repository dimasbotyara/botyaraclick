"""
botyaraclick - screens/themes_shop.py
Магазин тем оформления.

Показывает все 13 тем с превью цветов.
Купленные темы можно экипировать.
Покупка за игровую валюту, сохраняется глобально.
"""

import pygame
import math

from ui.button import Button
from ui.scrollbar import ScrollArea
from economy import format_money, format_number
from data.themes import THEMES, THEME_ORDER, get_theme
from locales.locale_manager import t


class ThemesShopScreen:
    """Магазин тем оформления."""

    def __init__(self, screen_width, screen_height,
                 save_manager, sound_manager):
        self.sw = screen_width
        self.sh = screen_height
        self.save = save_manager
        self.sound = sound_manager

        # Результат
        self.result = None  # "back", "theme_changed"
        self.finished = False
        self.theme_changed = False

        # Шрифты
        self._fonts = {}

        # UI
        self._back_button = None
        self._scroll = None
        self._theme_buttons = {}  # theme_id -> {"buy": Button, "equip": Button}

        # Анимация
        self._alpha = 0
        self._target_alpha = 255

        self._num_format = save_manager.get_setting("number_format", "short")
        self._initialized = False

    def init_fonts(self, fonts_dict=None):
        """Инициализирует шрифты."""
        if fonts_dict:
            self._fonts = fonts_dict
        else:
            self._fonts = {
                "title": pygame.font.Font(None, 36),
                "button": pygame.font.Font(None, 22),
                "normal": pygame.font.Font(None, 20),
                "small": pygame.font.Font(None, 16),
            }

    def _init_ui(self):
        """Создаёт UI."""
        if self._initialized:
            return

        if not self._fonts:
            self.init_fonts()

        # Назад
        self._back_button = Button(
            20, 12, 120, 38,
            text=t("common.back"),
            font=self._fonts.get("button"),
            color=(80, 80, 100),
            hover_color=(100, 100, 125),
            border_radius=8,
            tag="back",
        )

        # Скролл
        scroll_top = 70
        scroll_h = self.sh - scroll_top - 10

        card_h = 130
        gap = 12
        content_h = len(THEME_ORDER) * (card_h + gap) + 20

        self._scroll = ScrollArea(
            10, scroll_top,
            self.sw - 20, scroll_h,
            content_height=content_h,
            scroll_speed=40,
        )

        self._initialized = True

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

        # Скролл
        if self._scroll and self._scroll.handle_event(event):
            return True

        # Клик по карточкам тем
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = self._get_theme_action_at(event.pos)
            if clicked:
                theme_id, action = clicked
                self._handle_theme_action(theme_id, action)
                return True

        return False

    def _get_theme_action_at(self, pos):
        """Определяет, на какую тему и кнопку нажали."""
        if not self._scroll:
            return None

        mx, my = pos
        if not self._scroll.rect.collidepoint(pos):
            return None

        scroll_y = int(self._scroll.scroll_y)
        card_h = 130
        gap = 12
        cards_top = self._scroll.rect.top

        for i, theme_id in enumerate(THEME_ORDER):
            card_y = cards_top + 10 + i * (card_h + gap) - scroll_y

            if card_y + card_h < self._scroll.rect.top:
                continue
            if card_y > self._scroll.rect.bottom:
                break

            # Кнопка действия (правая часть карточки)
            btn_x = self._scroll.rect.right - 140
            btn_y = card_y + card_h - 45
            btn_rect = pygame.Rect(btn_x, btn_y, 120, 35)

            if btn_rect.collidepoint(mx, my):
                is_owned = self.save.is_theme_unlocked(theme_id)
                current_theme = self.save.get_save_data("current_theme", "default")
                is_equipped = theme_id == current_theme

                if is_equipped:
                    return None  # Уже экипировано
                elif is_owned:
                    return (theme_id, "equip")
                else:
                    return (theme_id, "buy")

        return None

    def _handle_theme_action(self, theme_id, action):
        """Обрабатывает действие с темой."""
        if action == "buy":
            theme_data = get_theme(theme_id)
            cost = theme_data.get("cost", 0)
            money = self.save.get_save_data("money", 0)

            if money >= cost:
                # Покупаем
                self.save.update_save_data("money", money - cost)
                self.save.unlock_theme(theme_id)
                self.sound.play("buy")
            else:
                self.sound.play("error")

        elif action == "equip":
            self.save.update_save_data("current_theme", theme_id)
            self.theme_changed = True
            self.sound.play("theme_change")

    def update(self, dt):
        """Обновляет экран."""
        self._init_ui()

        # Альфа
        speed = 400 * dt
        if self._alpha < self._target_alpha:
            self._alpha = min(self._alpha + speed, self._target_alpha)
        elif self._alpha > self._target_alpha:
            self._alpha = max(self._alpha - speed, self._target_alpha)

        if self.result and self._alpha <= 0:
            self.finished = True

        # Скролл
        if self._scroll:
            self._scroll.update(dt)

        # Кнопки
        mouse_pos = pygame.mouse.get_pos()
        if self._back_button:
            self._back_button.update(dt, mouse_pos)

        self._num_format = self.save.get_setting("number_format", "short")

    def draw(self, surface, theme=None):
        """Рисует магазин тем."""
        self._init_ui()

        # Фон
        bg = (22, 22, 35)
        if theme:
            bg = theme.get("bg_color", bg)
        surface.fill(bg)

        text_color = (220, 220, 240)
        dim_color = (120, 130, 150)
        money_color = (80, 220, 120)
        danger_color = (220, 80, 80)

        if theme:
            text_color = theme.get("text_color", text_color)
            dim_color = theme.get("text_dim", dim_color)
            money_color = theme.get("money_color", money_color)

        # Заголовок
        if self._fonts.get("title"):
            title_surf = self._fonts["title"].render(
                t("themes.title"), True, text_color
            )
            title_rect = title_surf.get_rect(center=(self.sw // 2, 30))
            surface.blit(title_surf, title_rect)

        # Баланс
        if self._fonts.get("normal"):
            money = self.save.get_save_data("money", 0)
            money_str = format_money(money, self._num_format)
            money_surf = self._fonts["normal"].render(money_str, True, money_color)
            money_rect = money_surf.get_rect(topright=(self.sw - 20, 15))
            surface.blit(money_surf, money_rect)

        # Назад
        if self._back_button:
            self._back_button.draw(surface, theme)

        # Карточки тем
        if self._scroll:
            current_theme = self.save.get_save_data("current_theme", "default")
            money = self.save.get_save_data("money", 0)

            def draw_cards(surf, scroll_y):
                card_h = 130
                gap = 12
                cards_top = self._scroll.rect.top
                card_w = self._scroll.rect.width - 20

                font_normal = self._fonts.get("normal")
                font_small = self._fonts.get("small")
                font_button = self._fonts.get("button")

                for i, theme_id in enumerate(THEME_ORDER):
                    card_y = cards_top + 10 + i * (card_h + gap) - scroll_y

                    if card_y + card_h < self._scroll.rect.top - 5:
                        continue
                    if card_y > self._scroll.rect.bottom + 5:
                        break

                    td = get_theme(theme_id)
                    is_owned = self.save.is_theme_unlocked(theme_id)
                    is_equipped = theme_id == current_theme
                    cost = td.get("cost", 0)
                    can_afford = money >= cost

                    card_x = self._scroll.rect.x + 10

                    # Фон карточки
                    if is_equipped:
                        card_bg = (40, 60, 45)
                        card_border = (80, 180, 100)
                    elif is_owned:
                        card_bg = (40, 45, 55)
                        card_border = (80, 100, 140)
                    else:
                        card_bg = (35, 35, 48)
                        card_border = (60, 60, 78)

                    # Hover
                    mouse_pos = pygame.mouse.get_pos()
                    card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
                    if card_rect.collidepoint(mouse_pos):
                        card_bg = tuple(min(c + 10, 255) for c in card_bg)

                    card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                    pygame.draw.rect(card_surf, (*card_bg, 230),
                                    (0, 0, card_w, card_h), border_radius=10)
                    pygame.draw.rect(card_surf, (*card_border, 200),
                                    (0, 0, card_w, card_h), width=2, border_radius=10)
                    surf.blit(card_surf, (card_x, card_y))

                    # Превью цветов (маленькие цветные квадратики)
                    preview_x = card_x + 15
                    preview_y = card_y + 15
                    preview_size = 25
                    preview_gap = 5

                    preview_colors = [
                        td.get("bg_color", (30, 30, 40)),
                        td.get("panel_color", (40, 40, 55)),
                        td.get("button_color", (50, 100, 200)),
                        td.get("text_color", (230, 230, 240)),
                        td.get("money_color", (80, 220, 120)),
                        td.get("accent_color", (50, 150, 255)),
                    ]

                    for j, color in enumerate(preview_colors):
                        px = preview_x + j * (preview_size + preview_gap)
                        pygame.draw.rect(surf, color,
                                        (px, preview_y, preview_size, preview_size),
                                        border_radius=4)
                        pygame.draw.rect(surf, (255, 255, 255, 40),
                                        (px, preview_y, preview_size, preview_size),
                                        width=1, border_radius=4)

                    # Название темы
                    theme_name = t(f"themes.{theme_id}")
                    if font_normal:
                        name_surf = font_normal.render(theme_name, True, text_color)
                        surf.blit(name_surf, (preview_x, card_y + 50))

                    # Шрифт темы
                    font_name = td.get("font_file", "")
                    if font_small and font_name:
                        font_info = font_small.render(
                            f"Font: {font_name}", True, dim_color
                        )
                        surf.blit(font_info, (preview_x, card_y + 72))

                    # Эффект фона
                    bg_effect = td.get("bg_effect", "none")
                    if font_small and bg_effect != "none":
                        effect_info = font_small.render(
                            f"Effect: {bg_effect}", True, dim_color
                        )
                        surf.blit(effect_info, (preview_x, card_y + 90))

                    # Кнопка действия (правая часть)
                    btn_x = card_x + card_w - 135
                    btn_y = card_y + card_h - 45
                    btn_w = 120
                    btn_h = 35

                    if is_equipped:
                        btn_bg = (50, 100, 60)
                        btn_text = t("themes.equipped")
                        btn_text_c = (150, 220, 160)
                    elif is_owned:
                        btn_bg = (50, 90, 150)
                        btn_text = t("themes.equip")
                        btn_text_c = (200, 220, 255)
                    elif can_afford:
                        btn_bg = (50, 120, 70)
                        cost_str = format_money(cost, self._num_format)
                        btn_text = f"{t('shop.buy')}".replace("${cost}", cost_str)
                        if "${cost}" not in t("shop.buy"):
                            btn_text = f"Buy {cost_str}"
                        btn_text_c = (200, 255, 200)
                    else:
                        btn_bg = (100, 50, 50)
                        cost_str = format_money(cost, self._num_format)
                        btn_text = cost_str
                        btn_text_c = (200, 150, 150)

                    # Hover кнопки
                    btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
                    if btn_rect.collidepoint(mouse_pos) and not is_equipped:
                        btn_bg = tuple(min(c + 20, 255) for c in btn_bg)

                    btn_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
                    pygame.draw.rect(btn_surf, (*btn_bg, 220),
                                    (0, 0, btn_w, btn_h), border_radius=6)
                    surf.blit(btn_surf, (btn_x, btn_y))

                    if font_small:
                        # Обрезаем текст если не влезает
                        while font_small.size(btn_text)[0] > btn_w - 12 and len(btn_text) > 5:
                            btn_text = btn_text[:-1]
                        bt_surf = font_small.render(btn_text, True, btn_text_c)
                        bt_rect = bt_surf.get_rect(center=(btn_x + btn_w // 2, btn_y + btn_h // 2))
                        surf.blit(bt_surf, bt_rect)

                    # Иконка "экипировано"
                    if is_equipped and font_normal:
                        check_surf = font_normal.render("✓", True, (80, 200, 100))
                        check_rect = check_surf.get_rect(
                            right=card_x + card_w - 15,
                            top=card_y + 10
                        )
                        surf.blit(check_surf, check_rect)

            self._scroll.draw(surface, theme, draw_cards)

    def reset(self):
        """Сбрасывает экран."""
        self.result = None
        self.finished = False
        self.theme_changed = False
        self._alpha = 0
        self._target_alpha = 255
        self._initialized = False

    def resize(self, width, height):
        """Обновляет размеры."""
        self.sw = width
        self.sh = height
        self._initialized = False
