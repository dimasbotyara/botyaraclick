"""
botyaraclick - data/prestige.py
Система престижа (перерождения).

Когда игрок заработал достаточно (total_earned >= 500M),
он может «перезапустить стартап» и получить Reputation Points (RP).
RP дают перманентные бонусы, которые сохраняются между престижами.
"""

import math
from config import PRESTIGE_THRESHOLD, PRESTIGE_FORMULA_DIVISOR


def calculate_rp(total_earned: float) -> int:
    """
    Рассчитывает количество RP, которое игрок получит при престиже.
    Формула: RP = floor(sqrt(total_earned / 500_000_000))
    """
    if total_earned < PRESTIGE_THRESHOLD:
        return 0
    return int(math.floor(math.sqrt(total_earned / PRESTIGE_FORMULA_DIVISOR)))


def calculate_rp_preview(total_earned: float, current_rp: int) -> int:
    """
    Показывает сколько НОВЫХ RP игрок получит (с учётом уже имеющихся).
    На самом деле RP не суммируются - каждый раз рассчитываются заново
    и добавляются к общему пулу.
    """
    new_rp = calculate_rp(total_earned)
    return new_rp


PRESTIGE_UPGRADES = [
    {
        "id": "prestige_income_1",
        "cost_rp": 1,
        "effect_type": "all_multiplier",
        "effect_value": 0.10,
        "max_count": -1,  # можно покупать много раз
        "prerequisite": None,
    },
    {
        "id": "prestige_click_1",
        "cost_rp": 1,
        "effect_type": "click_multiplier",
        "effect_value": 0.25,
        "max_count": -1,
        "prerequisite": None,
    },
    {
        "id": "prestige_passive_1",
        "cost_rp": 1,
        "effect_type": "passive_multiplier",
        "effect_value": 0.25,
        "max_count": -1,
        "prerequisite": None,
    },
    {
        "id": "prestige_starting_money",
        "cost_rp": 2,
        "effect_type": "starting_money",
        "effect_value": 1_000,
        "max_count": -1,
        "prerequisite": None,
    },
    {
        "id": "prestige_discount",
        "cost_rp": 3,
        "effect_type": "discount",
        "effect_value": 0.05,
        "max_count": 5,  # максимум 25% скидка
        "prerequisite": None,
    },
    {
        "id": "prestige_auto_click",
        "cost_rp": 5,
        "effect_type": "auto_click",
        "effect_value": 1.0,  # 1 автоклик в секунду
        "max_count": 10,
        "prerequisite": None,
    },
    {
        "id": "prestige_crit_chance",
        "cost_rp": 3,
        "effect_type": "crit_chance",
        "effect_value": 0.05,
        "max_count": 5,  # максимум +25% шанс крита
        "prerequisite": None,
    },
    {
        "id": "prestige_crit_mult",
        "cost_rp": 4,
        "effect_type": "crit_multiplier",
        "effect_value": 1.0,
        "max_count": 5,
        "prerequisite": None,
    },
    {
        "id": "prestige_start_era2",
        "cost_rp": 10,
        "effect_type": "starting_era",
        "effect_value": 1,
        "max_count": 1,
        "prerequisite": None,
    },
    {
        "id": "prestige_event_luck",
        "cost_rp": 5,
        "effect_type": "event_luck",
        "effect_value": 0.20,  # +20% шанс положительных ивентов
        "max_count": 3,
        "prerequisite": None,
    },
    {
        "id": "prestige_golden_time",
        "cost_rp": 4,
        "effect_type": "golden_time_bonus",
        "effect_value": 0.5,  # +0.5 сек на поимку золотых объектов
        "max_count": 4,
        "prerequisite": None,
    },
    {
        "id": "prestige_double_achievement",
        "cost_rp": 8,
        "effect_type": "achievement_bonus_mult",
        "effect_value": 1.0,  # удваивает бонусы от достижений
        "max_count": 1,
        "prerequisite": None,
    },
]

# Словарь для быстрого доступа
ALL_PRESTIGE_UPGRADES = {u["id"]: u for u in PRESTIGE_UPGRADES}


def get_prestige_upgrade_cost(upgrade_data: dict, count_owned: int) -> int:
    """Стоимость следующей покупки престиж-улучшения в RP."""
    base = upgrade_data["cost_rp"]
    # Каждая следующая покупка дорожает на 1 RP
    return base + count_owned
