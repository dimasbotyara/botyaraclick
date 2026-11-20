"""
botyaraclick - screens/upgrade_tree.py
Полноэкранное дерево улучшений.

Показывает все 176 улучшений, организованные по категориям и веткам.
Поддерживает скролл, покупку, тултипы, визуальные связи между улучшениями.
"""

import pygame
import math

from ui.button import Button
from ui import style
from ui.panel import Panel
from ui.scrollbar import ScrollArea
from ui.tooltip import TooltipManager
from ui.notification import NotificationManager
from economy import Economy, format_money, format_number
from data.upgrades import (
    ALL_UPGRADES, CATEGORY_ORDER, CATEGORIES,
    get_upgrades_by_category, get_upgrades_by_branch
)
from data.eras import ERAS
from locales.locale_manager import t
from ui.fonts import get_font


class UpgradeTreeScreen:
    """Полноэкранное дерево улучшений."""

    def __init__(self, screen_width, screen_height,
                 save_manager, sound_manager, economy):
        self.sw = screen_width
        self.sh = screen_height
        self.save = save_manager
        self.sound = sound_manager
        self.economy = economy

        # Результат
        self.result = None  # "back"
        self.finished = False

        # Текущая категория
        self._selected_category = CATEGORY_ORDER[0]

        # Шрифты
        self._fonts = {}

        # UI
        self._cat_buttons = []
        self._back_button = None
        self._scroll = None
        self._tooltip = TooltipManager(delay=0.3)

        # Анимация
        self._alpha = 0
        self._target_alpha = 255

        # Размеры ноды
        self.NODE_W = 200
        self.NODE_H = 82
        self.NODE_GAP_X = 14
        self.NODE_GAP_Y = 20
        self.BRANCH_GAP = 30

        self._num_format = save_manager.get_setting("number_format", "short")
        self._initialized = False

    def init_fonts(self, fonts_dict=None):
        """Инициализирует шрифты."""
        if fonts_dict:
            self._fonts = fonts_dict
        else:
            self._fonts = {
                "title": get_font(36, bold=True),
                "button": get_font(22),
                "normal": get_font(18),
                "small": get_font(15),
                "tiny": get_font(13),
            }
        self._tooltip.font = self._fonts.get("small")

    def _init_ui(self):
        """Создаёт UI элементы."""
        if self._initialized:
            return

        if not self._fonts:
            self.init_fonts()

        self._recalc_node_size()

        # === Кнопки категорий (вверху) ===
        self._cat_buttons.clear()
        cat_btn_w = min(170, (self.sw - 20) // len(CATEGORY_ORDER) - 5)
        cat_btn_h = 40
        total_cats_w = len(CATEGORY_ORDER) * (cat_btn_w + 5) - 5
        start_x = (self.sw - total_cats_w) // 2

        for i, cat_id in enumerate(CATEGORY_ORDER):
            cat_name = t(f"categories.{cat_id}")
            is_selected = cat_id == self._selected_category

            btn = Button(
                start_x + i * (cat_btn_w + 5),
                60,
                cat_btn_w, cat_btn_h,
                text=style.fit_text(
                    cat_name, self._fonts.get("button"), cat_btn_w - 18
                ),
                font=self._fonts.get("button"),
                color=(60, 100, 170) if is_selected else (50, 50, 70),
                hover_color=(75, 115, 185),
                border_radius=8,
                tag=cat_id,
            )
            self._cat_buttons.append(btn)

        # === Кнопка Назад ===
        self._back_button = Button(
            20, 12, 120, 38,
            text=t("upgrade_tree.back"),
            font=self._fonts.get("button"),
            color=(80, 80, 100),
            hover_color=(100, 100, 125),
            border_radius=8,
            tag="back",
        )

        # === Скролл ===
        tree_top = 110
        tree_height = self.sh - tree_top - 10
        content_h = self._calc_content_height()

        self._scroll = ScrollArea(
            10, tree_top,
            self.sw - 20, tree_height,
            content_height=content_h,
            scroll_speed=40,
        )

        self._initialized = True

    @staticmethod
    def _wrap_text(text, font, max_width, max_lines=2):
        """Разбивает текст на строки по ширине (с многоточием)."""
        if not font or not text:
            return [text or ""]

        words = text.split()
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if not current or font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
            if len(lines) >= max_lines:
                break
        if current and len(lines) < max_lines:
            lines.append(current)
        if not lines:
            return [text]

        joined = " ".join(lines)
        if joined != text.strip():
            lines = lines[:max_lines]
        return [style.fit_text(line, font, max_width) for line in lines]

    def _recalc_node_size(self):
        """Подбирает ширину карточки, чтобы все ноды влезали в ряд."""
        cat_data = CATEGORIES.get(self._selected_category, {})
        max_nodes = 1
        for branch_id in cat_data.get("branches", []):
            count = len(
                get_upgrades_by_branch(self._selected_category, branch_id)
            )
            max_nodes = max(max_nodes, count)

        avail = max(300, self.sw - 60)
        width = (avail - (max_nodes - 1) * self.NODE_GAP_X) // max_nodes
        self.NODE_W = max(104, min(200, width))

    def _calc_content_height(self):
        """Рассчитывает высоту содержимого для текущей категории."""
        cat_data = CATEGORIES.get(self._selected_category, {})
        branches = cat_data.get("branches", [])

        total_h = 20
        for branch_id in branches:
            items = get_upgrades_by_branch(self._selected_category, branch_id)
            # Ветка занимает: заголовок + ноды в линию
            branch_h = 35 + self.NODE_H + self.BRANCH_GAP
            total_h += branch_h

        return max(total_h + 50, self.sh - 120)

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

        # Категории
        for btn in self._cat_buttons:
            if btn.handle_event(event):
                self._selected_category = btn.tag
                # Обновляем цвета
                for cb in self._cat_buttons:
                    cb._color = (60, 100, 170) if cb.tag == self._selected_category else (50, 50, 70)
                # Пересчитываем скролл
                self._recalc_node_size()
                if self._scroll:
                    self._scroll.set_content_height(self._calc_content_height())
                    self._scroll.scroll_to_top()
                self.sound.play("click")
                return True

        # Скролл
        if self._scroll and self._scroll.handle_event(event):
            return True

        # Клик по ноде улучшения
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked_id = self._get_node_at(event.pos)
            if clicked_id:
                self._try_buy(clicked_id)
                return True

        return False

    def _get_node_at(self, pos):
        """Возвращает ID улучшения под курсором или None."""
        if not self._scroll:
            return None

        mx, my = pos
        scroll_y = int(self._scroll.scroll_y)
        tree_top = self._scroll.rect.top

        # Проверяем что клик в области скролла
        if not self._scroll.rect.collidepoint(pos):
            return None

        cat_data = CATEGORIES.get(self._selected_category, {})
        branches = cat_data.get("branches", [])

        current_y = tree_top + 20 - scroll_y

        for branch_id in branches:
            items = get_upgrades_by_branch(self._selected_category, branch_id)
            branch_title_h = 35

            # Ноды
            node_y = current_y + branch_title_h
            start_x = self._scroll.rect.x + 20

            for i, item in enumerate(items):
                node_x = start_x + i * (self.NODE_W + self.NODE_GAP_X)
                node_rect = pygame.Rect(node_x, node_y, self.NODE_W, self.NODE_H)

                if node_rect.collidepoint(mx, my):
                    return item["id"]

            current_y += branch_title_h + self.NODE_H + self.BRANCH_GAP

        return None

    def _try_buy(self, upgrade_id):
        """Пытается купить улучшение."""
        current_era = self.save.get_save_data("current_era", 0)
        can_buy, reason = self.economy.can_buy_upgrade(upgrade_id, current_era)

        if can_buy:
            success = self.economy.buy_upgrade(upgrade_id)
            if success:
                from core.achievement_tracker import AchievementTracker
                self.economy.recalculate()
                name = t(f"upgrades.{upgrade_id}")
                self.sound.play("buy")
        else:
            if reason == "no_money":
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

        # Скролл
        if self._scroll:
            self._scroll.update(dt)

        # Кнопки
        mouse_pos = pygame.mouse.get_pos()
        for btn in self._cat_buttons:
            btn.update(dt, mouse_pos)
        if self._back_button:
            self._back_button.update(dt, mouse_pos)

        # Тултипы
        hovered_id = self._get_node_at(mouse_pos)
        if hovered_id:
            tooltip_text = self._build_tooltip(hovered_id)
            self._tooltip.show(tooltip_text, mouse_pos)
        else:
            self._tooltip.hide()
        self._tooltip.update(dt)

        self._num_format = self.save.get_setting("number_format", "short")

    def _build_tooltip(self, upgrade_id):
        """Строит текст тултипа для улучшения."""
        up = ALL_UPGRADES.get(upgrade_id)
        if not up:
            return ""

        name = t(f"upgrades.{upgrade_id}")
        count = self.save.get_upgrade_count(upgrade_id)
        cost = self.economy.get_upgrade_cost(upgrade_id)

        effect_type = up["effect_type"]
        effect_value = up["effect_value"]

        if effect_type in ("click_multiplier", "passive_multiplier",
                          "all_multiplier", "discount", "crit_chance"):
            effect_str = t(f"effects.{effect_type}", value=f"{effect_value * 100:.0f}")
        elif effect_type == "crit_multiplier":
            effect_str = t(f"effects.{effect_type}", value=f"{effect_value:.0f}")
        else:
            effect_str = t(f"effects.{effect_type}",
                          value=format_number(effect_value, self._num_format))

        lines = [name]
        lines.append(effect_str)

        max_count = up.get("max_count", 1)
        if max_count == 1:
            if count > 0:
                lines.append(t("shop.max"))
            else:
                lines.append(f"{t('shop.cost', cost=format_number(cost, self._num_format))}")
        else:
            lines.append(f"{t('shop.owned', count=count)}")
            if max_count == -1 or count < max_count:
                lines.append(f"{t('shop.cost', cost=format_number(cost, self._num_format))}")
            else:
                lines.append(t("shop.max"))

        # Пререквизит
        prereq = up.get("prerequisite")
        if prereq and self.save.get_upgrade_count(prereq) <= 0:
            prereq_name = t(f"upgrades.{prereq}")
            lines.append(f"🔒 {t('shop.requires', name=prereq_name)}")

        # Эра
        era_req = up.get("era_required", 0)
        current_era = self.save.get_save_data("current_era", 0)
        if era_req > current_era:
            lines.append(f"🔒 {t('shop.era_locked', era=era_req + 1)}")

        return "\n".join(lines)

    def draw(self, surface, theme=None):
        """Рисует дерево улучшений."""
        self._init_ui()

        # Фон
        bg_color = (22, 22, 35)
        if theme:
            bg_color = theme.get("bg_color", bg_color)
        surface.fill(bg_color)

        text_color = (220, 220, 240)
        dim_color = (120, 120, 145)
        money_color = (80, 220, 120)
        locked_color = (80, 80, 100)
        bought_color = (50, 120, 70)
        available_color = (50, 80, 130)
        cant_afford_color = (90, 50, 50)
        border_bought = (80, 180, 100)
        border_available = (80, 130, 200)
        border_locked = (60, 60, 80)

        if theme:
            text_color = theme.get("text_color", text_color)
            dim_color = theme.get("text_dim", dim_color)
            money_color = theme.get("money_color", money_color)

        # Заголовок
        if self._fonts.get("title"):
            title_surf = self._fonts["title"].render(
                t("upgrade_tree.title"), True, text_color
            )
            title_rect = title_surf.get_rect(center=(self.sw // 2, 28))
            surface.blit(title_surf, title_rect)

        # Баланс в правом верхнем углу
        if self._fonts.get("normal"):
            money = self.save.get_save_data("money", 0)
            money_str = format_money(money, self._num_format)
            money_surf = self._fonts["normal"].render(money_str, True, money_color)
            money_rect = money_surf.get_rect(topright=(self.sw - 20, 15))
            surface.blit(money_surf, money_rect)

        # Категории
        for btn in self._cat_buttons:
            btn.draw(surface, theme)

        # Назад
        if self._back_button:
            self._back_button.draw(surface, theme)

        # Дерево
        if self._scroll:
            current_era = self.save.get_save_data("current_era", 0)

            def draw_tree(surf, scroll_y):
                cat_data = CATEGORIES.get(self._selected_category, {})
                branches = cat_data.get("branches", [])

                tree_top = self._scroll.rect.top
                current_y = tree_top + 20 - scroll_y

                font_normal = self._fonts.get("normal")
                font_small = self._fonts.get("small")
                font_tiny = self._fonts.get("tiny")
                font_button = self._fonts.get("button")

                for branch_id in branches:
                    items = get_upgrades_by_branch(self._selected_category, branch_id)

                    # Заголовок ветки
                    branch_name = t(f"branches.{branch_id}")
                    if font_button:
                        br_surf = font_button.render(branch_name, True, (140, 170, 220))
                        surf.blit(br_surf, (self._scroll.rect.x + 20, current_y))

                    node_y = current_y + 35
                    start_x = self._scroll.rect.x + 20

                    prev_node_right = 0

                    for i, item in enumerate(items):
                        upgrade_id = item["id"]
                        count = self.save.get_upgrade_count(upgrade_id)
                        cost = self.economy.get_upgrade_cost(upgrade_id)
                        can_buy, reason = self.economy.can_buy_upgrade(upgrade_id, current_era)
                        max_c = item.get("max_count", 1)
                        is_bought = (max_c == 1 and count >= 1) or (max_c != -1 and max_c != 1 and count >= max_c)
                        is_available = can_buy
                        is_visible = self.economy.is_upgrade_visible(upgrade_id, current_era)

                        node_x = start_x + i * (self.NODE_W + self.NODE_GAP_X)

                        # Пропускаем невидимые (за экраном)
                        if node_y + self.NODE_H < self._scroll.rect.top - 10:
                            prev_node_right = node_x + self.NODE_W
                            continue
                        if node_y > self._scroll.rect.bottom + 10:
                            break

                        # Линия связи с предыдущей нодой
                        if i > 0 and prev_node_right > 0:
                            line_y = node_y + self.NODE_H // 2
                            line_start = prev_node_right + 2
                            line_end = node_x - 2

                            prereq = item.get("prerequisite")
                            if prereq and self.save.get_upgrade_count(prereq) > 0:
                                line_col = (80, 150, 80)
                            else:
                                line_col = (50, 50, 65)

                            if line_end > line_start:
                                pygame.draw.line(surf, line_col,
                                               (line_start, line_y),
                                               (line_end, line_y), 2)
                                # Стрелочка
                                pygame.draw.polygon(surf, line_col, [
                                    (line_end, line_y),
                                    (line_end - 6, line_y - 4),
                                    (line_end - 6, line_y + 4),
                                ])

                        # Определяем цвета ноды
                        if is_bought:
                            node_bg = bought_color
                            node_border = border_bought
                            node_text_c = (200, 255, 200)
                        elif not is_visible:
                            node_bg = locked_color
                            node_border = border_locked
                            node_text_c = dim_color
                        elif is_available:
                            node_bg = available_color
                            node_border = border_available
                            node_text_c = text_color
                        elif reason == "no_money":
                            node_bg = cant_afford_color
                            node_border = (140, 70, 70)
                            node_text_c = (200, 150, 150)
                        else:
                            node_bg = locked_color
                            node_border = border_locked
                            node_text_c = dim_color

                        # Hover
                        mouse_pos = pygame.mouse.get_pos()
                        node_rect = pygame.Rect(
                            node_x, node_y, self.NODE_W, self.NODE_H
                        )
                        hovered = node_rect.collidepoint(mouse_pos)
                        if hovered:
                            node_bg = style.lighten(node_bg, 0.12)

                        # Карточка ноды
                        style.draw_panel(
                            surf, node_rect, node_bg, radius=9,
                            border_color=node_border, border_width=1,
                            alpha=235, gradient=0.16,
                            shadow=hovered, shadow_alpha=55
                        )
                        style.draw_soft_rect(
                            surf,
                            pygame.Rect(node_rect.x + 1, node_rect.y + 7,
                                        3, self.NODE_H - 14),
                            node_border, 210, radius=2
                        )

                        text_x = node_x + 11
                        max_text_w = self.NODE_W - 22

                        # Название: до двух строк
                        name = t(f"upgrades.{upgrade_id}")
                        reserve = 26 if (max_c != 1 and count > 0) else 0
                        if font_small:
                            lines = self._wrap_text(
                                name, font_small, max_text_w - reserve, 2
                            )
                            for li, line in enumerate(lines):
                                line_surf = font_small.render(
                                    line, True, node_text_c
                                )
                                surf.blit(line_surf, (text_x, node_y + 6 + li * 17))

                        # Эффект
                        if font_tiny:
                            effect_type = item["effect_type"]
                            effect_value = item["effect_value"]
                            if effect_type in ("click_multiplier", "passive_multiplier",
                                              "all_multiplier", "discount", "crit_chance"):
                                eff_str = f"+{effect_value * 100:.0f}%"
                            elif effect_type == "crit_multiplier":
                                eff_str = f"+{effect_value:.0f}x"
                            elif effect_type == "passive_income":
                                eff_str = f"+{format_number(effect_value, self._num_format)}/s"
                            else:
                                eff_str = f"+{format_number(effect_value, self._num_format)}/click"

                            eff_surf = font_tiny.render(eff_str, True, (138, 168, 208))
                            surf.blit(eff_surf, (text_x, node_y + 42))

                        # Цена / статус
                        if font_tiny:
                            if is_bought:
                                status_str = t("shop.max") if max_c == 1 else f"x{count}"
                                style.draw_check(
                                    surf, (text_x + 6, node_y + 67),
                                    size=10, color=(130, 225, 150)
                                )
                                status_surf = font_tiny.render(
                                    status_str, True, (130, 225, 150)
                                )
                            elif not is_visible:
                                status_str = "🔒"
                                status_surf = font_tiny.render(status_str, True, dim_color)
                            else:
                                cost_str = format_money(cost, self._num_format)
                                cost_c = money_color if is_available else (230, 120, 120)
                                status_surf = font_tiny.render(cost_str, True, cost_c)

                            blit_x = text_x + 16 if is_bought else text_x
                            surf.blit(status_surf, (blit_x, node_y + 60))

                        # Количество (для многоразовых)
                        if max_c != 1 and count > 0 and not is_bought and font_tiny:
                            cnt_str = f"x{count}"
                            cnt_surf = font_tiny.render(cnt_str, True, (190, 208, 236))
                            cnt_rect = cnt_surf.get_rect(
                                right=node_x + self.NODE_W - 9,
                                top=node_y + 7
                            )
                            style.draw_soft_rect(
                                surf,
                                pygame.Rect(cnt_rect.x - 5, cnt_rect.y - 2,
                                            cnt_rect.w + 10, cnt_rect.h + 4),
                                (255, 255, 255), 22, radius=6
                            )
                            surf.blit(cnt_surf, cnt_rect)

                        prev_node_right = node_x + self.NODE_W

                    current_y += 35 + self.NODE_H + self.BRANCH_GAP

            self._scroll.draw(surface, theme, draw_tree)

        # Тултипы
        self._tooltip.draw(surface, theme)

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
        self._initialized = False
