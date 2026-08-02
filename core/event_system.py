"""
botyaraclick - core/event_system.py
Система рандомных игровых событий.

Управляет таймерами, появлением и обработкой ивентов.
"""

import random
import time
import math

from config import (
    EVENT_MIN_INTERVAL, EVENT_MAX_INTERVAL,
    EVENT_GOLDEN_DURATION
)
from data.events import (
    EVENTS, get_available_events, get_event_weight
)


class ActiveEvent:
    """Активное событие на экране."""

    def __init__(self, event_data, game_state):
        self.data = event_data
        self.event_type = event_data["type"]
        self.event_id = event_data["id"]
        self.icon = event_data.get("icon", "🎲")

        self.alive = True
        self.created_at = time.time()

        # Позиция (для золотых объектов)
        self.x = 0
        self.y = 0
        self.vx = 0
        self.vy = 0

        # Таймеры
        self.time_left = 0
        self.duration = 0

        # Результат
        self.result = None  # "caught", "missed", "accepted", "declined", "success", "failed"
        self.result_amount = 0

        # Challenge
        self.challenge_clicks = 0
        self.challenge_required = 0

        # Инициализация по типу
        self._init_by_type(game_state)

    def _init_by_type(self, game_state):
        """Инициализирует ивент по типу."""
        screen_w = game_state.get("screen_width", 1280)
        screen_h = game_state.get("screen_height", 720)

        if self.event_type == "golden":
            # Летит через экран
            catch_time = self.data.get("catch_time", 3.0)
            # Добавляем бонусное время от престижа
            bonus_time = game_state.get("golden_time_bonus", 0)
            self.time_left = catch_time + bonus_time
            self.duration = self.time_left

            # Случайная позиция
            side = random.choice(["left", "right", "top"])
            if side == "left":
                self.x = -30
                self.y = random.uniform(100, screen_h - 200)
                self.vx = random.uniform(150, 300)
                self.vy = random.uniform(-30, 30)
            elif side == "right":
                self.x = screen_w + 30
                self.y = random.uniform(100, screen_h - 200)
                self.vx = random.uniform(-300, -150)
                self.vy = random.uniform(-30, 30)
            else:
                self.x = random.uniform(200, screen_w - 200)
                self.y = -30
                self.vx = random.uniform(-50, 50)
                self.vy = random.uniform(100, 200)

        elif self.event_type in ("buff", "debuff"):
            self.duration = self.data.get("duration", 15)
            self.time_left = self.duration

        elif self.event_type == "challenge":
            self.challenge_required = self.data.get("required_clicks", 50)
            self.challenge_clicks = 0
            self.time_left = self.data.get("time_limit", 10)
            self.duration = self.time_left

    def update(self, dt, screen_w, screen_h):
        """Обновляет состояние ивента."""
        if not self.alive:
            return

        self.time_left -= dt

        if self.event_type == "golden":
            self.x += self.vx * dt
            self.y += self.vy * dt

            # Улетел за экран или время вышло
            if self.time_left <= 0:
                self.result = "missed"
                self.alive = False
            elif (self.x < -100 or self.x > screen_w + 100 or
                  self.y < -100 or self.y > screen_h + 100):
                self.result = "missed"
                self.alive = False

        elif self.event_type in ("buff", "debuff"):
            if self.time_left <= 0:
                self.alive = False
                if self.event_type == "debuff":
                    self.result = "survived"

        elif self.event_type == "challenge":
            if self.time_left <= 0:
                if self.challenge_clicks >= self.challenge_required:
                    self.result = "success"
                else:
                    self.result = "failed"
                self.alive = False

    def try_catch(self, click_x, click_y, catch_radius=50):
        """Пытается поймать золотой объект."""
        if self.event_type != "golden" or not self.alive:
            return False

        dist = math.sqrt((click_x - self.x) ** 2 + (click_y - self.y) ** 2)
        if dist <= catch_radius:
            self.result = "caught"
            self.alive = False
            return True
        return False

    def add_challenge_click(self):
        """Добавляет клик для challenge."""
        if self.event_type == "challenge" and self.alive:
            self.challenge_clicks += 1
            if self.challenge_clicks >= self.challenge_required:
                self.result = "success"
                self.alive = False
                return True
        return False

    @property
    def progress(self):
        """Прогресс ивента (0-1)."""
        if self.duration <= 0:
            return 1.0
        return 1.0 - (self.time_left / self.duration)


