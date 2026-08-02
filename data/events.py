"""
botyaraclick - data/events.py
Все рандомные игровые события.

Типы ивентов:
- "golden"     — летящий объект, нужно кликнуть за N секунд
- "buff"       — временный положительный эффект
- "debuff"     — временный отрицательный эффект
- "instant"    — мгновенный эффект (дать/забрать деньги)
- "choice"     — мини-квест с выбором
- "challenge"  — испытание (кликай N раз за M секунд)

Поля эффектов:
- "click_mult"    — множитель к $/клик
- "passive_mult"  — множитель к $/сек
- "money_percent" — % от текущего баланса (+/-)
- "money_flat"    — фиксированная сумма
- "duration"      — длительность в секундах
"""


EVENTS = [
    # ========================================================================
    # ЗОЛОТЫЕ ОБЪЕКТЫ (нужно успеть кликнуть)
    # ========================================================================
    {
        "id": "golden_bug",
        "type": "golden",
        "rarity": "common",
        "catch_time": 3.0,
        "reward_type": "click_mult_instant",
        "reward_value": 100,
        "min_era": 0,
        "icon": "🐛",
    },
    {
        "id": "golden_bitcoin",
        "type": "golden",
        "rarity": "uncommon",
        "catch_time": 2.5,
        "reward_type": "money_percent",
        "reward_value": 0.10,
        "min_era": 1,
        "icon": "₿",
    },
    {
        "id": "golden_ufo",
        "type": "golden",
        "rarity": "rare",
        "catch_time": 2.0,
        "reward_type": "click_mult_instant",
        "reward_value": 500,
        "min_era": 2,
        "icon": "🛸",
    },
    {
        "id": "golden_diamond",
        "type": "golden",
        "rarity": "epic",
        "catch_time": 1.5,
        "reward_type": "money_percent",
        "reward_value": 0.25,
        "min_era": 3,
        "icon": "💎",
    },
    {
        "id": "golden_rocket",
        "type": "golden",
        "rarity": "legendary",
        "catch_time": 1.0,
        "reward_type": "money_percent",
        "reward_value": 0.50,
        "min_era": 5,
        "icon": "🚀",
    },

    # ========================================================================
    # ПОЛОЖИТЕЛЬНЫЕ БАФФЫ
    # ========================================================================
    {
        "id": "bull_market",
        "type": "buff",
        "rarity": "common",
        "effect": "passive_mult",
        "effect_value": 3.0,
        "duration": 30,
        "min_era": 0,
        "icon": "📈",
    },
    {
        "id": "coffee_break",
        "type": "buff",
        "rarity": "common",
        "effect": "click_mult",
        "effect_value": 5.0,
        "duration": 15,
        "min_era": 0,
        "icon": "☕",
    },
    {
        "id": "viral_post",
        "type": "buff",
        "rarity": "uncommon",
        "effect": "passive_mult",
        "effect_value": 2.0,
        "duration": 60,
        "min_era": 1,
        "icon": "🔥",
    },
    {
        "id": "genius_idea",
        "type": "buff",
        "rarity": "rare",
        "effect": "click_mult",
        "effect_value": 10.0,
        "duration": 20,
        "min_era": 1,
        "icon": "💡",
    },
    {
        "id": "investor_gift",
        "type": "buff",
        "rarity": "uncommon",
        "effect": "passive_mult",
        "effect_value": 5.0,
        "duration": 15,
        "min_era": 2,
        "icon": "🎁",
    },
    {
        "id": "tiktok_trend",
        "type": "buff",
        "rarity": "common",
        "effect": "passive_mult",
        "effect_value": 3.0,
        "duration": 30,
        "min_era": 1,
        "icon": "📱",
    },
    {
        "id": "energy_drink",
        "type": "buff",
        "rarity": "common",
        "effect": "click_mult",
        "effect_value": 3.0,
        "duration": 30,
        "min_era": 0,
        "icon": "⚡",
    },
    {
        "id": "lucky_day",
        "type": "buff",
        "rarity": "rare",
        "effect": "click_mult",
        "effect_value": 7.0,
        "duration": 25,
        "min_era": 2,
        "icon": "🍀",
    },
    {
        "id": "government_grant",
        "type": "buff",
        "rarity": "rare",
        "effect": "passive_mult",
        "effect_value": 4.0,
        "duration": 45,
        "min_era": 2,
        "icon": "🏛️",
    },
    {
        "id": "ai_boost",
        "type": "buff",
        "rarity": "epic",
        "effect": "passive_mult",
        "effect_value": 10.0,
        "duration": 15,
        "min_era": 4,
        "icon": "🤖",
    },

    # ========================================================================
    # ОТРИЦАТЕЛЬНЫЕ ДЕБАФФЫ
    # ========================================================================
    {
        "id": "market_crisis",
        "type": "debuff",
        "rarity": "common",
        "effect": "passive_mult",
        "effect_value": 0.7,
        "duration": 20,
        "min_era": 1,
        "icon": "📉",
    },
    {
        "id": "production_bug",
        "type": "debuff",
        "rarity": "common",
        "effect": "click_mult",
        "effect_value": 0.5,
        "duration": 15,
        "min_era": 0,
        "icon": "🐛",
    },
    {
        "id": "tax_audit",
        "type": "instant",
        "rarity": "uncommon",
        "effect": "money_percent",
        "effect_value": -0.05,
        "duration": 0,
        "min_era": 1,
        "icon": "💸",
    },
    {
        "id": "power_outage",
        "type": "debuff",
        "rarity": "uncommon",
        "effect": "passive_mult",
        "effect_value": 0.0,
        "duration": 10,
        "min_era": 1,
        "icon": "🔌",
    },
    {
        "id": "ddos_attack",
        "type": "debuff",
        "rarity": "rare",
        "effect": "passive_mult",
        "effect_value": 0.3,
        "duration": 15,
        "min_era": 2,
        "icon": "🦠",
    },
    {
        "id": "employee_strike",
        "type": "debuff",
        "rarity": "uncommon",
        "effect": "passive_mult",
        "effect_value": 0.5,
        "duration": 25,
        "min_era": 2,
        "icon": "✊",
    },
    {
        "id": "server_fire",
        "type": "debuff",
        "rarity": "rare",
        "effect": "passive_mult",
        "effect_value": 0.2,
        "duration": 12,
        "min_era": 3,
        "icon": "🔥",
    },

    # ========================================================================
    # МГНОВЕННЫЕ ЭФФЕКТЫ
    # ========================================================================
    {
        "id": "lottery_win",
        "type": "instant",
        "rarity": "rare",
        "effect": "money_percent",
        "effect_value": 0.15,
        "duration": 0,
        "min_era": 1,
        "icon": "🎰",
    },
    {
        "id": "donation",
        "type": "instant",
        "rarity": "uncommon",
        "effect": "money_percent",
        "effect_value": 0.05,
        "duration": 0,
        "min_era": 0,
        "icon": "💝",
    },

    # ========================================================================
    # ВЫБОР (Мини-квесты)
    # ========================================================================
    {
        "id": "investor_deal",
        "type": "choice",
        "rarity": "uncommon",
        "risk_percent": 0.10,
        "win_chance": 0.50,
        "win_multiplier": 2.0,
        "min_era": 1,
        "icon": "🤝",
    },
    {
        "id": "tender",
        "type": "choice",
        "rarity": "uncommon",
        "risk_percent": 0.08,
        "win_chance": 0.60,
        "win_multiplier": 3.0,
        "min_era": 2,
        "icon": "📋",
    },
    {
        "id": "crypto_investment",
        "type": "choice",
        "rarity": "rare",
        "risk_percent": 0.15,
        "win_chance": 0.40,
        "win_multiplier": 4.0,
        "min_era": 2,
        "icon": "🪙",
    },
    {
        "id": "startup_acquisition",
        "type": "choice",
        "rarity": "rare",
        "risk_percent": 0.20,
        "win_chance": 0.45,
        "win_multiplier": 3.5,
        "min_era": 3,
        "icon": "🏢",
    },

    # ========================================================================
    # ИСПЫТАНИЯ (Challenge)
    # ========================================================================
    {
        "id": "hackathon",
        "type": "challenge",
        "rarity": "uncommon",
        "required_clicks": 50,
        "time_limit": 10,
        "reward_type": "money_percent",
        "reward_value": 0.08,
        "min_era": 1,
        "icon": "🏆",
    },
    {
        "id": "speed_coding",
        "type": "challenge",
        "rarity": "rare",
        "required_clicks": 80,
        "time_limit": 10,
        "reward_type": "money_percent",
        "reward_value": 0.15,
        "min_era": 2,
        "icon": "⌨️",
    },
    {
        "id": "server_emergency",
        "type": "challenge",
        "rarity": "uncommon",
        "required_clicks": 30,
        "time_limit": 5,
        "reward_type": "money_percent",
        "reward_value": 0.05,
        "min_era": 1,
        "icon": "🚨",
    },
]


# Веса редкости для выбора ивентов
RARITY_WEIGHTS = {
    "common": 40,
    "uncommon": 30,
    "rare": 20,
    "epic": 8,
    "legendary": 2,
}


def get_available_events(current_era: int) -> list:
    """Возвращает список ивентов, доступных для текущей эры."""
    return [e for e in EVENTS if e["min_era"] <= current_era]


def get_event_weight(event: dict) -> int:
    """Возвращает вес ивента для рандомного выбора."""
    return RARITY_WEIGHTS.get(event.get("rarity", "common"), 10)
