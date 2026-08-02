"""
botyaraclick - economy.py
Экономические расчёты: сила клика, пассивный доход,
множители, стоимость улучшений, форматирование чисел.
"""

import math

from config import (
    STARTING_CLICK_POWER, PRICE_MULTIPLIER,
    CRIT_BASE_CHANCE, CRIT_BASE_MULTIPLIER,
    NUMBER_SUFFIXES, NUMBER_FORMAT_STANDARD,
    NUMBER_FORMAT_SHORT, NUMBER_FORMAT_SCIENTIFIC,
    PRESTIGE_THRESHOLD, PRESTIGE_FORMULA_DIVISOR
)
from data.upgrades import ALL_UPGRADES, ALL_UPGRADES_LIST


class Economy:
    """
    Центральный класс для всех экономических расчётов.
    Работает на основе данных из save_manager.
    """

    def __init__(self, save_manager):
        self.save = save_manager

        # Кешированные значения (пересчитываются при покупке)
        self._click_power = STARTING_CLICK_POWER
        self._passive_income = 0.0
        self._click_multiplier = 1.0
        self._passive_multiplier = 1.0
        self._all_multiplier = 1.0
        self._discount = 0.0
        self._crit_chance = CRIT_BASE_CHANCE
        self._crit_multiplier = CRIT_BASE_MULTIPLIER
        self._auto_click_rate = 0.0

        self._needs_recalc = True

    def recalculate(self, achievement_bonuses=None):
        """Полностью пересчитывает все экономические параметры."""
        if self.save.save_data is None:
            return

        upgrades = self.save.get_save_data("upgrades", {})
        prestige_upgrades = self.save.get_save_data("prestige_upgrades", {})

        # Базовые значения
        click_power = STARTING_CLICK_POWER
        passive_income = 0.0
        click_mult = 1.0
        passive_mult = 1.0
        all_mult = 1.0
        discount = 0.0
        crit_chance = CRIT_BASE_CHANCE
        crit_mult = CRIT_BASE_MULTIPLIER
        auto_click = 0.0

        # === Суммируем эффекты от обычных улучшений ===
        for upgrade_id, count in upgrades.items():
            if count <= 0:
                continue

            up_data = ALL_UPGRADES.get(upgrade_id)
            if not up_data:
                continue

            effect_type = up_data["effect_type"]
            effect_value = up_data["effect_value"]
            total_effect = effect_value * count

            if effect_type == "click_power":
                click_power += total_effect
            elif effect_type == "passive_income":
                passive_income += total_effect
            elif effect_type == "click_multiplier":
                click_mult += total_effect
            elif effect_type == "passive_multiplier":
                passive_mult += total_effect
            elif effect_type == "all_multiplier":
                all_mult += total_effect
            elif effect_type == "discount":
                discount += total_effect
            elif effect_type == "crit_chance":
                crit_chance += total_effect
            elif effect_type == "crit_multiplier":
                crit_mult += total_effect

        # === Суммируем эффекты от престиж-улучшений ===
        for up_id, count in prestige_upgrades.items():
            if count <= 0:
                continue

            from data.prestige import ALL_PRESTIGE_UPGRADES
            pup = ALL_PRESTIGE_UPGRADES.get(up_id)
            if not pup:
                continue

            effect_type = pup["effect_type"]
            effect_value = pup["effect_value"]
            total = effect_value * count

            if effect_type == "click_multiplier":
                click_mult += total
            elif effect_type == "passive_multiplier":
                passive_mult += total
            elif effect_type == "all_multiplier":
                all_mult += total
            elif effect_type == "discount":
                discount += total
            elif effect_type == "crit_chance":
                crit_chance += total
            elif effect_type == "crit_multiplier":
                crit_mult += total
            elif effect_type == "auto_click":
                auto_click += total

        # === Суммируем бонусы от достижений ===
        if achievement_bonuses:
            all_mult += achievement_bonuses.get("all_multiplier", 0)
            click_mult += achievement_bonuses.get("click_multiplier", 0)
            passive_mult += achievement_bonuses.get("passive_multiplier", 0)
            discount += achievement_bonuses.get("discount", 0)
            crit_chance += achievement_bonuses.get("crit_chance", 0)

        # === Применяем множители ===
        # all_multiplier влияет и на клик, и на пассив
        final_click = click_power * click_mult * all_mult
        final_passive = passive_income * passive_mult * all_mult

        # Ограничения
        discount = min(discount, 0.90)  # максимум 90% скидка
        crit_chance = min(crit_chance, 0.90)  # максимум 90% шанс крита

        # Сохраняем
        self._click_power = final_click
        self._passive_income = final_passive
        self._click_multiplier = click_mult
        self._passive_multiplier = passive_mult
        self._all_multiplier = all_mult
        self._discount = discount
        self._crit_chance = crit_chance
        self._crit_multiplier = crit_mult
        self._auto_click_rate = auto_click

        self._needs_recalc = False

    @property
    def click_power(self):
        return self._click_power

    @property
    def passive_income(self):
        return self._passive_income

    @property
    def crit_chance(self):
        return self._crit_chance

    @property
    def crit_multiplier(self):
        return self._crit_multiplier

    @property
    def discount(self):
        return self._discount

    @property
    def auto_click_rate(self):
        return self._auto_click_rate

    @property
    def click_multiplier(self):
        return self._click_multiplier

    @property
    def passive_multiplier(self):
        return self._passive_multiplier

    @property
    def all_multiplier(self):
        return self._all_multiplier

    def get_upgrade_cost(self, upgrade_id):
        """Возвращает текущую стоимость улучшения."""
        up_data = ALL_UPGRADES.get(upgrade_id)
        if not up_data:
            return float('inf')

        count = self.save.get_upgrade_count(upgrade_id)
        base_cost = up_data["base_cost"]

        # Одноразовые улучшения
        if up_data["max_count"] == 1:
            if count >= 1:
                return float('inf')
            raw_cost = base_cost
        else:
            # Многоразовые — цена растёт
            raw_cost = base_cost * (PRICE_MULTIPLIER ** count)

        # Применяем скидку
        discounted = raw_cost * (1.0 - self._discount)
        return max(1, discounted)

    def can_afford(self, upgrade_id):
        """Может ли игрок купить улучшение."""
        cost = self.get_upgrade_cost(upgrade_id)
        money = self.save.get_save_data("money", 0)
        return money >= cost

    def can_buy_upgrade(self, upgrade_id, current_era=0):
        """
        Комплексная проверка: можно ли купить улучшение.
        Учитывает деньги, эру, пререквизиты, лимит покупок.
        """
        up_data = ALL_UPGRADES.get(upgrade_id)
        if not up_data:
            return False, "not_found"

        # Проверка эры
        if current_era < up_data.get("era_required", 0):
            return False, "era_locked"

        # Проверка пререквизита
        prereq = up_data.get("prerequisite")
        if prereq:
            prereq_count = self.save.get_upgrade_count(prereq)
            if prereq_count <= 0:
                return False, "prerequisite"

        # Проверка лимита
        count = self.save.get_upgrade_count(upgrade_id)
        max_count = up_data.get("max_count", 1)
        if max_count != -1 and count >= max_count:
            return False, "max_reached"

        # Проверка денег
        if not self.can_afford(upgrade_id):
            return False, "no_money"

        return True, "ok"

    def buy_upgrade(self, upgrade_id):
        """
        Покупает улучшение.
        Возвращает True если покупка успешна.
        """
        cost = self.get_upgrade_cost(upgrade_id)
        money = self.save.get_save_data("money", 0)

        if money < cost:
            return False

        # Списываем деньги
        self.save.update_save_data("money", money - cost)

        # Увеличиваем счётчик улучшения
        count = self.save.get_upgrade_count(upgrade_id)
        self.save.set_upgrade_count(upgrade_id, count + 1)

        # Увеличиваем статистику покупок
        self.save.increment_stat("total_purchases")

        # Помечаем что нужен пересчёт
        self._needs_recalc = True

        return True

    def is_upgrade_visible(self, upgrade_id, current_era=0):
        """Проверяет, должно ли улучшение быть видимым в магазине."""
        up_data = ALL_UPGRADES.get(upgrade_id)
        if not up_data:
            return False

        # Показываем если:
        # 1. Эра подходит, ИЛИ
        # 2. Пререквизит куплен (даже если эра ещё не та — тизер)
        era_ok = current_era >= up_data.get("era_required", 0)
        prereq = up_data.get("prerequisite")
        prereq_ok = True
        if prereq:
            prereq_ok = self.save.get_upgrade_count(prereq) > 0

        # Не показываем если эра не подходит и пререквизит не куплен
        if not era_ok and not prereq_ok:
            return False

        return True

    def do_click(self, event_click_mult=1.0):
        """
        Обрабатывает клик.
        Возвращает (earned_amount, is_crit).
        """
        import random

        base = self._click_power * event_click_mult
        is_crit = random.random() < self._crit_chance

        if is_crit:
            earned = base * self._crit_multiplier
        else:
            earned = base

        # Добавляем деньги
        money = self.save.get_save_data("money", 0)
        self.save.update_save_data("money", money + earned)

        # Статистика
        self.save.increment_stat("total_clicks")
        total = self.save.get_save_data("total_earned", 0)
        self.save.update_save_data("total_earned", total + earned)

        return earned, is_crit

    def do_passive_tick(self, dt, event_passive_mult=1.0):
        """
        Обрабатывает пассивный доход за dt секунд.
        Возвращает заработанную сумму.
        """
        income = self._passive_income * event_passive_mult * dt
        if income <= 0:
            return 0

        money = self.save.get_save_data("money", 0)
        self.save.update_save_data("money", money + income)

        total = self.save.get_save_data("total_earned", 0)
        self.save.update_save_data("total_earned", total + income)

        return income

    def do_auto_click(self, dt, event_click_mult=1.0):
        """
        Обрабатывает автоклики (от престиж-улучшения).
        Возвращает заработанную сумму.
        """
        if self._auto_click_rate <= 0:
            return 0

        clicks_this_frame = self._auto_click_rate * dt
        earned = self._click_power * event_click_mult * clicks_this_frame

        money = self.save.get_save_data("money", 0)
        self.save.update_save_data("money", money + earned)

        total = self.save.get_save_data("total_earned", 0)
        self.save.update_save_data("total_earned", total + earned)

        return earned

    @property
    def needs_recalc(self):
        return self._needs_recalc

    def mark_dirty(self):
        """Помечает что нужен пересчёт."""
        self._needs_recalc = True