class EventSystem:
    """Система управления рандомными ивентами."""

    def __init__(self):
        self.active_events = []  # список ActiveEvent
        self.active_buffs = []   # активные баффы/дебаффы
        self._next_event_timer = 0
        self._schedule_next_event()

        # Статистика
        self.total_events = 0

    def _schedule_next_event(self):
        """Планирует следующий ивент."""
        self._next_event_timer = random.uniform(
            EVENT_MIN_INTERVAL, EVENT_MAX_INTERVAL
        )

    def update(self, dt, game_state):
        """
        Обновляет систему ивентов.

        game_state: dict с ключами:
            - current_era: int
            - screen_width: int
            - screen_height: int
            - money: float
            - passive_income: float
            - click_power: float
            - event_luck: float (бонус от престижа)
            - golden_time_bonus: float
        """
        screen_w = game_state.get("screen_width", 1280)
        screen_h = game_state.get("screen_height", 720)

        # Обновляем активные ивенты
        for event in self.active_events:
            event.update(dt, screen_w, screen_h)

        # Обновляем баффы
        for buff in self.active_buffs:
            buff.update(dt, screen_w, screen_h)

        # Удаляем мёртвые
        self.active_events = [e for e in self.active_events if e.alive]
        self.active_buffs = [b for b in self.active_buffs if b.alive]

        # Таймер нового ивента
        self._next_event_timer -= dt
        if self._next_event_timer <= 0:
            self._spawn_event(game_state)
            self._schedule_next_event()

    def _spawn_event(self, game_state):
        """Создаёт новый случайный ивент."""
        current_era = game_state.get("current_era", 0)
        event_luck = game_state.get("event_luck", 0)

        available = get_available_events(current_era)
        if not available:
            return

        # Взвешенный выбор
        weights = []
        for event in available:
            weight = get_event_weight(event)

            # Бонус удачи увеличивает шанс позитивных ивентов
            if event["type"] in ("buff", "golden", "instant"):
                if event.get("effect_value", 0) > 0 or event["type"] == "golden":
                    weight = int(weight * (1 + event_luck))

            weights.append(weight)

        chosen = random.choices(available, weights=weights, k=1)[0]

        # Создаём ивент
        active = ActiveEvent(chosen, game_state)

        if chosen["type"] in ("buff", "debuff"):
            self.active_buffs.append(active)
        else:
            self.active_events.append(active)

        self.total_events += 1

    def handle_click(self, click_x, click_y, game_state):
        """
        Обрабатывает клик — проверяет поимку золотых объектов
        и клики для challenges.
        Возвращает результат или None.
        """
        results = []

        # Проверяем золотые объекты
        for event in self.active_events:
            if event.event_type == "golden" and event.alive:
                if event.try_catch(click_x, click_y):
                    reward = self._calculate_golden_reward(event, game_state)
                    results.append({
                        "type": "golden_caught",
                        "event": event,
                        "reward": reward,
                    })

        # Добавляем клики в challenges
        for event in self.active_events:
            if event.event_type == "challenge" and event.alive:
                if event.add_challenge_click():
                    reward = self._calculate_challenge_reward(event, game_state)
                    results.append({
                        "type": "challenge_complete",
                        "event": event,
                        "reward": reward,
                    })

        return results if results else None

    def _calculate_golden_reward(self, event, game_state):
        """Рассчитывает награду за пойманный золотой объект."""
        money = game_state.get("money", 0)
        click_power = game_state.get("click_power", 1)

        reward_type = event.data.get("reward_type", "click_mult_instant")
        reward_value = event.data.get("reward_value", 10)

        if reward_type == "click_mult_instant":
            return click_power * reward_value
        elif reward_type == "money_percent":
            return max(click_power * 10, money * reward_value)
        return click_power * 10

    def _calculate_challenge_reward(self, event, game_state):
        """Рассчитывает награду за выполненное испытание."""
        money = game_state.get("money", 0)

        reward_type = event.data.get("reward_type", "money_percent")
        reward_value = event.data.get("reward_value", 0.05)

        if reward_type == "money_percent":
            return max(100, money * reward_value)
        return 100

    def get_click_multiplier(self):
        """Возвращает текущий множитель клика от баффов/дебаффов."""
        mult = 1.0
        for buff in self.active_buffs:
            if buff.data.get("effect") == "click_mult":
                if buff.event_type == "buff":
                    mult *= buff.data.get("effect_value", 1.0)
                else:  # debuff
                    mult *= buff.data.get("effect_value", 1.0)
        return mult

    def get_passive_multiplier(self):
        """Возвращает текущий множитель пассивного дохода от баффов/дебаффов."""
        mult = 1.0
        for buff in self.active_buffs:
            if buff.data.get("effect") == "passive_mult":
                if buff.event_type == "buff":
                    mult *= buff.data.get("effect_value", 1.0)
                else:  # debuff
                    mult *= buff.data.get("effect_value", 1.0)
        return mult

    def process_choice(self, event, choice, game_state):
        """
        Обрабатывает выбор игрока в choice-ивенте.
        Возвращает результат.
        """
        if choice == "accept":
            money = game_state.get("money", 0)
            risk_percent = event.data.get("risk_percent", 0.10)
            win_chance = event.data.get("win_chance", 0.50)
            win_multiplier = event.data.get("win_multiplier", 2.0)

            risk_amount = money * risk_percent

            if random.random() < win_chance:
                # Выиграл
                win_amount = risk_amount * win_multiplier
                event.result = "won"
                event.result_amount = win_amount
                event.alive = False
                return {
                    "type": "deal_won",
                    "amount": win_amount,
                    "risk": risk_amount,
                }
            else:
                # Проиграл
                event.result = "lost"
                event.result_amount = risk_amount
                event.alive = False
                return {
                    "type": "deal_lost",
                    "amount": risk_amount,
                }
        else:
            # Отказался
            event.result = "declined"
            event.alive = False
            return {"type": "declined"}

    def process_instant(self, event, game_state):
        """Обрабатывает мгновенный ивент."""
        money = game_state.get("money", 0)
        effect_value = event.data.get("effect_value", 0)

        if event.data.get("effect") == "money_percent":
            amount = money * abs(effect_value)
            if effect_value > 0:
                return {"type": "money_gained", "amount": amount}
            else:
                return {"type": "money_lost", "amount": amount}

        return None

    def clear(self):
        """Очищает все ивенты."""
        self.active_events.clear()
        self.active_buffs.clear()

    @property
    def has_active_events(self):
        """Есть ли активные ивенты на экране."""
        return len(self.active_events) > 0 or len(self.active_buffs) > 0
