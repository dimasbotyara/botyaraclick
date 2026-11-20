"""
botyaraclick - screens/game_screen.py
ОСНОВНОЙ ИГРОВОЙ ЭКРАН.

Layout:
┌──────────────────────────────────────────────────────┐
│  💰 Balance    📊 $/sec    🖱️ $/click    Era   [⏸]  │  ← Top panel
├───────────────────────────────────┬──────────────────┤
│                                   │                  │
│         CLICK ZONE                │    SHOP PANEL    │
│    (button, particles,            │   (quick buy)    │
│     floating text, events)        │                  │
│                                   │                  │
├───────────────────────────────────┴──────────────────┤
│ [Tree] [Achievements] [Themes] [Statistics] [Prestige]│ ← Bottom panel
└──────────────────────────────────────────────────────┘
"""

import pygame
import math
import time
import random

from config import (
    TOP_PANEL_HEIGHT, BOTTOM_PANEL_HEIGHT, SIDE_PANEL_WIDTH,
    FPS, AUTOSAVE_INTERVAL, HOTKEY_PAUSE, HOTKEY_CLICK,
    HOTKEY_SAVE, HOTKEY_FULLSCREEN
)
from ui.button import Button
from ui.panel import Panel
from ui.scrollbar import ScrollArea
from ui.tooltip import TooltipManager
from ui.notification import NotificationManager
from ui.fonts import load_theme_fonts, get_font
from ui import style
from effects.particles import ParticleSystem
from effects.floating_text import FloatingTextManager
from effects.animations import AnimationManager
from effects.bg_effects import BackgroundEffectManager
from economy import Economy, format_money, format_number, format_percent
from core.event_system import EventSystem
from core.achievement_tracker import AchievementTracker
from data.upgrades import (
    ALL_UPGRADES, CATEGORY_ORDER, CATEGORIES,
    get_upgrades_by_branch
)
from data.eras import get_era_for_money, get_era_data, ERAS
from data.themes import get_theme
from locales.locale_manager import t


def fit_text(text, font, max_width, ellipsis="…"):
    """Обрезает текст по фактической ширине в пикселях (а не по буквам)."""
    if not font or not text:
        return text
    if font.size(text)[0] <= max_width:
        return text

    result = text
    while result and font.size(result + ellipsis)[0] > max_width:
        result = result[:-1]
    result = result.rstrip()
    return (result + ellipsis) if result else ellipsis