# ============================================================================
# ФОРМАТИРОВАНИЕ ЧИСЕЛ
# ============================================================================

def format_number(number, fmt=NUMBER_FORMAT_SHORT):
    """
    Форматирует число для отображения.

    fmt:
        "standard" — 1,000,000
        "short"    — 1.00M
        "scientific" — 1.00e6
    """
    if number is None:
        return "$0"

    if fmt == NUMBER_FORMAT_STANDARD:
        return _format_standard(number)
    elif fmt == NUMBER_FORMAT_SCIENTIFIC:
        return _format_scientific(number)
    else:  # short
        return _format_short(number)


def format_money(number, fmt=NUMBER_FORMAT_SHORT):
    """Форматирует число как деньги с символом $."""
    return f"${format_number(number, fmt)}"


def _format_standard(number):
    """Стандартный формат: 1,000,000"""
    if abs(number) < 1:
        return f"{number:.2f}"
    if abs(number) < 1000:
        if number == int(number):
            return f"{int(number):,}"
        return f"{number:,.1f}"
    return f"{number:,.0f}"


def _format_short(number):
    """Сокращённый формат: 1.00M"""
    if abs(number) < 1:
        return f"{number:.2f}"
    if abs(number) < 1000:
        if number == int(number):
            return str(int(number))
        return f"{number:.1f}"

    # Определяем суффикс
    tier = 0
    n = abs(number)
    while n >= 1000 and tier < len(NUMBER_SUFFIXES) - 1:
        n /= 1000
        tier += 1

    sign = "-" if number < 0 else ""

    if n >= 100:
        return f"{sign}{n:.0f}{NUMBER_SUFFIXES[tier]}"
    elif n >= 10:
        return f"{sign}{n:.1f}{NUMBER_SUFFIXES[tier]}"
    else:
        return f"{sign}{n:.2f}{NUMBER_SUFFIXES[tier]}"


def _format_scientific(number):
    """Научный формат: 1.00e6"""
    if abs(number) < 1000:
        if abs(number) < 1:
            return f"{number:.2f}"
        if number == int(number):
            return str(int(number))
        return f"{number:.1f}"
    return f"{number:.2e}"


def format_time(seconds):
    """Форматирует время в строку."""
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def format_percent(value):
    """Форматирует число как процент."""
    return f"{value * 100:.0f}%"
