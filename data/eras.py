"""
botyaraclick - data/eras.py
Определения эр развития (этапов прогрессии).
"""


ERAS = [
    {
        "id": "garage",
        "unlock_money": 0,
        "bg_colors": {
            "top": (25, 20, 18),
            "bottom": (40, 35, 30),
        },
        "ambient_particles": "dust",
        "click_object_color": (120, 120, 130),
        "click_object_glow": (80, 80, 100),
    },
    {
        "id": "home_office",
        "unlock_money": 10_000,
        "bg_colors": {
            "top": (30, 35, 50),
            "bottom": (20, 25, 40),
        },
        "ambient_particles": "none",
        "click_object_color": (100, 140, 200),
        "click_object_glow": (60, 100, 180),
    },
    {
        "id": "startup",
        "unlock_money": 500_000,
        "bg_colors": {
            "top": (35, 45, 60),
            "bottom": (25, 30, 45),
        },
        "ambient_particles": "sparkle",
        "click_object_color": (80, 180, 120),
        "click_object_glow": (50, 150, 90),
    },
    {
        "id": "it_company",
        "unlock_money": 50_000_000,
        "bg_colors": {
            "top": (20, 30, 55),
            "bottom": (15, 20, 40),
        },
        "ambient_particles": "data_flow",
        "click_object_color": (60, 130, 220),
        "click_object_glow": (40, 100, 200),
    },
    {
        "id": "corporation",
        "unlock_money": 10_000_000_000,
        "bg_colors": {
            "top": (15, 15, 35),
            "bottom": (10, 10, 25),
        },
        "ambient_particles": "glow",
        "click_object_color": (200, 170, 50),
        "click_object_glow": (180, 150, 30),
    },
    {
        "id": "megacorp",
        "unlock_money": 5_000_000_000_000,
        "bg_colors": {
            "top": (10, 5, 25),
            "bottom": (5, 0, 15),
        },
        "ambient_particles": "energy",
        "click_object_color": (180, 50, 220),
        "click_object_glow": (150, 30, 200),
    },
    {
        "id": "space_age",
        "unlock_money": 1_000_000_000_000_000,
        "bg_colors": {
            "top": (2, 2, 15),
            "bottom": (0, 0, 5),
        },
        "ambient_particles": "stars",
        "click_object_color": (100, 200, 255),
        "click_object_glow": (50, 150, 255),
    },
]


def get_era_for_money(total_earned: float) -> int:
    """Возвращает индекс текущей эры на основе общего заработка."""
    era_index = 0
    for i, era in enumerate(ERAS):
        if total_earned >= era["unlock_money"]:
            era_index = i
    return era_index


def get_era_data(era_index: int) -> dict:
    """Возвращает данные эры по индексу."""
    if 0 <= era_index < len(ERAS):
        return ERAS[era_index]
    return ERAS[-1]
