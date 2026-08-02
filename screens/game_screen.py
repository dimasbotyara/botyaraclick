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


class GameScreen:
    """Основной игровой экран."""

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
            self._fonts = {
                "title": pygame.font.Font(None, 36),
                "large": pygame.font.Font(None, 30),
                "button": pygame.font.Font(None, 24),
                "normal": pygame.font.Font(None, 20),
                "small": pygame.font.Font(None, 16),
                "tiny": pygame.font.Font(None, 14),
                "money_big": pygame.font.Font(None, 32),
                "click_text": pygame.font.Font(None, 42),
            }

        self.tooltip.font = self._fonts.get("small")
        self.notifications.font = self._fonts.get("normal")
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
            ("tree", t("upgrade_tree.title")),
            ("achievements", t("achievements.title")),
            ("themes", t("themes.title")),
            ("statistics", t("statistics.title")),
            ("prestige", t("prestige.title")),
        ]
        btn_count = len(bottom_btns)
        btn_w = min(160, (self.sw - 20) // btn_count - 5)
        btn_h = BOTTOM_PANEL_HEIGHT - 10
        total_w = btn_count * btn_w + (btn_count - 1) * 5
        start_x = (self.sw - total_w) // 2

        self._bottom_buttons.clear()
        for i, (bid, btext) in enumerate(bottom_btns):
            btn = Button(
                start_x + i * (btn_w + 5),
                self.sh - BOTTOM_PANEL_HEIGHT + 5,
                btn_w, btn_h,
                text=btext,
                font=self._fonts.get("small"),
                color=(50, 50, 70),
                hover_color=(70, 70, 95),
                border_radius=6,
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
        cat_area_h = 45  # высота кнопок категорий
        branch_area_h = 35
        items_top = shop_top + cat_area_h + branch_area_h + 5
        items_height = shop_height - cat_area_h - branch_area_h - 10

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
        """Строит кнопки категорий магазина."""
        shop_x = self.sw - SIDE_PANEL_WIDTH
        shop_top = TOP_PANEL_HEIGHT
        font = self._fonts.get("tiny")

        self._shop_cat_buttons.clear()
        cat_btn_w = (SIDE_PANEL_WIDTH - 10) // len(CATEGORY_ORDER)

        for i, cat_id in enumerate(CATEGORY_ORDER):
            cat_name = t(f"categories.{cat_id}")
            # Сокращаем если не влезает
            if font and font.size(cat_name)[0] > cat_btn_w - 6:
                cat_name = cat_name[:6] + ".."

            btn = Button(
                shop_x + 5 + i * cat_btn_w,
                shop_top + 3,
                cat_btn_w - 2, 38,
                text=cat_name,
                font=font,
                color=(60, 100, 160) if cat_id == self._shop_category else (45, 45, 65),
                hover_color=(75, 115, 175),
                border_radius=5,
                tag=cat_id,
            )
            self._shop_cat_buttons.append(btn)

        self._build_shop_branches()

    def _build_shop_branches(self):
        """Строит кнопки веток текущей категории."""
        shop_x = self.sw - SIDE_PANEL_WIDTH
        shop_top = TOP_PANEL_HEIGHT + 43
        font = self._fonts.get("tiny")

        self._shop_branch_buttons.clear()

        cat_data = CATEGORIES.get(self._shop_category, {})
        branches = cat_data.get("branches", [])

        if not branches:
            return

        br_btn_w = (SIDE_PANEL_WIDTH - 10) // max(len(branches), 1)

        for i, br_id in enumerate(branches):
            br_name = t(f"branches.{br_id}")
            if font and font.size(br_name)[0] > br_btn_w - 6:
                br_name = br_name[:7] + ".."

            btn = Button(
                shop_x + 5 + i * br_btn_w,
                shop_top,
                br_btn_w - 2, 30,
                text=br_name,
                font=font,
                color=(55, 90, 140) if br_id == self._shop_branch else (40, 40, 58),
                hover_color=(70, 105, 155),
                border_radius=4,
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
        item_h = 65
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

        # Фон панели
        panel_rect = pygame.Rect(
            offset[0], offset[1],
            self.sw, TOP_PANEL_HEIGHT
        )
        panel_surf = pygame.Surface((self.sw, TOP_PANEL_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (*panel_color, 230),
                         (0, 0, self.sw, TOP_PANEL_HEIGHT))
        surface.blit(panel_surf, panel_rect.topleft)

        # Разделительная линия
        pygame.draw.line(
            surface,
            theme.get("panel_border", (60, 60, 80)),
            (offset[0], TOP_PANEL_HEIGHT + offset[1]),
            (self.sw + offset[0], TOP_PANEL_HEIGHT + offset[1])
        )

        font = self._fonts.get("normal")
        big_font = self._fonts.get("money_big")
        small_font = self._fonts.get("small")

        if not font:
            return

        money = self.save.get_save_data("money", 0)
        per_click = self.economy.click_power
        per_sec = self.economy.passive_income

        # Баланс
        money_str = format_money(money, self._num_format)
        money_surf = big_font.render(money_str, True, money_color) if big_font else font.render(money_str, True, money_color)
        surface.blit(money_surf, (20 + offset[0], 15 + offset[1]))

        # $/клик
        click_str = f"{format_money(per_click, self._num_format)}/{t('game.per_click')}"
        click_surf = font.render(click_str, True, accent)
        surface.blit(click_surf, (280 + offset[0], 20 + offset[1]))

        # $/сек
        sec_str = f"{format_money(per_sec, self._num_format)}/{t('game.per_second')}"
        sec_surf = font.render(sec_str, True, text_color)
        surface.blit(sec_surf, (520 + offset[0], 20 + offset[1]))

        # Эра
        era_data = get_era_data(self._current_era)
        era_name = t(f"eras.{era_data['id']}")
        era_str = f"{t('game.era')}: {era_name}"
        if small_font:
            era_surf = small_font.render(era_str, True, theme.get("text_dim", (150, 150, 170)))
            surface.blit(era_surf, (740 + offset[0], 22 + offset[1]))

        # Кнопка паузы
        if self._pause_button:
            self._pause_button.draw(surface, theme, offset=offset)

    def _draw_click_button(self, surface, theme, offset):
        """Рисует главную кнопку клика."""
        if not self._click_center:
            return

        cx = self._click_center[0] + offset[0]
        cy = self._click_center[1] + offset[1]
        base_r = self._click_button_radius

        # Масштаб от нажатия и наведения (БЕЗ авто-пульсации!)
        scale = self.animations.click_bounce.scale * getattr(self, "_click_hover_scale", 1.0)
        r = max(10, int(base_r * scale))

        era_data = get_era_data(self._current_era)
        btn_color = era_data.get("click_object_color", (100, 140, 200))
        glow_color = era_data.get("click_object_glow", (60, 100, 180))

        is_hovered = getattr(self, "_is_click_hovered", False)

        # 1. Плавное свечение вокруг кнопки (усиливается при наведении)
        glow_r = int(r * 1.5)
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        base_alpha = 70 if is_hovered else 40
        pygame.draw.circle(
            glow_surf,
            (*glow_color, base_alpha),
            (glow_r, glow_r), glow_r
        )
        if is_hovered:
            pygame.draw.circle(
                glow_surf,
                (255, 255, 255, 30),
                (glow_r, glow_r), int(r * 1.1)
            )
        surface.blit(glow_surf, (cx - glow_r, cy - glow_r))

        # 2. Мягкая объёмная тень под кнопкой
        shadow_surf = pygame.Surface((r * 2 + 10, r * 2 + 10), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surf, (0, 0, 0, 80), (r + 5, r + 7), r)
        surface.blit(shadow_surf, (cx - r - 5, cy - r - 3))

        # 3. Основная сферическая кнопка с градиентом
        main_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        center_color = tuple(min(255, int(c * 1.35)) for c in btn_color)
        edge_color = tuple(max(0, int(c * 0.65)) for c in btn_color)

        steps = 12
        for i in range(steps):
            step_r = int(r * (1 - i / (steps * 1.3)))
            if step_r <= 0:
                continue
            t_val = i / steps
            offset_x = r - int(r * 0.12 * t_val)
            offset_y = r - int(r * 0.15 * t_val)
            r_c = int(center_color[0] * t_val + edge_color[0] * (1 - t_val))
            g_c = int(center_color[1] * t_val + edge_color[1] * (1 - t_val))
            b_c = int(center_color[2] * t_val + edge_color[2] * (1 - t_val))
            pygame.draw.circle(main_surf, (r_c, g_c, b_c), (offset_x, offset_y), step_r)

        # 4. Внешний кольцевой ободок (ярче при наведении)
        ring_color = (255, 255, 255) if is_hovered else tuple(min(255, c + 50) for c in btn_color)
        ring_width = 4 if is_hovered else 3
        pygame.draw.circle(main_surf, ring_color, (r, r), r - 1, ring_width)

        # 5. Верхний глянцевый блик
        glare_w = int(r * 1.2)
        glare_h = int(r * 0.5)
        if glare_w > 0 and glare_h > 0:
            glare_surf = pygame.Surface((glare_w, glare_h), pygame.SRCALPHA)
            pygame.draw.ellipse(glare_surf, (255, 255, 255, 80 if is_hovered else 50), (0, 0, glare_w, glare_h))
            main_surf.blit(glare_surf, (r - glare_w // 2, int(r * 0.1)))

        surface.blit(main_surf, (cx - r, cy - r))

        # 6. Иконка эры + Текст
        font = self._fonts.get("click_text")
        small_font = self._fonts.get("button") or self._fonts.get("normal")

        era_icons = ["📟", "💻", "🚀", "🏢", "👑", "🌌", "🪐"]
        icon = era_icons[min(self._current_era, len(era_icons) - 1)]

        if font:
            click_text = t("game.click")
            # Тень от текста
            shadow_txt = font.render(click_text, True, (0, 0, 0))
            shadow_rect = shadow_txt.get_rect(center=(cx + 2, cy + (12 if small_font else 2)))
            surface.blit(shadow_txt, shadow_rect)

            # Сам текст
            txt_color = (255, 255, 200) if is_hovered else (255, 255, 255)
            text_surf = font.render(click_text, True, txt_color)
            text_rect = text_surf.get_rect(center=(cx, cy + (10 if small_font else 0)))

            if small_font:
                icon_surf = small_font.render(icon, True, (255, 255, 255))
                icon_rect = icon_surf.get_rect(center=(cx, cy - 18))
                surface.blit(icon_surf, icon_rect)

            surface.blit(text_surf, text_rect)

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
        if not font:
            return

        x = 10
        y = TOP_PANEL_HEIGHT + 10

        for buff in self.event_system.active_buffs:
            if not buff.alive:
                continue

            is_positive = buff.event_type == "buff"
            color = (60, 200, 100) if is_positive else (200, 60, 60)

            # Маленькая плашка
            time_str = f"{buff.icon} {buff.time_left:.0f}s"
            text_surf = font.render(time_str, True, color)

            bg_w = text_surf.get_width() + 12
            bg_h = text_surf.get_height() + 8
            bg_surf = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
            pygame.draw.rect(bg_surf, (20, 20, 30, 180), (0, 0, bg_w, bg_h), border_radius=4)
            surface.blit(bg_surf, (x, y))
            surface.blit(text_surf, (x + 6, y + 4))

            y += bg_h + 4

    def _draw_shop_panel(self, surface, theme, offset):
        """Рисует правую панель магазина."""
        panel_color = theme.get("panel_color", (40, 40, 55))
        border_color = theme.get("panel_border", (60, 60, 80))
        text_color = theme.get("text_color", (230, 230, 240))
        dim_color = theme.get("text_dim", (150, 150, 170))
        money_color = theme.get("money_color", (80, 220, 120))
        btn_color = theme.get("button_color", (50, 100, 200))
        danger_color = theme.get("danger_color", (220, 60, 60))

        shop_x = self.sw - SIDE_PANEL_WIDTH + offset[0]
        shop_y = TOP_PANEL_HEIGHT + offset[1]
        shop_h = self.sh - TOP_PANEL_HEIGHT - BOTTOM_PANEL_HEIGHT

        # Фон панели
        panel_surf = pygame.Surface((SIDE_PANEL_WIDTH, shop_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (*panel_color, 240),
                         (0, 0, SIDE_PANEL_WIDTH, shop_h))
        surface.blit(panel_surf, (shop_x, shop_y))

        # Разделитель
        pygame.draw.line(surface, border_color,
                         (shop_x, shop_y), (shop_x, shop_y + shop_h))

        # Кнопки категорий
        for btn in self._shop_cat_buttons:
            btn.draw(surface, theme, offset=offset)

        # Кнопки веток
        for btn in self._shop_branch_buttons:
            btn.draw(surface, theme, offset=offset)

        # Предметы магазина
        if self._shop_scroll:
            items = self._get_shop_items()
            item_h = 65
            self._shop_scroll.set_content_height(len(items) * item_h + 10)

            def draw_items(surf, scroll_y):
                font = self._fonts.get("small")
                tiny_font = self._fonts.get("tiny")
                if not font:
                    return

                items_x = self._shop_scroll.rect.x
                items_top = self._shop_scroll.rect.top

                for i, item in enumerate(items):
                    item_y = items_top + i * item_h - scroll_y

                    # Пропускаем невидимые
                    if item_y + item_h < self._shop_scroll.rect.top - 5:
                        continue
                    if item_y > self._shop_scroll.rect.bottom + 5:
                        break

                    upgrade_id = item["id"]
                    count = self.save.get_upgrade_count(upgrade_id)
                    cost = self.economy.get_upgrade_cost(upgrade_id)
                    can_buy, reason = self.economy.can_buy_upgrade(upgrade_id, self._current_era)
                    is_visible = self.economy.is_upgrade_visible(upgrade_id, self._current_era)

                    if not is_visible:
                        continue

                    name = t(f"upgrades.{upgrade_id}")

                    # Фон предмета
                    item_w = self._shop_scroll.rect.width - 15
                    item_rect = pygame.Rect(items_x, item_y, item_w, item_h - 3)

                    if can_buy:
                        bg = (45, 55, 70)
                    elif reason == "max_reached":
                        bg = (35, 50, 35)
                    else:
                        bg = (35, 35, 48)

                    # Hover
                    mouse_pos = pygame.mouse.get_pos()
                    if item_rect.collidepoint(mouse_pos) and can_buy:
                        bg = (55, 70, 90)

                    item_surf = pygame.Surface((item_w, item_h - 3), pygame.SRCALPHA)
                    pygame.draw.rect(item_surf, (*bg, 200),
                                     (0, 0, item_w, item_h - 3),
                                     border_radius=5)
                    surf.blit(item_surf, item_rect.topleft)

                    # Название
                    name_surf = font.render(name, True,
                                           text_color if can_buy or reason == "max_reached"
                                           else dim_color)
                    surf.blit(name_surf, (items_x + 8, item_y + 5))

                    # Цена / Статус
                    if reason == "max_reached":
                        status_surf = tiny_font.render(t("shop.max"), True, (100, 180, 100))
                        surf.blit(status_surf, (items_x + 8, item_y + 25))
                    elif reason == "era_locked":
                        era_req = item.get("era_required", 0)
                        lock_str = f"🔒 {t('shop.era_locked', era=era_req + 1)}"
                        lock_surf = tiny_font.render(lock_str, True, dim_color)
                        surf.blit(lock_surf, (items_x + 8, item_y + 25))
                    elif reason == "prerequisite":
                        prereq_name = t(f"upgrades.{item.get('prerequisite', '')}")
                        req_str = f"🔒 {prereq_name}"
                        req_surf = tiny_font.render(req_str, True, dim_color)
                        surf.blit(req_surf, (items_x + 8, item_y + 25))
                    else:
                        cost_str = format_money(cost, self._num_format)
                        cost_c = money_color if can_buy else danger_color
                        cost_surf = tiny_font.render(cost_str, True, cost_c)
                        surf.blit(cost_surf, (items_x + 8, item_y + 25))

                    # Эффект
                    if tiny_font:
                        effect_type = item.get("effect_type", "")
                        effect_value = item.get("effect_value", 0)
                        if effect_type in ("click_multiplier", "passive_multiplier",
                                          "all_multiplier", "discount",
                                          "crit_chance"):
                            effect_str = t(f"effects.{effect_type}",
                                          value=f"{effect_value * 100:.0f}")
                        elif effect_type == "crit_multiplier":
                            effect_str = t(f"effects.{effect_type}",
                                          value=f"{effect_value:.0f}")
                        else:
                            effect_str = t(f"effects.{effect_type}",
                                          value=format_number(effect_value, self._num_format))
                        eff_surf = tiny_font.render(effect_str, True, (130, 160, 200))
                        surf.blit(eff_surf, (items_x + 8, item_y + 42))

                    # Количество (для многоразовых)
                    if item.get("max_count", 1) != 1 and count > 0:
                        count_str = f"x{count}"
                        count_surf = font.render(count_str, True, (180, 200, 230))
                        count_rect = count_surf.get_rect(
                            right=items_x + item_w - 10,
                            centery=item_y + item_h // 2 - 2
                        )
                        surf.blit(count_surf, count_rect)
                    elif item.get("max_count", 1) == 1 and count > 0:
                        check_surf = font.render("✓", True, (100, 200, 100))
                        check_rect = check_surf.get_rect(
                            right=items_x + item_w - 10,
                            centery=item_y + item_h // 2 - 2
                        )
                        surf.blit(check_surf, check_rect)

            self._shop_scroll.draw(surface, theme, draw_items)

    def _draw_bottom_panel(self, surface, theme, offset):
        """Рисует нижнюю панель."""
        panel_color = theme.get("panel_color", (40, 40, 55))
        border_color = theme.get("panel_border", (60, 60, 80))

        bot_y = self.sh - BOTTOM_PANEL_HEIGHT + offset[1]

        # Фон
        panel_surf = pygame.Surface((self.sw, BOTTOM_PANEL_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (*panel_color, 230),
                         (0, 0, self.sw, BOTTOM_PANEL_HEIGHT))
        surface.blit(panel_surf, (offset[0], bot_y))

        # Разделитель
        pygame.draw.line(surface, border_color,
                         (offset[0], bot_y),
                         (self.sw + offset[0], bot_y))

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
