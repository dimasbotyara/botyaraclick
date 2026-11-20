"""
botyaraclick - screens/prestige_screen.py
Экран престижа.

Показывает:
- Текущие RP и сколько можно заработать
- Кнопку "Сделать престиж"
- Престиж-улучшения, которые можно купить за RP
"""

import pygame
import math

from ui.button import Button
from ui.scrollbar import ScrollArea
from ui.popup import PopupManager
from economy import format_money, format_number
from data.prestige import (
    calculate_rp, PRESTIGE_UPGRADES, ALL_PRESTIGE_UPGRADES,
    get_prestige_upgrade_cost
)
from config import PRESTIGE_THRESHOLD
from locales.locale_manager import t
from ui.fonts import get_font


class PrestigeScreen:
    """Экран престижа."""

    def __init__(self, screen_width, screen_height,
                 save_manager, sound_manager):
        self.sw = screen_width
        self.sh = screen_height
        self.save = save_manager
        self.sound = sound_manager

        # Результат
        self.result = None  # "back", "prestige_done"
        self.finished = False

        # Шрифты
        self._fonts = {}

        # UI
        self._back_button = None
        self._prestige_button = None
        self._scroll = None
        self._popup = PopupManager(screen_width, screen_height)

        # Анимация
        self._alpha = 0
        self._target_alpha = 255
        self._glow_phase = 0

        self._num_format = save_manager.get_setting("number_format", "short")
        self._initialized = False

    def init_fonts(self, fonts_dict=None):
        """Инициализирует шрифты."""
        if fonts_dict:
            self._fonts = fonts_dict
        else:
            self._fonts = {
                "title": get_font(42, bold=True),
                "large": get_font(30, bold=True),
                "button": get_font(24),
                "normal": get_font(20),
                "small": get_font(16),
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

        # Кнопка престижа
        total_earned = self.save.get_save_data("total_earned", 0)
        can_prestige = total_earned >= PRESTIGE_THRESHOLD
        rp_earn = calculate_rp(total_earned)

        self._prestige_button = Button(
            self.sw // 2 - 140,
            230, 280, 55,
            text=t("prestige.do_prestige"),
            font=self._fonts.get("button"),
            color=(180, 120, 30) if can_prestige else (70, 70, 90),
            hover_color=(220, 150, 40) if can_prestige else (70, 70, 90),
            text_color=(255, 240, 200) if can_prestige else (120, 120, 140),
            border_radius=12,
            border_width=2,
            border_color=(255, 200, 50) if can_prestige else (80, 80, 100),
            enabled=can_prestige,
            tag="prestige",
        )

        # Скролл для улучшений
        upgrades_top = 310
        upgrades_h = self.sh - upgrades_top - 20

        item_h = 75
        content_h = len(PRESTIGE_UPGRADES) * (item_h + 8) + 50

        self._scroll = ScrollArea(
            self.sw // 2 - 280, upgrades_top,
            560, upgrades_h,
            content_height=content_h,
            scroll_speed=35,
        )

        self._initialized = True

    def handle_event(self, event):
        """Обрабатывает события."""
        self._init_ui()

        # Попапы
        if self._popup.has_popup:
            self._popup.handle_event(event, self._fonts.get("button"))
            return True

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

        # Престиж
        if self._prestige_button and self._prestige_button.handle_event(event):
            self._popup.show_confirm(
                title=t("prestige.title"),
                message=t("prestige.confirm"),
                on_result=self._on_prestige_confirm,
                yes_text=t("common.yes"),
                no_text=t("common.no"),
            )
            self.sound.play("click")
            return True

        # Скролл
        if self._scroll and self._scroll.handle_event(event):
            return True

        # Клик по престиж-улучшениям
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked_id = self._get_upgrade_at(event.pos)
            if clicked_id:
                self._try_buy_prestige_upgrade(clicked_id)
                return True

        return False

    def _on_prestige_confirm(self, result):
        """Обработчик подтверждения престижа."""
        if result == "yes":
            total_earned = self.save.get_save_data("total_earned", 0)
            rp = calculate_rp(total_earned)

            if rp > 0:
                self.save.do_prestige(rp)
                self.sound.play("prestige")
                self.result = "prestige_done"
                self._target_alpha = 0

    def _get_upgrade_at(self, pos):
        """Возвращает ID престиж-улучшения под курсором."""
        if not self._scroll or not self._scroll.rect.collidepoint(pos):
            return None

        mx, my = pos
        scroll_y = int(self._scroll.scroll_y)
        items_top = self._scroll.rect.top

        item_h = 75
        gap = 8

        for i, up in enumerate(PRESTIGE_UPGRADES):
            item_y = items_top + 10 + i * (item_h + gap) - scroll_y

            if item_y + item_h < self._scroll.rect.top:
                continue
            if item_y > self._scroll.rect.bottom:
                break

            item_rect = pygame.Rect(
                self._scroll.rect.x + 10, item_y,
                self._scroll.rect.width - 30, item_h
            )

            if item_rect.collidepoint(mx, my):
                return up["id"]

        return None

    def _try_buy_prestige_upgrade(self, upgrade_id):
        """Пытается купить престиж-улучшение."""
        up_data = ALL_PRESTIGE_UPGRADES.get(upgrade_id)
        if not up_data:
            return

        count = self.save.get_prestige_upgrade_count(upgrade_id)
        max_count = up_data.get("max_count", -1)

        if max_count != -1 and count >= max_count:
            self.sound.play("error")
            return

        cost = get_prestige_upgrade_cost(up_data, count)
        available_rp = self.save.get_save_data("available_rp", 0)

        if available_rp >= cost:
            self.save.update_save_data("available_rp", available_rp - cost)
            self.save.set_prestige_upgrade_count(upgrade_id, count + 1)
            self.save.save_current()
            self.sound.play("buy")
        else:
            self.sound.play("error")

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

        # Анимация
        self._glow_phase += dt * 3

        # Скролл
        if self._scroll:
            self._scroll.update(dt)

        # Попапы
        self._popup.update(dt, pygame.mouse.get_pos())

        # Кнопки
        mouse_pos = pygame.mouse.get_pos()
        if self._back_button:
            self._back_button.update(dt, mouse_pos)
        if self._prestige_button:
            # Обновляем доступность
            total_earned = self.save.get_save_data("total_earned", 0)
            can = total_earned >= PRESTIGE_THRESHOLD
            self._prestige_button.enabled = can
            self._prestige_button.update(dt, mouse_pos)

        self._num_format = self.save.get_setting("number_format", "short")

    def draw(self, surface, theme=None):
        """Рисует экран престижа."""
        self._init_ui()

        # Фон
        bg = (15, 12, 25)
        if theme:
            bg = theme.get("bg_color", bg)
        surface.fill(bg)

        text_color = (220, 220, 240)
        dim_color = (120, 130, 150)
        money_color = (80, 220, 120)
        gold_color = (255, 200, 50)
        rp_color = (220, 180, 60)

        if theme:
            text_color = theme.get("text_color", text_color)
            dim_color = theme.get("text_dim", dim_color)

        font_title = self._fonts.get("title")
        font_large = self._fonts.get("large")
        font_normal = self._fonts.get("normal")
        font_small = self._fonts.get("small")
        font_button = self._fonts.get("button")

        # Заголовок
        if font_title:
            glow = int(20 * (math.sin(self._glow_phase) + 1) / 2)
            title_color = (220 + glow, 180 + glow, 50)
            title_surf = font_title.render(
                f"⭐ {t('prestige.title')} ⭐", True, title_color
            )
            title_rect = title_surf.get_rect(center=(self.sw // 2, 35))
            surface.blit(title_surf, title_rect)

        # Информация
        total_earned = self.save.get_save_data("total_earned", 0)
        current_rp = self.save.get_save_data("available_rp", 0)
        total_rp = self.save.get_save_data("total_rp", 0)
        prestige_count = self.save.get_save_data("prestige_count", 0)
        rp_earn = calculate_rp(total_earned)
        can_prestige = total_earned >= PRESTIGE_THRESHOLD

        info_y = 70

        # Текущие RP
        if font_large:
            rp_str = t("prestige.current_rp", rp=current_rp)
            rp_surf = font_large.render(rp_str, True, rp_color)
            rp_rect = rp_surf.get_rect(center=(self.sw // 2, info_y))
            surface.blit(rp_surf, rp_rect)
            info_y += 35

        # Сколько заработаем
        if font_normal:
            if can_prestige:
                earn_str = t("prestige.earn_rp", rp=rp_earn)
                earn_color = gold_color
            else:
                threshold_str = format_money(PRESTIGE_THRESHOLD, self._num_format)
                earn_str = t("prestige.threshold", amount=threshold_str)
                earn_color = dim_color

            earn_surf = font_normal.render(earn_str, True, earn_color)
            earn_rect = earn_surf.get_rect(center=(self.sw // 2, info_y))
            surface.blit(earn_surf, earn_rect)
            info_y += 28

        # Всего заработано / количество престижей
        if font_small:
            total_str = f"Total earned: {format_money(total_earned, self._num_format)} | Prestige #{prestige_count} | Total RP earned: {total_rp}"
            total_surf = font_small.render(total_str, True, dim_color)
            total_rect = total_surf.get_rect(center=(self.sw // 2, info_y))
            surface.blit(total_surf, total_rect)
            info_y += 25

        # Прогресс до престижа
        if not can_prestige and font_small:
            progress = min(1.0, total_earned / PRESTIGE_THRESHOLD)
            bar_w = 400
            bar_h = 12
            bar_x = self.sw // 2 - bar_w // 2
            bar_y = info_y + 5

            pygame.draw.rect(surface, (40, 40, 55),
                            (bar_x, bar_y, bar_w, bar_h), border_radius=6)
            if progress > 0:
                fill_w = int(bar_w * progress)
                pygame.draw.rect(surface, rp_color,
                                (bar_x, bar_y, fill_w, bar_h), border_radius=6)

            pct_str = f"{progress * 100:.1f}%"
            pct_surf = font_small.render(pct_str, True, text_color)
            pct_rect = pct_surf.get_rect(center=(self.sw // 2, bar_y + bar_h + 12))
            surface.blit(pct_surf, pct_rect)

        # Назад
        if self._back_button:
            self._back_button.draw(surface, theme)

        # Кнопка престижа
        if self._prestige_button:
            self._prestige_button.draw(surface, theme)

        # Заголовок улучшений
        if font_button:
            upgrades_title = font_button.render(
                t("prestige.upgrades"), True, rp_color
            )
            upgrades_rect = upgrades_title.get_rect(
                center=(self.sw // 2, 300)
            )
            surface.blit(upgrades_title, upgrades_rect)

        # Престиж-улучшения
        if self._scroll:
            available_rp_now = self.save.get_save_data("available_rp", 0)

            def draw_upgrades(surf, scroll_y):
                items_top = self._scroll.rect.top
                item_h = 75
                gap = 8
                item_w = self._scroll.rect.width - 30

                for i, up in enumerate(PRESTIGE_UPGRADES):
                    item_y = items_top + 10 + i * (item_h + gap) - scroll_y

                    if item_y + item_h < self._scroll.rect.top - 5:
                        continue
                    if item_y > self._scroll.rect.bottom + 5:
                        break

                    up_id = up["id"]
                    count = self.save.get_prestige_upgrade_count(up_id)
                    max_c = up.get("max_count", -1)
                    is_maxed = max_c != -1 and count >= max_c
                    cost = get_prestige_upgrade_cost(up, count) if not is_maxed else 0
                    can_afford = available_rp_now >= cost and not is_maxed

                    item_x = self._scroll.rect.x + 10

                    # Фон
                    if is_maxed:
                        bg_c = (35, 50, 35)
                        border_c = (80, 150, 80)
                    elif can_afford:
                        bg_c = (40, 45, 60)
                        border_c = (100, 130, 180)
                    else:
                        bg_c = (35, 35, 48)
                        border_c = (60, 60, 78)

                    # Hover
                    mouse_pos = pygame.mouse.get_pos()
                    item_rect = pygame.Rect(item_x, item_y, item_w, item_h)
                    if item_rect.collidepoint(mouse_pos) and not is_maxed:
                        bg_c = tuple(min(c + 12, 255) for c in bg_c)

                    item_surf = pygame.Surface((item_w, item_h), pygame.SRCALPHA)
                    pygame.draw.rect(item_surf, (*bg_c, 220),
                                    (0, 0, item_w, item_h), border_radius=8)
                    pygame.draw.rect(item_surf, (*border_c, 180),
                                    (0, 0, item_w, item_h), width=1, border_radius=8)
                    surf.blit(item_surf, (item_x, item_y))

                    # Название
                    name = t(f"prestige.{up_id}")
                    if font_normal:
                        name_surf = font_normal.render(name, True, text_color)
                        surf.blit(name_surf, (item_x + 12, item_y + 8))

                    # Описание эффекта
                    if font_small:
                        effect_type = up["effect_type"]
                        effect_value = up["effect_value"]
                        if effect_type in ("all_multiplier", "click_multiplier",
                                          "passive_multiplier"):
                            eff_str = f"+{effect_value * 100:.0f}% per level"
                        elif effect_type == "discount":
                            eff_str = f"-{effect_value * 100:.0f}% per level"
                        elif effect_type == "crit_chance":
                            eff_str = f"+{effect_value * 100:.0f}% per level"
                        elif effect_type == "crit_multiplier":
                            eff_str = f"+{effect_value:.0f}x per level"
                        elif effect_type == "auto_click":
                            eff_str = f"+{effect_value:.0f}/sec per level"
                        elif effect_type == "starting_money":
                            eff_str = f"+${format_number(effect_value, self._num_format)} per level"
                        elif effect_type == "golden_time_bonus":
                            eff_str = f"+{effect_value}s per level"
                        elif effect_type == "event_luck":
                            eff_str = f"+{effect_value * 100:.0f}% per level"
                        else:
                            eff_str = f"+{effect_value} per level"

                        eff_surf = font_small.render(eff_str, True, (130, 160, 200))
                        surf.blit(eff_surf, (item_x + 12, item_y + 30))

                    # Стоимость / статус
                    if font_small:
                        if is_maxed:
                            status_str = f"MAX (Lv.{count})"
                            status_c = (100, 200, 120)
                        else:
                            status_str = f"Cost: {cost} RP  |  Lv.{count}"
                            if max_c != -1:
                                status_str += f"/{max_c}"
                            status_c = rp_color if can_afford else (180, 100, 100)

                        status_surf = font_small.render(status_str, True, status_c)
                        surf.blit(status_surf, (item_x + 12, item_y + 50))

            self._scroll.draw(surface, theme, draw_upgrades)

        # Попапы
        self._popup.draw(surface, theme, self._fonts.get("button"), self._fonts.get("title"))

    def reset(self):
        """Сбрасывает экран."""
        self.result = None
        self.finished = False
        self._alpha = 0
        self._target_alpha = 255
        self._initialized = False

    def resize(self, width, height):
        """Обновляет размеры."""
        self.sw = width
        self.sh = height
        self._popup.resize(width, height)
        self._initialized = False