class GameScreen:
    """Основной игровой экран."""

    # Иконки эр и категорий магазина
    ERA_ICONS = ["📟", "💻", "🚀", "🏢", "👑", "🌌", "🪐"]
    CATEGORY_ICONS = {
        "equipment": "🖥",
        "staff": "👥",
        "infrastructure": "🏗",
        "products": "📦",
        "skills": "🎯",
        "empire": "🏛",
    }

    # Высоты зон магазина
    SHOP_PAD = 6
    CAT_BTN_H = 32
    CAT_AREA_H = 74
    BRANCH_BTN_H = 28
    BRANCH_AREA_H = 38

    def __init__(self, screen_width, screen_height,
                 save_manager, sound_manager, locale_manager):
        self.sw = screen_width
        self.sh = screen_height
        self.save = save_manager
        self.sound = sound_manager
        self.locale = locale_manager

        # Результат
        self.result = None  # "pause", "quit"
        self.wants_pause = False
        self.wants_quit = False

        # Системы
        self.economy = Economy(save_manager)
        self.event_system = EventSystem()
        self.achievement_tracker = AchievementTracker(save_manager)
        self.particles = ParticleSystem(
            enabled=save_manager.get_setting("particles_enabled", True)
        )
        self.floating_text = FloatingTextManager(
            enabled=save_manager.get_setting("floating_text_enabled", True)
        )
        self.animations = AnimationManager()
        self.bg_effects = BackgroundEffectManager(screen_width, screen_height,
            enabled=save_manager.get_setting("particles_enabled", True)
        )
        self.tooltip = TooltipManager(delay=0.4)
        self.notifications = NotificationManager(screen_width, screen_height)

        # Шрифты
        self._fonts = {}
        self._fonts_loaded = False

        # UI элементы
        self._click_button_rect = None
        self._click_button_radius = 0
        self._click_hover_scale = 1.0
        self._is_click_hovered = False
        self._pause_button = None
        self._bottom_buttons = {}
        self._shop_scroll = None
        self._shop_items = []

        # Текущая категория/ветка в магазине
        self._shop_category = "staff"
        self._shop_branch = "developers"
        self._shop_cat_buttons = []
        self._shop_branch_buttons = []

        # Состояние
        self._current_era = 0
        self._previous_era = 0
        self._autosave_timer = 0
        self._play_time_timer = 0
        self._passive_tick_accum = 0
        self._auto_click_accum = 0
        self._initialized = False

        # Число формат
        self._num_format = save_manager.get_setting("number_format", "short")

        # Текущая тема
        self._theme_data = None
        self._load_theme()

    def _load_theme(self):
        """Загружает текущую тему."""
        theme_id = self.save.get_save_data("current_theme", "default")
        self._theme_data = get_theme(theme_id)

        # Устанавливаем фоновый эффект
        bg_effect = self._theme_data.get("bg_effect", "none")
        self.bg_effects.set_effect(bg_effect, self._theme_data)

    def init_fonts(self, fonts_dict=None):
        """Инициализирует шрифты."""
        if fonts_dict:
            self._fonts = fonts_dict
        else:
            self._fonts = load_theme_fonts()

        self.tooltip.font = self._fonts.get("small")
        # Уведомления — компактные, снизу экрана
        self.notifications.font = self._fonts.get("small")
        self.notifications.small_font = self._fonts.get("small")

        font_path = None
        if "normal" in self._fonts:
            try:
                font_path = self._fonts["normal"].path if hasattr(self._fonts["normal"], 'path') else None
            except AttributeError:
                pass
        self.floating_text.set_font(font_path)

        self._fonts_loaded = True

    def _init_ui(self):
        """Создаёт UI элементы."""
        if self._initialized and self._fonts_loaded:
            return

        if not self._fonts_loaded:
            self.init_fonts()

        # Размеры зон
        top_h = TOP_PANEL_HEIGHT
        bot_h = BOTTOM_PANEL_HEIGHT
        shop_w = SIDE_PANEL_WIDTH
        click_zone_w = self.sw - shop_w
        click_zone_h = self.sh - top_h - bot_h

        # === Кнопка клика (круглая, по центру зоны) ===
        click_cx = click_zone_w // 2
        click_cy = top_h + click_zone_h // 2
        self._click_button_radius = min(click_zone_w, click_zone_h) // 4
        self._click_button_rect = pygame.Rect(
            click_cx - self._click_button_radius,
            click_cy - self._click_button_radius,
            self._click_button_radius * 2,
            self._click_button_radius * 2,
        )
        self._click_center = (click_cx, click_cy)

        # === Кнопка паузы ===
        self._pause_button = Button(
            self.sw - 55, 10, 45, 40,
            text="⏸",
            font=self._fonts.get("button"),
            color=(60, 60, 80),
            hover_color=(80, 80, 105),
            border_radius=8,
            tag="pause",
        )

        # === Нижние кнопки ===
        bottom_btns = [
            ("tree", "🌳", t("upgrade_tree.title")),
            ("achievements", "🏆", t("achievements.title")),
            ("themes", "🎨", t("themes.title")),
            ("statistics", "📊", t("statistics.title")),
            ("prestige", "⭐", t("prestige.title")),
        ]
        btn_count = len(bottom_btns)
        gap = 8
        btn_w = min(190, (self.sw - 24) // btn_count - gap)
        btn_h = BOTTOM_PANEL_HEIGHT - 12
        total_w = btn_count * btn_w + (btn_count - 1) * gap
        start_x = (self.sw - total_w) // 2
        btn_font = self._fonts.get("tiny")

        self._bottom_buttons.clear()
        for i, (bid, icon, btext) in enumerate(bottom_btns):
            btn = Button(
                start_x + i * (btn_w + gap),
                self.sh - BOTTOM_PANEL_HEIGHT + 6,
                btn_w, btn_h,
                text=fit_text(btext, btn_font, btn_w - 36),
                icon=icon,
                font=btn_font,
                color=(44, 48, 64),
                hover_color=(66, 74, 100),
                text_color=(206, 214, 232),
                border_radius=9,
                tooltip=btext,
                tag=bid,
            )
            self._bottom_buttons[bid] = btn

        # === Магазин (правая панель) ===
        shop_x = self.sw - shop_w
        shop_top = top_h
        shop_height = self.sh - top_h - bot_h

        self._shop_rect = pygame.Rect(shop_x, shop_top, shop_w, shop_height)

        # Категории магазина
        self._build_shop_categories()

        # Скролл для предметов магазина
        cat_area_h = self.CAT_AREA_H        # сетка категорий (2 ряда)
        branch_area_h = self.BRANCH_AREA_H  # «пилюли» веток
        items_top = shop_top + cat_area_h + branch_area_h
        items_height = shop_height - cat_area_h - branch_area_h - 8

        self._shop_scroll = ScrollArea(
            shop_x + 5, items_top,
            shop_w - 10, items_height,
            content_height=1000,
            scroll_speed=35,
        )

        # Начальный пересчёт экономики
        ach_bonuses = self.achievement_tracker.get_achievement_bonuses()
        self.economy.recalculate(ach_bonuses)

        # Начальная эра
        total_earned = self.save.get_save_data("total_earned", 0)
        self._current_era = get_era_for_money(total_earned)
        self._previous_era = self._current_era

        self._initialized = True

    def _build_shop_categories(self):
        """Строит сетку категорий магазина (2 ряда по 3)."""
        shop_x = self.sw - SIDE_PANEL_WIDTH
        shop_top = TOP_PANEL_HEIGHT
        font = self._fonts.get("tiny")

        self._shop_cat_buttons.clear()

        cols = 3
        pad = self.SHOP_PAD
        gap = 4
        btn_w = (SIDE_PANEL_WIDTH - pad * 2 - gap * (cols - 1)) // cols

        for i, cat_id in enumerate(CATEGORY_ORDER):
            row, col = divmod(i, cols)
            name = fit_text(t(f"categories.{cat_id}"), font, btn_w - 34)
            active = cat_id == self._shop_category

            btn = Button(
                shop_x + pad + col * (btn_w + gap),
                shop_top + pad + row * (self.CAT_BTN_H + gap),
                btn_w, self.CAT_BTN_H,
                text=name,
                icon=self.CATEGORY_ICONS.get(cat_id, ""),
                font=font,
                color=(56, 104, 176) if active else (40, 44, 60),
                hover_color=(72, 124, 200) if active else (54, 60, 82),
                text_color=(255, 255, 255) if active else (185, 192, 214),
                border_radius=8,
                tooltip=t(f"categories.{cat_id}"),
                tag=cat_id,
            )
            self._shop_cat_buttons.append(btn)

        self._build_shop_branches()

    def _build_shop_branches(self):
        """Строит «пилюли» веток текущей категории."""
        shop_x = self.sw - SIDE_PANEL_WIDTH
        shop_top = TOP_PANEL_HEIGHT + self.CAT_AREA_H
        font = self._fonts.get("tiny")

        self._shop_branch_buttons.clear()

        cat_data = CATEGORIES.get(self._shop_category, {})
        branches = cat_data.get("branches", [])
        if not branches:
            return

        pad = self.SHOP_PAD
        gap = 4
        br_btn_w = (SIDE_PANEL_WIDTH - pad * 2 - gap * (len(branches) - 1)) // len(branches)

        for i, br_id in enumerate(branches):
            active = br_id == self._shop_branch
            name = fit_text(t(f"branches.{br_id}"), font, br_btn_w - 10)

            btn = Button(
                shop_x + pad + i * (br_btn_w + gap),
                shop_top + 2,
                br_btn_w, self.BRANCH_BTN_H,
                text=name,
                font=font,
                color=(46, 74, 116) if active else (34, 37, 50),
                hover_color=(58, 92, 140) if active else (46, 51, 68),
                text_color=(235, 242, 255) if active else (150, 158, 180),
                border_radius=self.BRANCH_BTN_H // 2,
                border_width=1 if active else 0,
                border_color=(96, 150, 220) if active else None,
                tooltip=t(f"branches.{br_id}"),
                tag=br_id,
            )
            self._shop_branch_buttons.append(btn)

    def _get_shop_items(self):
        """Возвращает список улучшений для текущей ветки магазина."""
        items = get_upgrades_by_branch(self._shop_category, self._shop_branch)
        return items

    # ================================================================
    # ОБРАБОТКА СОБЫТИЙ
    # ================================================================

    def handle_event(self, event):
        """Обрабатывает все события."""
        self._init_ui()

        # Уведомления рисуются поверх игры — клик по ним просто закрывает их
        if self.notifications.handle_event(event):
            return True

        # Клавиатура
        if event.type == pygame.KEYDOWN:
            if event.key == HOTKEY_PAUSE:
                self.wants_pause = True
                return True
            elif event.key == HOTKEY_CLICK:
                self._do_click(self._click_center[0], self._click_center[1])
                return True
            elif event.key == HOTKEY_SAVE:
                self.save.save_current()
                self.sound.play("save")
                self.notifications.add(t("pause.save_success"), icon="💾", duration=2.0)
                return True
            elif event.key == HOTKEY_FULLSCREEN:
                return False  # Обрабатывается в main.py

        # Кнопка паузы
        if self._pause_button and self._pause_button.handle_event(event):
            self.wants_pause = True
            self.sound.play("pause")
            return True

        # Клик мыши
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Проверяем клик по золотым объектам
            event_results = self.event_system.handle_click(mx, my, self._get_game_state())
            if event_results:
                for res in event_results:
                    self._handle_event_result(res, mx, my)
                return True

            # Проверяем клик по кнопке клика
            if self._click_button_rect:
                dx = mx - self._click_center[0]
                dy = my - self._click_center[1]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= self._click_button_radius:
                    self._do_click(mx, my)
                    return True

        # Нижние кнопки
        for btn_id, btn in self._bottom_buttons.items():
            if btn.handle_event(event):
                self.result = btn_id
                self.sound.play("click")
                return True

        # Категории магазина
        for btn in self._shop_cat_buttons:
            if btn.handle_event(event):
                self._shop_category = btn.tag
                # Устанавливаем первую ветку
                cat_data = CATEGORIES.get(self._shop_category, {})
                branches = cat_data.get("branches", [])
                self._shop_branch = branches[0] if branches else ""
                self._build_shop_categories()
                if self._shop_scroll:
                    self._shop_scroll.scroll_to_top()
                self.sound.play("click")
                return True

        # Ветки магазина
        for btn in self._shop_branch_buttons:
            if btn.handle_event(event):
                self._shop_branch = btn.tag
                self._build_shop_branches()
                if self._shop_scroll:
                    self._shop_scroll.scroll_to_top()
                self.sound.play("click")
                return True

        # Скролл магазина
        if self._shop_scroll:
            if self._shop_scroll.handle_event(event):
                return True

        # Клик по предметам магазина
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._shop_rect and self._shop_rect.collidepoint(event.pos):
                self._handle_shop_click(event.pos)
                return True

        return False

    def _do_click(self, mx, my):
        """Выполняет клик."""
        # Получаем множитель от ивентов
        event_click_mult = self.event_system.get_click_multiplier()

        # Экономический клик
        earned, is_crit = self.economy.do_click(event_click_mult)

        # Анимация
        self.animations.trigger_click(0.15 if is_crit else 0.10)

        # Частицы
        particle_colors = self._theme_data.get("particle_colors", [(255, 255, 255)])
        if is_crit:
            self.particles.emit_crit(mx, my, particle_colors)
            self.sound.play("click_crit")
        else:
            self.particles.emit_click(mx, my, particle_colors, count=6)
            self.sound.play("click")

        # Всплывающий текст
        money_color = self._theme_data.get("money_color", (80, 220, 120))
        crit_color = self._theme_data.get("crit_color", (255, 200, 0))
        self.floating_text.add_click(
            mx + random.randint(-20, 20),
            my - 30 + random.randint(-10, 10),
            earned, is_crit,
            colors=[crit_color if is_crit else money_color]
        )

        # Трекинг достижений
        self.achievement_tracker.register_click()

        # Сбрасываем трекер "деньги без покупок"
        current_no_buy = self.save.get_save_data("money_earned_without_buying", 0)
        self.save.update_save_data("money_earned_without_buying", current_no_buy + earned)

        # Добавляем клики в challenge
        for ev in self.event_system.active_events:
            if ev.event_type == "challenge" and ev.alive:
                ev.add_challenge_click()

    def _handle_shop_click(self, pos):
        """Обрабатывает клик по предмету в магазине."""
        if not self._shop_scroll:
            return

        mx, my = pos
        scroll_y = int(self._shop_scroll.scroll_y)

        items = self._get_shop_items()
        item_h = 76
        items_top = self._shop_scroll.rect.top

        for i, item in enumerate(items):
            item_y = items_top + i * item_h - scroll_y

            if item_y > self._shop_scroll.rect.bottom or item_y + item_h < self._shop_scroll.rect.top:
                continue

            item_rect = pygame.Rect(
                self._shop_scroll.rect.x,
                item_y,
                self._shop_scroll.rect.width - 15,
                item_h - 3
            )

            if item_rect.collidepoint(mx, my):
                self._try_buy_upgrade(item["id"])
                return

    def _try_buy_upgrade(self, upgrade_id):
        """Пытается купить улучшение."""
        can_buy, reason = self.economy.can_buy_upgrade(
            upgrade_id, self._current_era
        )

        if can_buy:
            success = self.economy.buy_upgrade(upgrade_id)
            if success:
                # Пересчёт
                ach_bonuses = self.achievement_tracker.get_achievement_bonuses()
                self.economy.recalculate(ach_bonuses)

                name = t(f"upgrades.{upgrade_id}")
                self.notifications.add_purchase(name)
                self.sound.play("buy")

                # Частицы покупки
                shop_cx = self.sw - SIDE_PANEL_WIDTH // 2
                shop_cy = self.sh // 2
                self.particles.emit_purchase(shop_cx, shop_cy)

                # Сброс трекера "деньги без покупок"
                self.save.update_save_data("money_earned_without_buying", 0)
        else:
            if reason == "no_money":
                self.sound.play("error")
            elif reason == "era_locked":
                era_req = ALL_UPGRADES[upgrade_id].get("era_required", 0)
                self.notifications.add(
                    t("shop.era_locked", era=era_req + 1),
                    icon="🔒", duration=2.0, importance="warning"
                )
            elif reason == "prerequisite":
                prereq_id = ALL_UPGRADES[upgrade_id].get("prerequisite", "")
                prereq_name = t(f"upgrades.{prereq_id}")
                self.notifications.add(
                    t("shop.requires", name=prereq_name),
                    icon="🔒", duration=2.0, importance="warning"
                )

    def _handle_event_result(self, result, mx, my):
        """Обрабатывает результат ивента."""
        rtype = result.get("type")
        reward = result.get("reward", 0)

        if rtype == "golden_caught":
            money = self.save.get_save_data("money", 0)
            self.save.update_save_data("money", money + reward)
            total = self.save.get_save_data("total_earned", 0)
            self.save.update_save_data("total_earned", total + reward)
            self.save.increment_stat("golden_caught")

            self.floating_text.add_event_text(mx, my, f"+${format_number(reward, self._num_format)}", positive=True)
            self.particles.emit_confetti(mx, my, count=20)
            self.sound.play("golden_catch")
            self.notifications.add_event(
                t("events.event_caught", amount=format_number(reward, self._num_format)),
                icon="🌟", positive=True
            )

        elif rtype == "challenge_complete":
            money = self.save.get_save_data("money", 0)
            self.save.update_save_data("money", money + reward)
            total = self.save.get_save_data("total_earned", 0)
            self.save.update_save_data("total_earned", total + reward)
            self.save.increment_stat("challenges_completed")

            self.floating_text.add_event_text(mx, my, f"+${format_number(reward, self._num_format)}", positive=True)
            self.particles.emit_confetti(mx, my, count=25)
            self.sound.play("deal_won")
            self.notifications.add_event(
                t("events.challenge_success", amount=format_number(reward, self._num_format)),
                icon="🏆", positive=True
            )

    # ================================================================
    # ОБНОВЛЕНИЕ
    # ================================================================

    def update(self, dt):
        """Обновляет всё каждый кадр."""
        self._init_ui()

        mouse_pos = pygame.mouse.get_pos()

        # === Плавное наведение на кнопку клика ===
        if self._click_center and self._click_button_radius:
            dx = mouse_pos[0] - self._click_center[0]
            dy = mouse_pos[1] - self._click_center[1]
            dist = math.hypot(dx, dy)
            self._is_click_hovered = dist <= self._click_button_radius
            target_hover = 1.05 if self._is_click_hovered else 1.0
            self._click_hover_scale += (target_hover - self._click_hover_scale) * min(1.0, dt * 14.0)
        else:
            self._is_click_hovered = False

        # === Время игры ===
        play_time = self.save.get_save_data("play_time", 0)
        self.save.update_save_data("play_time", play_time + dt)

        # === Пассивный доход ===
        event_passive_mult = self.event_system.get_passive_multiplier()
        passive_earned = self.economy.do_passive_tick(dt, event_passive_mult)

        # === Автоклики ===
        event_click_mult = self.event_system.get_click_multiplier()
        auto_earned = self.economy.do_auto_click(dt, event_click_mult)

        # === Проверка эры ===
        total_earned = self.save.get_save_data("total_earned", 0)
        new_era = get_era_for_money(total_earned)
        if new_era != self._current_era:
            self._on_era_change(self._current_era, new_era)
            self._current_era = new_era

        # === Пересчёт экономики если нужно ===
        if self.economy.needs_recalc:
            ach_bonuses = self.achievement_tracker.get_achievement_bonuses()
            self.economy.recalculate(ach_bonuses)

        # === Ивенты ===
        game_state = self._get_game_state()
        self.event_system.update(dt, game_state)

        # Обработка новых баффов/дебаффов
        for ev in self.event_system.active_buffs:
            if ev.event_type == "debuff" and ev.result == "survived":
                self.save.increment_stat("debuffs_survived")

        # Обработка мгновенных ивентов
        for ev in self.event_system.active_events:
            if ev.event_type == "instant" and ev.alive:
                result = self.event_system.process_instant(ev, game_state)
                if result:
                    if result["type"] == "money_gained":
                        money = self.save.get_save_data("money", 0)
                        self.save.update_save_data("money", money + result["amount"])
                        self.notifications.add_event(
                            t(f"events.{ev.event_id}", value=format_number(result["amount"], self._num_format)),
                            icon=ev.icon, positive=True
                        )
                        self.sound.play("event_positive")
                    elif result["type"] == "money_lost":
                        money = self.save.get_save_data("money", 0)
                        loss = min(money, result["amount"])
                        self.save.update_save_data("money", money - loss)
                        self.notifications.add_event(
                            t(f"events.{ev.event_id}", value=format_percent(abs(ev.data.get("effect_value", 0)))),
                            icon=ev.icon, positive=False
                        )
                        self.sound.play("event_negative")
                ev.alive = False

            # Уведомления для баффов/дебаффов при появлении
            elif ev.event_type == "choice" and ev.alive and ev.result is None:
                # Показываем выбор — пока просто автоматически
                # TODO: в будущем показывать попап
                pass

        # Уведомления для новых баффов
        for buff in self.event_system.active_buffs:
            if buff.progress < 0.02:  # только что появился
                if buff.event_type == "buff":
                    self.sound.play("event_positive")
                    self.notifications.add_event(
                        t(f"events.{buff.event_id}",
                          value=buff.data.get("effect_value", 1),
                          duration=int(buff.data.get("duration", 15))),
                        icon=buff.icon, positive=True
                    )
                elif buff.event_type == "debuff":
                    self.sound.play("event_negative")
                    self.animations.trigger_shake(5, 0.3)
                    self.notifications.add_event(
                        t(f"events.{buff.event_id}",
                          value=buff.data.get("effect_value", 1),
                          duration=int(buff.data.get("duration", 15))),
                        icon=buff.icon, positive=False
                    )

        # === Достижения ===
        self.achievement_tracker.check_all(game_state)
        for ach in self.achievement_tracker.newly_unlocked:
            ach_name = t(f"achievements.{ach['id']}")
            ach_desc = t(f"achievement_desc.{ach['id']}")
            self.notifications.add_achievement(ach_name, ach_desc)
            self.sound.play("achievement")
            # Пересчёт экономики (бонусы достижений)
            ach_bonuses = self.achievement_tracker.get_achievement_bonuses()
            self.economy.recalculate(ach_bonuses)

        # === Автосохранение ===
        self._autosave_timer += dt
        if self._autosave_timer >= AUTOSAVE_INTERVAL:
            self.save.save_current()
            self._autosave_timer = 0

        # === Обновление UI и эффектов ===
        self.animations.update(dt)
        self.particles.update(dt)
        self.floating_text.update(dt)
        self.bg_effects.update(dt)
        self.tooltip.update(dt)
        self.notifications.update(dt)

        # Кнопки
        if self._pause_button:
            self._pause_button.update(dt, mouse_pos)
        for btn in self._bottom_buttons.values():
            btn.update(dt, mouse_pos)
        for btn in self._shop_cat_buttons:
            btn.update(dt, mouse_pos)
        for btn in self._shop_branch_buttons:
            btn.update(dt, mouse_pos)

        if self._shop_scroll:
            self._shop_scroll.update(dt)

        # Обновляем настройки эффектов
        self.particles.enabled = self.save.get_setting("particles_enabled", True)
        self.floating_text.enabled = self.save.get_setting("floating_text_enabled", True)
        self.bg_effects.enabled = self.save.get_setting("particles_enabled", True)
        self._num_format = self.save.get_setting("number_format", "short")

    def _on_era_change(self, old_era, new_era):
        """Обрабатывает смену эры."""
        old_data = get_era_data(old_era)
        new_data = get_era_data(new_era)

        self.animations.trigger_era_transition(
            old_data.get("bg_colors", {}),
            new_data.get("bg_colors", {}),
            duration=3.0
        )

        self.sound.play("era_up")
        self.save.update_save_data("current_era", new_era)

        era_name = t(f"eras.{new_data['id']}")
        self.notifications.add(
            era_name, icon="🏢",
            duration=4.0, importance="achievement",
            sub_text=t("game.era")
        )

        # Конфетти!
        cx = self.sw // 2
        cy = self.sh // 2
        self.particles.emit_confetti(cx, cy, count=50)

    def _get_game_state(self):
        """Собирает текущее состояние игры для систем."""
        return {
            "screen_width": self.sw,
            "screen_height": self.sh,
            "current_era": self._current_era,
            "money": self.save.get_save_data("money", 0),
            "total_earned": self.save.get_save_data("total_earned", 0),
            "total_clicks": self.save.get_save_data("total_clicks", 0),
            "total_purchases": self.save.get_save_data("total_purchases", 0),
            "play_time": self.save.get_save_data("play_time", 0),
            "passive_income": self.economy.passive_income,
            "click_power": self.economy.click_power,
            "golden_caught": self.save.get_save_data("golden_caught", 0),
            "golden_missed": self.save.get_save_data("golden_missed", 0),
            "deals_won": self.save.get_save_data("deals_won", 0),
            "deals_lost": self.save.get_save_data("deals_lost", 0),
            "challenges_completed": self.save.get_save_data("challenges_completed", 0),
            "debuffs_survived": self.save.get_save_data("debuffs_survived", 0),
            "prestige_count": self.save.get_save_data("prestige_count", 0),
            "money_earned_without_buying": self.save.get_save_data("money_earned_without_buying", 0),
            "deals_lost_in_row": self.save.get_save_data("deals_lost_in_row", 0),
            "themes_owned": len(self.save.get_unlocked_themes()),
            "event_luck": self._get_prestige_bonus("event_luck"),
            "golden_time_bonus": self._get_prestige_bonus("golden_time_bonus"),
        }

    def _get_prestige_bonus(self, bonus_type):
        """Получает бонус от престиж-улучшений."""
        from data.prestige import ALL_PRESTIGE_UPGRADES
        total = 0
        for up_id, up_data in ALL_PRESTIGE_UPGRADES.items():
            if up_data["effect_type"] == bonus_type:
                count = self.save.get_prestige_upgrade_count(up_id)
                total += up_data["effect_value"] * count
        return total

    # ================================================================
    # ОТРИСОВКА
    # ================================================================

    def draw(self, surface):
        """Рисует весь игровой экран."""
        self._init_ui()

        theme = self._theme_data

        # Смещение от тряски
        shake_x, shake_y = self.animations.shake_offset
        offset = (int(shake_x), int(shake_y))

        # === Фон ===
        self._draw_background(surface, theme, offset)

        # === Фоновый эффект ===
        self.bg_effects.draw(surface)

        # === Верхняя панель ===
        self._draw_top_panel(surface, theme, offset)

        # === Кнопка клика ===
        self._draw_click_button(surface, theme, offset)

        # === Золотые объекты ===
        self._draw_golden_objects(surface, theme)

        # === Баффы/дебаффы индикаторы ===
        self._draw_buff_indicators(surface, theme)

        # === Частицы ===
        self.particles.draw(surface)

        # === Всплывающий текст ===
        self.floating_text.draw(surface)

        # === Правая панель (магазин) ===
        self._draw_shop_panel(surface, theme, offset)

        # === Нижняя панель ===
        self._draw_bottom_panel(surface, theme, offset)

        # === Переход эры ===
        if self.animations.era_transition:
            era_data = get_era_data(self._current_era)
            era_name = t(f"eras.{era_data['id']}")
            self.animations.era_transition.draw(
                surface, era_name,
                self._fonts.get("normal"),
                self._fonts.get("title")
            )

        # === Уведомления ===
        self.notifications.draw(surface, theme)

        # === Тултипы ===
        self.tooltip.draw(surface, theme)

    def _draw_background(self, surface, theme, offset):
        """Рисует фон с градиентом."""
        era_data = get_era_data(self._current_era)

        if self.animations.era_transition:
            top, bottom = self.animations.era_transition.bg_colors
        else:
            top = era_data.get("bg_colors", {}).get("top", (30, 30, 45))
            bottom = era_data.get("bg_colors", {}).get("bottom", (20, 20, 30))

        for y in range(self.sh):
            t_val = y / max(self.sh - 1, 1)
            r = int(top[0] + (bottom[0] - top[0]) * t_val)
            g = int(top[1] + (bottom[1] - top[1]) * t_val)
            b = int(top[2] + (bottom[2] - top[2]) * t_val)
            pygame.draw.line(surface, (r, g, b),
                             (0 + offset[0], y + offset[1]),
                             (self.sw + offset[0], y + offset[1]))

    def _draw_top_panel(self, surface, theme, offset):
        """Рисует верхнюю информационную панель."""
        panel_color = theme.get("panel_color", (40, 40, 55))
        text_color = theme.get("text_color", (230, 230, 240))
        money_color = theme.get("money_color", (80, 220, 120))
        accent = theme.get("accent_color", (50, 150, 255))
        dim_color = theme.get("text_dim", (150, 150, 170))
        border_color = theme.get("panel_border", (60, 60, 80))

        bar = pygame.Rect(offset[0], offset[1], self.sw, TOP_PANEL_HEIGHT)
        style.draw_panel(
            surface, bar, panel_color, radius=0,
            border_color=None, gradient=0.18
        )

        big_font = self._fonts.get("money_big")
        font = self._fonts.get("normal")
        small = self._fonts.get("small")
        tiny = self._fonts.get("tiny")
        if not (font and big_font):
            return

        money = self.save.get_save_data("money", 0)
        per_click = self.economy.click_power
        per_sec = self.economy.passive_income

        center_y = offset[1] + TOP_PANEL_HEIGHT // 2

        # --- Баланс ---
        x = 20 + offset[0]
        if small:
            coin = small.render("💰", True, (255, 206, 84))
            surface.blit(
                coin, (x, center_y - coin.get_height() // 2 + 1)
            )
            x += coin.get_width() + 9

        money_surf = big_font.render(
            format_money(money, self._num_format), True, money_color
        )
        surface.blit(money_surf, (x, center_y - money_surf.get_height() // 2))
        x += money_surf.get_width() + 18

        era_data = get_era_data(self._current_era)
        era_icon = self.ERA_ICONS[min(self._current_era, len(self.ERA_ICONS) - 1)]
        era_name = t(f"eras.{era_data['id']}")
        era_color = era_data.get("click_object_color", accent)

        blocks = [
            (t("game.per_click").upper(),
             format_money(per_click, self._num_format), accent),
            (t("game.per_second").upper(),
             format_money(per_sec, self._num_format), money_color),
            (t("game.era").upper(), f"{era_icon} {era_name}", era_color),
        ]

        # Не залезаем на кнопку паузы и панель магазина
        max_x = self.sw - SIDE_PANEL_WIDTH - 10

        for idx, (label, value, color) in enumerate(blocks):
            label_surf = tiny.render(label, True, dim_color) if tiny else None
            value_surf = small.render(value, True, color) if small else None
            if not (label_surf and value_surf):
                continue

            block_w = max(label_surf.get_width(), value_surf.get_width())
            if x + block_w + 30 > max_x:
                break

            # разделитель
            sep_h = 26
            sep_alpha = pygame.Surface((1, sep_h), pygame.SRCALPHA)
            sep_alpha.fill((*border_color, 120))
            surface.blit(sep_alpha, (x, center_y - sep_h // 2))
            x += 16

            surface.blit(label_surf, (x, center_y - 19))
            surface.blit(value_surf, (x, center_y + 1))
            x += block_w + 16

        # --- Тонкий прогресс до следующей эры по нижней кромке ---
        self._draw_era_progress(surface, theme, offset, era_color)

        # Кнопка паузы
        if self._pause_button:
            self._pause_button.draw(surface, theme, offset=offset)

    def _draw_era_progress(self, surface, theme, offset, era_color):
        """Полоска прогресса до следующей эры внизу верхней панели."""
        from data.eras import ERAS

        if self._current_era + 1 >= len(ERAS):
            return

        current_unlock = ERAS[self._current_era].get("unlock_money", 0)
        next_unlock = ERAS[self._current_era + 1].get("unlock_money", 1)
        total_earned = self.save.get_save_data("total_earned", 0)

        span = max(1, next_unlock - current_unlock)
        progress = (total_earned - current_unlock) / span

        bar_rect = pygame.Rect(
            offset[0], offset[1] + TOP_PANEL_HEIGHT - 3, self.sw, 3
        )
        style.draw_progress_bar(
            surface, bar_rect, progress, era_color,
            (255, 255, 255, 18), radius=0
        )


    def _draw_click_button(self, surface, theme, offset):
        """Рисует главную кнопку клика."""
        if not self._click_center:
            return

        cx = self._click_center[0] + offset[0]
        cy = self._click_center[1] + offset[1]
        base_r = self._click_button_radius

        # Масштаб кнопки: ТОЛЬКО отклик на нажатие и плавное наведение.
        # Никакой пульсации/«дыхания» в простое — кнопка статична.
        scale = self.animations.click_bounce.scale * self._click_hover_scale
        r = max(10, int(base_r * scale))

        era_data = get_era_data(self._current_era)
        btn_color = era_data.get("click_object_color", (100, 140, 200))
        glow_color = era_data.get("click_object_glow", (60, 100, 180))
        is_hovered = self._is_click_hovered

        # 1. Мягкое свечение вокруг кнопки
        style.draw_glow_circle(
            surface, (cx, cy), int(r * 1.55), glow_color,
            alpha=100 if is_hovered else 62
        )

        # 2. Мягкая тень-эллипс под кнопкой
        shadow_w = int(r * 1.9)
        shadow_h = int(r * 0.55)
        shadow = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        for i in range(5, 0, -1):
            ratio = i / 5
            rect = pygame.Rect(
                (shadow_w - int(shadow_w * ratio)) // 2,
                (shadow_h - int(shadow_h * ratio)) // 2,
                int(shadow_w * ratio), int(shadow_h * ratio)
            )
            pygame.draw.ellipse(shadow, (0, 0, 0, 11), rect)
        surface.blit(shadow, (cx - shadow_w // 2, cy + int(r * 0.80)))

        # 3. Сфера (гладкий градиент + блик, кешируется по цвету эры)
        d = r * 2
        dome = style.radial_dome(d, btn_color)
        surface.blit(dome, (cx - r, cy - r))

        # 5. Значок эры в «медальоне»
        icon = self.ERA_ICONS[min(self._current_era, len(self.ERA_ICONS) - 1)]
        badge_r = max(13, int(r * 0.26))
        badge_cy = cy - int(r * 0.50)

        badge = pygame.Surface((badge_r * 2, badge_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            badge, (0, 0, 0, 26), (badge_r, badge_r), badge_r
        )
        pygame.draw.circle(
            badge, (255, 255, 255, 40), (badge_r, badge_r), badge_r, 1
        )
        surface.blit(badge, (cx - badge_r, badge_cy - badge_r))

        icon_font = get_font(max(14, int(badge_r * 1.6)))
        icon_surf = icon_font.render(icon, True, (255, 255, 255))
        surface.blit(
            icon_surf, icon_surf.get_rect(center=(cx, badge_cy))
        )

        # 6. Текст «КЛИК!»
        text_size = max(18, int(r * 0.44))
        text_font = get_font(text_size, bold=True)
        click_text = t("game.click")
        text_center = (cx, cy + int(r * 0.24))

        shadow_txt = text_font.render(click_text, True, (0, 0, 0))
        shadow_txt.set_alpha(110)
        surface.blit(
            shadow_txt,
            shadow_txt.get_rect(
                center=(text_center[0], text_center[1] + 2)
            )
        )

        txt_color = (255, 252, 220) if is_hovered else (255, 255, 255)
        text_surf = text_font.render(click_text, True, txt_color)
        surface.blit(text_surf, text_surf.get_rect(center=text_center))

    def _draw_golden_objects(self, surface, theme):
        """Рисует золотые летящие объекты."""
        font = self._fonts.get("large")
        small_font = self._fonts.get("small")

        for ev in self.event_system.active_events:
            if ev.event_type == "golden" and ev.alive:
                x, y = int(ev.x), int(ev.y)

                # Свечение
                glow_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
                glow_alpha = int(100 * (0.5 + 0.5 * math.sin(time.time() * 8)))
                pygame.draw.circle(glow_surf, (255, 215, 0, glow_alpha), (40, 40), 40)
                surface.blit(glow_surf, (x - 40, y - 40))

                # Иконка
                if font:
                    icon_surf = font.render(ev.icon, True, (255, 215, 0))
                    icon_rect = icon_surf.get_rect(center=(x, y))
                    surface.blit(icon_surf, icon_rect)

                # Таймер
                if small_font and ev.time_left > 0:
                    timer_str = f"{ev.time_left:.1f}s"
                    timer_surf = small_font.render(timer_str, True, (255, 255, 200))
                    timer_rect = timer_surf.get_rect(center=(x, y + 30))
                    surface.blit(timer_surf, timer_rect)

                # Трейл
                self.particles.emit_trail(x, y, color=(255, 215, 0))

            elif ev.event_type == "challenge" and ev.alive:
                # Индикатор challenge
                self._draw_challenge_indicator(surface, ev, theme)

    def _draw_challenge_indicator(self, surface, ev, theme):
        """Рисует индикатор испытания."""
        font = self._fonts.get("normal")
        big_font = self._fonts.get("large")

        if not font:
            return

        cx = (self.sw - SIDE_PANEL_WIDTH) // 2
        cy = TOP_PANEL_HEIGHT + 40

        # Фон
        ind_w, ind_h = 350, 60
        ind_surf = pygame.Surface((ind_w, ind_h), pygame.SRCALPHA)
        pygame.draw.rect(ind_surf, (30, 30, 50, 200), (0, 0, ind_w, ind_h), border_radius=10)
        surface.blit(ind_surf, (cx - ind_w // 2, cy))

        # Текст
        progress_str = f"{ev.icon} {ev.challenge_clicks}/{ev.challenge_required}  |  {ev.time_left:.1f}s"
        progress_surf = font.render(progress_str, True, (255, 220, 100))
        progress_rect = progress_surf.get_rect(center=(cx, cy + ind_h // 2))
        surface.blit(progress_surf, progress_rect)

        # Прогресс-бар
        bar_w = ind_w - 20
        bar_h = 6
        bar_x = cx - bar_w // 2
        bar_y = cy + ind_h - 12
        fill_ratio = min(1.0, ev.challenge_clicks / max(ev.challenge_required, 1))

        pygame.draw.rect(surface, (50, 50, 70), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        if fill_ratio > 0:
            pygame.draw.rect(surface, (100, 220, 100),
                             (bar_x, bar_y, int(bar_w * fill_ratio), bar_h),
                             border_radius=3)

    def _draw_buff_indicators(self, surface, theme):
        """Рисует индикаторы активных баффов/дебаффов."""
        font = self._fonts.get("small")
        tiny = self._fonts.get("tiny")
        if not font:
            return

        x = 12
        y = TOP_PANEL_HEIGHT + 12

        for buff in self.event_system.active_buffs:
            if not buff.alive:
                continue

            is_positive = buff.event_type == "buff"
            color = (70, 210, 120) if is_positive else (230, 90, 90)

            name = t(f"events.{buff.event_id}")
            label = fit_text(name, font, 190)
            text = f"{buff.icon} {label}  {buff.time_left:.0f}s"
            text_surf = font.render(text, True, style.lighten(color, 0.35))

            w = text_surf.get_width() + 20
            h = text_surf.get_height() + 14
            rect = pygame.Rect(x, y, w, h)

            style.draw_panel(
                surface, rect, (24, 26, 36), radius=9,
                border_color=style.with_alpha(color, 120),
                border_width=1, alpha=225, gradient=0.12,
                shadow=True, shadow_alpha=40
            )
            surface.blit(text_surf, (x + 10, y + 5))

            # Полоска остатка времени
            if buff.duration > 0:
                ratio = max(0.0, min(1.0, buff.time_left / buff.duration))
                bar = pygame.Rect(x + 10, rect.bottom - 6, w - 20, 2)
                style.draw_progress_bar(
                    surface, bar, ratio, color, (255, 255, 255), bg_alpha=30
                )

            y += h + 6

    def _draw_shop_panel(self, surface, theme, offset):
        """Рисует правую панель магазина."""
        panel_color = theme.get("panel_color", (40, 40, 55))
        border_color = theme.get("panel_border", (60, 60, 80))
        text_color = theme.get("text_color", (230, 230, 240))
        dim_color = theme.get("text_dim", (150, 150, 170))
        money_color = theme.get("money_color", (80, 220, 120))
        danger_color = theme.get("danger_color", (220, 60, 60))
        accent = theme.get("accent_color", (50, 150, 255))

        shop_x = self.sw - SIDE_PANEL_WIDTH + offset[0]
        shop_y = TOP_PANEL_HEIGHT + offset[1]
        shop_h = self.sh - TOP_PANEL_HEIGHT - BOTTOM_PANEL_HEIGHT

        shop_rect = pygame.Rect(shop_x, shop_y, SIDE_PANEL_WIDTH, shop_h)
        style.draw_panel(
            surface, shop_rect, panel_color, radius=0,
            gradient=0.14
        )

        # Левая граница + мягкая тень на игровое поле
        pygame.draw.line(
            surface, border_color, (shop_x, shop_y), (shop_x, shop_y + shop_h)
        )
        edge_shadow = pygame.Surface((14, shop_h), pygame.SRCALPHA)
        for i in range(14):
            alpha = int(52 * (1 - i / 14))
            pygame.draw.line(edge_shadow, (0, 0, 0, alpha), (i, 0), (i, shop_h))
        surface.blit(edge_shadow, (shop_x - 14, shop_y))

        # Кнопки категорий и веток
        for btn in self._shop_cat_buttons:
            btn.draw(surface, theme, offset=offset)
        for btn in self._shop_branch_buttons:
            btn.draw(surface, theme, offset=offset)

        # Разделитель под фильтрами
        sep_y = TOP_PANEL_HEIGHT + self.CAT_AREA_H + self.BRANCH_AREA_H - 6
        style.draw_separator(
            surface, int(shop_x + 6), int(shop_x + SIDE_PANEL_WIDTH - 6),
            sep_y + offset[1], border_color
        )

        # Предметы магазина
        if not self._shop_scroll:
            return

        items = self._get_shop_items()
        item_h = 76
        self._shop_scroll.set_content_height(len(items) * item_h + 10)

        def draw_items(surf, scroll_y):
            font = self._fonts.get("small")
            tiny_font = self._fonts.get("tiny")
            if not font:
                return

            items_x = self._shop_scroll.rect.x
            items_top = self._shop_scroll.rect.top
            mouse_pos = pygame.mouse.get_pos()

            for i, item in enumerate(items):
                item_y = items_top + i * item_h - scroll_y

                if item_y + item_h < items_top - 5:
                    continue
                if item_y > self._shop_scroll.rect.bottom + 5:
                    break

                upgrade_id = item["id"]
                count = self.save.get_upgrade_count(upgrade_id)
                cost = self.economy.get_upgrade_cost(upgrade_id)
                can_buy, reason = self.economy.can_buy_upgrade(
                    upgrade_id, self._current_era
                )
                if not self.economy.is_upgrade_visible(upgrade_id, self._current_era):
                    continue

                name = t(f"upgrades.{upgrade_id}")
                item_w = self._shop_scroll.rect.width - 15
                card = pygame.Rect(items_x, item_y, item_w, item_h - 5)
                hovered = card.collidepoint(mouse_pos)

                # Цвета карточки по состоянию
                if can_buy:
                    card_bg = (42, 52, 70)
                    accent_color = money_color
                elif reason == "max_reached":
                    card_bg = (34, 47, 38)
                    accent_color = (110, 200, 130)
                else:
                    card_bg = (33, 35, 47)
                    accent_color = (68, 72, 92)

                if hovered and can_buy:
                    card_bg = style.lighten(card_bg, 0.10)

                if can_buy or reason == "max_reached":
                    border = (
                        accent_color if hovered
                        else style.mix(card_bg, accent_color, 0.42)
                    )
                else:
                    border = (52, 56, 74)

                style.draw_panel(
                    surf, card, card_bg, radius=8,
                    border_color=border, border_width=1, gradient=0.07,
                    alpha=235,
                    shadow=hovered and can_buy, shadow_alpha=45
                )

                # Акцентная полоска слева
                style.draw_soft_rect(
                    surf,
                    pygame.Rect(card.x + 1, card.y + 9, 3, card.height - 18),
                    accent_color, 235 if can_buy else 150, radius=2
                )

                text_left = card.x + 12
                text_right_limit = card.right - 44

                # Название
                name_color = (
                    text_color if (can_buy or reason == "max_reached")
                    else dim_color
                )
                name_surf = font.render(
                    fit_text(name, font, text_right_limit - text_left),
                    True, name_color
                )
                surf.blit(name_surf, (text_left, card.y + 6))

                # Цена / статус
                if reason == "max_reached":
                    status = t("shop.max")
                    status_surf = tiny_font.render(status, True, (140, 220, 160))
                    surf.blit(status_surf, (text_left, card.y + 27))
                elif reason == "era_locked":
                    era_req = item.get("era_required", 0)
                    lock_str = f"🔒 {t('shop.era_locked', era=era_req + 1)}"
                    lock_surf = tiny_font.render(
                        fit_text(lock_str, tiny_font, text_right_limit - text_left),
                        True, dim_color
                    )
                    surf.blit(lock_surf, (text_left, card.y + 27))
                elif reason == "prerequisite":
                    prereq_name = t(f"upgrades.{item.get('prerequisite', '')}")
                    req_str = f"🔒 {prereq_name}"
                    req_surf = tiny_font.render(
                        fit_text(req_str, tiny_font, text_right_limit - text_left),
                        True, dim_color
                    )
                    surf.blit(req_surf, (text_left, card.y + 27))
                else:
                    cost_str = format_money(cost, self._num_format)
                    cost_color = money_color if can_buy else danger_color
                    cost_surf = tiny_font.render(cost_str, True, cost_color)
                    pill = pygame.Rect(
                        0, 0,
                        cost_surf.get_width() + 16,
                        cost_surf.get_height() + 6
                    )
                    pill.topleft = (text_left - 2, card.y + 25)
                    style.draw_soft_rect(
                        surf, pill, cost_color,
                        34 if can_buy else 26, radius=pill.height // 2
                    )
                    surf.blit(cost_surf, cost_surf.get_rect(center=pill.center))

                # Эффект
                effect_type = item.get("effect_type", "")
                effect_value = item.get("effect_value", 0)
                if effect_type in ("click_multiplier", "passive_multiplier",
                                   "all_multiplier", "discount", "crit_chance"):
                    effect_str = t(
                        f"effects.{effect_type}", value=f"{effect_value * 100:.0f}"
                    )
                elif effect_type == "crit_multiplier":
                    effect_str = t(
                        f"effects.{effect_type}", value=f"{effect_value:.0f}"
                    )
                else:
                    effect_str = t(
                        f"effects.{effect_type}",
                        value=format_number(effect_value, self._num_format)
                    )

                effect_surf = tiny_font.render(
                    fit_text(effect_str, tiny_font, card.width - 24),
                    True, (128, 156, 196)
                )
                surf.blit(effect_surf, (text_left, card.y + 48))

                # Счётчик / галочка справа
                max_count = item.get("max_count", 1)
                if max_count != 1 and count > 0:
                    count_str = f"x{count}"
                    count_surf = tiny_font.render(
                        count_str, True, (200, 216, 240)
                    )
                    rect = count_surf.get_rect(
                        right=card.right - 10, top=card.y + 10
                    )
                    surf.blit(count_surf, rect)
                elif max_count == 1 and count > 0:
                    style.draw_check(
                        surf, (card.right - 17, card.y + 19),
                        size=11, color=(120, 220, 150)
                    )

        self._shop_scroll.draw(surface, theme, draw_items)

    def _draw_bottom_panel(self, surface, theme, offset):
        """Рисует нижнюю панель."""
        panel_color = theme.get("panel_color", (40, 40, 55))
        border_color = theme.get("panel_border", (60, 60, 80))

        bot_rect = pygame.Rect(
            offset[0], self.sh - BOTTOM_PANEL_HEIGHT + offset[1],
            self.sw, BOTTOM_PANEL_HEIGHT
        )
        style.draw_panel(
            surface, bot_rect, panel_color, radius=0, gradient=0.16
        )

        # Тень вверх и линия-разделитель
        shadow = pygame.Surface((self.sw, 10), pygame.SRCALPHA)
        for i in range(10):
            alpha = int(46 * (1 - i / 10))
            pygame.draw.line(shadow, (0, 0, 0, alpha), (0, i), (self.sw, i))
        surface.blit(shadow, (offset[0], bot_rect.top - 10))
        pygame.draw.line(
            surface, border_color,
            (offset[0], bot_rect.top), (self.sw + offset[0], bot_rect.top)
        )

        # Кнопки
        for btn in self._bottom_buttons.values():
            btn.draw(surface, theme, offset=offset)

    # ================================================================
    # УТИЛИТЫ
    # ================================================================

    def reload_theme(self):
        """Перезагружает тему."""
        self._load_theme()

    def resize(self, width, height):
        """Обновляет размеры при изменении окна."""
        self.sw = width
        self.sh = height
        self._initialized = False
        self.bg_effects.resize(width, height)
        self.notifications.resize(width, height)

    def reset(self):
        """Полный сброс экрана."""
        self.result = None
        self.wants_pause = False
        self._initialized = False
        self.event_system.clear()
        self.particles.clear()
        self.floating_text.clear()
        self.notifications.clear()
        self.animations.clear()
        self._autosave_timer = 0

        ach_bonuses = self.achievement_tracker.get_achievement_bonuses()
        self.economy.recalculate(ach_bonuses)
        self._load_theme()

        total_earned = self.save.get_save_data("total_earned", 0)
        self._current_era = get_era_for_money(total_earned)
        self._previous_era = self._current_era
