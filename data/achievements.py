"""
botyaraclick - data/achievements.py
Все 50 достижений в игре.

Каждое достижение содержит:
- id: уникальный идентификатор
- category: категория достижения
- condition_type: тип условия проверки
- condition_value: значение условия
- bonus_type: тип бонуса за получение (или None)
- bonus_value: значение бонуса
- secret: является ли секретным (не видно до получения)
"""


ACHIEVEMENTS = [
    # ========================================================================
    # 💰 БОГАТСТВО (10 штук)
    # ========================================================================
    {
        "id": "first_hundred",
        "category": "wealth",
        "condition_type": "total_earned",
        "condition_value": 100,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.01,
        "secret": False,
    },
    {
        "id": "first_thousand",
        "category": "wealth",
        "condition_type": "total_earned",
        "condition_value": 1_000,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.02,
        "secret": False,
    },
    {
        "id": "first_ten_k",
        "category": "wealth",
        "condition_type": "total_earned",
        "condition_value": 10_000,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.02,
        "secret": False,
    },
    {
        "id": "first_hundred_k",
        "category": "wealth",
        "condition_type": "total_earned",
        "condition_value": 100_000,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.03,
        "secret": False,
    },
    {
        "id": "first_million",
        "category": "wealth",
        "condition_type": "total_earned",
        "condition_value": 1_000_000,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.03,
        "secret": False,
    },
    {
        "id": "ten_million",
        "category": "wealth",
        "condition_type": "total_earned",
        "condition_value": 10_000_000,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.04,
        "secret": False,
    },
    {
        "id": "hundred_million",
        "category": "wealth",
        "condition_type": "total_earned",
        "condition_value": 100_000_000,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.04,
        "secret": False,
    },
    {
        "id": "billionaire",
        "category": "wealth",
        "condition_type": "total_earned",
        "condition_value": 1_000_000_000,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.05,
        "secret": False,
    },
    {
        "id": "trillionaire",
        "category": "wealth",
        "condition_type": "total_earned",
        "condition_value": 1_000_000_000_000,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.05,
        "secret": False,
    },
    {
        "id": "quadrillionaire",
        "category": "wealth",
        "condition_type": "total_earned",
        "condition_value": 1_000_000_000_000_000,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.06,
        "secret": False,
    },

    # ========================================================================
    # 🖱️ КЛИКИ (8 штук)
    # ========================================================================
    {
        "id": "first_click",
        "category": "clicks",
        "condition_type": "total_clicks",
        "condition_value": 1,
        "bonus_type": None,
        "bonus_value": 0,
        "secret": False,
    },
    {
        "id": "hundred_clicks",
        "category": "clicks",
        "condition_type": "total_clicks",
        "condition_value": 100,
        "bonus_type": "click_multiplier",
        "bonus_value": 0.02,
        "secret": False,
    },
    {
        "id": "thousand_clicks",
        "category": "clicks",
        "condition_type": "total_clicks",
        "condition_value": 1_000,
        "bonus_type": "click_multiplier",
        "bonus_value": 0.03,
        "secret": False,
    },
    {
        "id": "click_maniac",
        "category": "clicks",
        "condition_type": "total_clicks",
        "condition_value": 10_000,
        "bonus_type": "click_multiplier",
        "bonus_value": 0.05,
        "secret": False,
    },
    {
        "id": "clickosaurus",
        "category": "clicks",
        "condition_type": "total_clicks",
        "condition_value": 50_000,
        "bonus_type": "click_multiplier",
        "bonus_value": 0.05,
        "secret": False,
    },
    {
        "id": "click_god",
        "category": "clicks",
        "condition_type": "total_clicks",
        "condition_value": 100_000,
        "bonus_type": "click_multiplier",
        "bonus_value": 0.08,
        "secret": False,
    },
    {
        "id": "click_legend",
        "category": "clicks",
        "condition_type": "total_clicks",
        "condition_value": 500_000,
        "bonus_type": "click_multiplier",
        "bonus_value": 0.10,
        "secret": False,
    },
    {
        "id": "click_immortal",
        "category": "clicks",
        "condition_type": "total_clicks",
        "condition_value": 1_000_000,
        "bonus_type": "click_multiplier",
        "bonus_value": 0.15,
        "secret": False,
    },

    # ========================================================================
    # 🛒 ПОКУПКИ (6 штук)
    # ========================================================================
    {
        "id": "first_purchase",
        "category": "purchases",
        "condition_type": "total_purchases",
        "condition_value": 1,
        "bonus_type": None,
        "bonus_value": 0,
        "secret": False,
    },
    {
        "id": "shopaholic",
        "category": "purchases",
        "condition_type": "total_purchases",
        "condition_value": 10,
        "bonus_type": "discount",
        "bonus_value": 0.01,
        "secret": False,
    },
    {
        "id": "collector",
        "category": "purchases",
        "condition_type": "total_purchases",
        "condition_value": 25,
        "bonus_type": "discount",
        "bonus_value": 0.02,
        "secret": False,
    },
    {
        "id": "big_spender",
        "category": "purchases",
        "condition_type": "total_purchases",
        "condition_value": 50,
        "bonus_type": "discount",
        "bonus_value": 0.03,
        "secret": False,
    },
    {
        "id": "buyer_of_all",
        "category": "purchases",
        "condition_type": "total_purchases",
        "condition_value": 100,
        "bonus_type": "discount",
        "bonus_value": 0.04,
        "secret": False,
    },
    {
        "id": "full_collection",
        "category": "purchases",
        "condition_type": "unique_upgrades",
        "condition_value": 176,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.25,
        "secret": False,
    },

    # ========================================================================
    # ⚡ СКОРОСТЬ (4 штуки)
    # ========================================================================
    {
        "id": "fast_fingers",
        "category": "speed",
        "condition_type": "clicks_per_second",
        "condition_value": 8,
        "bonus_type": "click_multiplier",
        "bonus_value": 0.03,
        "secret": False,
    },
    {
        "id": "machine_gun",
        "category": "speed",
        "condition_type": "clicks_per_second",
        "condition_value": 15,
        "bonus_type": "click_multiplier",
        "bonus_value": 0.05,
        "secret": False,
    },
    {
        "id": "inhuman_speed",
        "category": "speed",
        "condition_type": "clicks_per_second",
        "condition_value": 25,
        "bonus_type": "click_multiplier",
        "bonus_value": 0.08,
        "secret": False,
    },
    {
        "id": "light_speed",
        "category": "speed",
        "condition_type": "clicks_per_second",
        "condition_value": 35,
        "bonus_type": "click_multiplier",
        "bonus_value": 0.12,
        "secret": False,
    },

    # ========================================================================
    # 🏢 ПРОГРЕСС - ЭРЫ (6 штук)
    # ========================================================================
    {
        "id": "from_garage",
        "category": "progress",
        "condition_type": "era_reached",
        "condition_value": 1,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.03,
        "secret": False,
    },
    {
        "id": "startup_founder",
        "category": "progress",
        "condition_type": "era_reached",
        "condition_value": 2,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.04,
        "secret": False,
    },
    {
        "id": "businessman",
        "category": "progress",
        "condition_type": "era_reached",
        "condition_value": 3,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.05,
        "secret": False,
    },
    {
        "id": "tycoon",
        "category": "progress",
        "condition_type": "era_reached",
        "condition_value": 4,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.06,
        "secret": False,
    },
    {
        "id": "world_domination",
        "category": "progress",
        "condition_type": "era_reached",
        "condition_value": 5,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.08,
        "secret": False,
    },
    {
        "id": "to_the_stars",
        "category": "progress",
        "condition_type": "era_reached",
        "condition_value": 6,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.10,
        "secret": False,
    },

    # ========================================================================
    # 🎲 ИВЕНТЫ (6 штук)
    # ========================================================================
    {
        "id": "lucky_catch",
        "category": "events",
        "condition_type": "golden_caught",
        "condition_value": 1,
        "bonus_type": "crit_chance",
        "bonus_value": 0.01,
        "secret": False,
    },
    {
        "id": "golden_hunter",
        "category": "events",
        "condition_type": "golden_caught",
        "condition_value": 10,
        "bonus_type": "crit_chance",
        "bonus_value": 0.02,
        "secret": False,
    },
    {
        "id": "event_master",
        "category": "events",
        "condition_type": "golden_caught",
        "condition_value": 50,
        "bonus_type": "crit_chance",
        "bonus_value": 0.03,
        "secret": False,
    },
    {
        "id": "risky_player",
        "category": "events",
        "condition_type": "deals_won",
        "condition_value": 5,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.03,
        "secret": False,
    },
    {
        "id": "survivor",
        "category": "events",
        "condition_type": "debuffs_survived",
        "condition_value": 10,
        "bonus_type": "passive_multiplier",
        "bonus_value": 0.03,
        "secret": False,
    },
    {
        "id": "challenge_champion",
        "category": "events",
        "condition_type": "challenges_completed",
        "condition_value": 10,
        "bonus_type": "click_multiplier",
        "bonus_value": 0.05,
        "secret": False,
    },

    # ========================================================================
    # 🕐 ВРЕМЯ (4 штуки)
    # ========================================================================
    {
        "id": "newbie",
        "category": "time",
        "condition_type": "play_time",
        "condition_value": 600,
        "bonus_type": None,
        "bonus_value": 0,
        "secret": False,
    },
    {
        "id": "enthusiast",
        "category": "time",
        "condition_type": "play_time",
        "condition_value": 3_600,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.02,
        "secret": False,
    },
    {
        "id": "dedicated",
        "category": "time",
        "condition_type": "play_time",
        "condition_value": 18_000,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.03,
        "secret": False,
    },
    {
        "id": "madman",
        "category": "time",
        "condition_type": "play_time",
        "condition_value": 86_400,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.05,
        "secret": False,
    },

    # ========================================================================
    # 🔥 СЕКРЕТНЫЕ (6 штук)
    # ========================================================================
    {
        "id": "secret_marathon",
        "category": "secret",
        "condition_type": "clicks_without_pause",
        "condition_value": 1000,
        "bonus_type": "click_multiplier",
        "bonus_value": 0.10,
        "secret": True,
    },
    {
        "id": "secret_hoarder",
        "category": "secret",
        "condition_type": "money_without_buying",
        "condition_value": 1_000_000,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.05,
        "secret": True,
    },
    {
        "id": "secret_midnight",
        "category": "secret",
        "condition_type": "click_at_midnight",
        "condition_value": 1,
        "bonus_type": "crit_chance",
        "bonus_value": 0.03,
        "secret": True,
    },
    {
        "id": "secret_all_themes",
        "category": "secret",
        "condition_type": "themes_owned",
        "condition_value": 12,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.10,
        "secret": True,
    },
    {
        "id": "secret_prestige_3",
        "category": "secret",
        "condition_type": "prestige_count",
        "condition_value": 3,
        "bonus_type": "all_multiplier",
        "bonus_value": 0.08,
        "secret": True,
    },
    {
        "id": "secret_unlucky",
        "category": "secret",
        "condition_type": "deals_lost",
        "condition_value": 5,
        "bonus_type": "crit_chance",
        "bonus_value": 0.05,
        "secret": True,
    },
]


# Категории достижений для отображения
ACHIEVEMENT_CATEGORIES = [
    "wealth", "clicks", "purchases", "speed",
    "progress", "events", "time", "secret"
]


# Словарь для быстрого доступа
ALL_ACHIEVEMENTS = {a["id"]: a for a in ACHIEVEMENTS}


def get_achievements_by_category(category: str) -> list:
    """Возвращает достижения по категории."""
    return [a for a in ACHIEVEMENTS if a["category"] == category]
