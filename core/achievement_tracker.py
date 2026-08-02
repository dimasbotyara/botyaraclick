"""
botyaraclick - core/achievement_tracker.py
Трекер достижений — проверяет условия и выдаёт достижения.
"""

import time
import math

from data.achievements import ACHIEVEMENTS, ALL_ACHIEVEMENTS


class AchievementTracker:
    """
    Трекер достижений.
    Проверяет условия каждый кадр и уведомляет о новых.
    """

    def __init__(self, save_manager):
        self.save_manager = save_manager
        self.newly_unlocked = []  # буфер новых достижений для уведомлений

        # Трекеры для скорости кликов
        self._click_times = []  # timestamps последних кликов
        self._current_cps = 0   # кликов в секунду

        # Трекер для "кликов без паузы"
        self._last_click_time = 0
        self._consecutive_clicks = 0
        self._max_consecutive = 0

    def register_click(self):
        """Регистрирует клик для трекинга скорости."""
        now = time.time()
        self._click_times.append(now)

        # Считаем кликов в секунду (за последнюю секунду)
        cutoff = now - 1.0
        self._click_times = [t for t in self._click_times if t > cutoff]
        self._current_cps = len(self._click_times)

        # Трекер consecutive clicks
        if self._last_click_time > 0 and now - self._last_click_time < 0.5:
            self._consecutive_clicks += 1
        else:
            self._consecutive_clicks = 1

        self._last_click_time = now
        self._max_consecutive = max(self._max_consecutive, self._consecutive_clicks)

        # Обновляем в save
        self.save_manager.update_save_data(
            "clicks_without_pause", self._consecutive_clicks
        )

    def check_all(self, game_state):
        """
        Проверяет все условия достижений.

        game_state: dict с ключами:
            - total_earned
            - total_clicks
            - total_purchases
            - current_era
            - play_time
            - golden_caught
            - deals_won
            - deals_lost
            - debuffs_survived
            - challenges_completed
            - prestige_count
            - money
            - themes_owned (количество)
        """
        self.newly_unlocked.clear()

        for achievement in ACHIEVEMENTS:
            aid = achievement["id"]

            # Уже получено?
            if self.save_manager.has_achievement(aid):
                continue

            # Проверяем условие
            if self._check_condition(achievement, game_state):
                self.save_manager.add_achievement(aid)
                self.newly_unlocked.append(achievement)

    def _check_condition(self, achievement, game_state):
        """Проверяет условие одного достижения."""
        ctype = achievement["condition_type"]
        cvalue = achievement["condition_value"]

        if ctype == "total_earned":
            return game_state.get("total_earned", 0) >= cvalue

        elif ctype == "total_clicks":
            return game_state.get("total_clicks", 0) >= cvalue

        elif ctype == "total_purchases":
            return game_state.get("total_purchases", 0) >= cvalue

        elif ctype == "unique_upgrades":
            upgrades = self.save_manager.get_save_data("upgrades", {})
            unique = sum(1 for v in upgrades.values() if v > 0)
            return unique >= cvalue

        elif ctype == "clicks_per_second":
            return self._current_cps >= cvalue

        elif ctype == "era_reached":
            return game_state.get("current_era", 0) >= cvalue

        elif ctype == "golden_caught":
            return game_state.get("golden_caught", 0) >= cvalue

        elif ctype == "deals_won":
            return game_state.get("deals_won", 0) >= cvalue

        elif ctype == "debuffs_survived":
            return game_state.get("debuffs_survived", 0) >= cvalue

        elif ctype == "challenges_completed":
            return game_state.get("challenges_completed", 0) >= cvalue

        elif ctype == "play_time":
            return game_state.get("play_time", 0) >= cvalue

        elif ctype == "clicks_without_pause":
            return self._consecutive_clicks >= cvalue

        elif ctype == "money_without_buying":
            return game_state.get("money_earned_without_buying", 0) >= cvalue

        elif ctype == "click_at_midnight":
            now = time.localtime()
            return now.tm_hour == 0 and now.tm_min == 0

        elif ctype == "themes_owned":
            return game_state.get("themes_owned", 1) >= cvalue

        elif ctype == "prestige_count":
            return game_state.get("prestige_count", 0) >= cvalue

        elif ctype == "deals_lost":
            return game_state.get("deals_lost_in_row", 0) >= cvalue

        return False

    def get_achievement_bonuses(self):
        """
        Возвращает суммарные бонусы от всех полученных достижений.
        Возвращает dict:
        {
            "all_multiplier": float,
            "click_multiplier": float,
            "passive_multiplier": float,
            "discount": float,
            "crit_chance": float,
        }
        """
        bonuses = {
            "all_multiplier": 0.0,
            "click_multiplier": 0.0,
            "passive_multiplier": 0.0,
            "discount": 0.0,
            "crit_chance": 0.0,
        }

        unlocked = self.save_manager.get_save_data("achievements", [])

        for aid in unlocked:
            ach = ALL_ACHIEVEMENTS.get(aid)
            if ach and ach["bonus_type"]:
                bonus_type = ach["bonus_type"]
                bonus_value = ach["bonus_value"]
                if bonus_type in bonuses:
                    bonuses[bonus_type] += bonus_value

        # Проверяем престиж-бонус "удвоение бонусов достижений"
        ach_mult = self.save_manager.get_prestige_upgrade_count(
            "prestige_double_achievement"
        )
        if ach_mult > 0:
            for key in bonuses:
                bonuses[key] *= 2.0

        return bonuses

    def get_progress(self, achievement_id, game_state):
        """
        Возвращает прогресс достижения (current, target).
        Для отображения прогресс-бара.
        """
        ach = ALL_ACHIEVEMENTS.get(achievement_id)
        if not ach:
            return 0, 1

        ctype = ach["condition_type"]
        target = ach["condition_value"]

        if ctype == "total_earned":
            current = game_state.get("total_earned", 0)
        elif ctype == "total_clicks":
            current = game_state.get("total_clicks", 0)
        elif ctype == "total_purchases":
            current = game_state.get("total_purchases", 0)
        elif ctype == "era_reached":
            current = game_state.get("current_era", 0)
        elif ctype == "golden_caught":
            current = game_state.get("golden_caught", 0)
        elif ctype == "deals_won":
            current = game_state.get("deals_won", 0)
        elif ctype == "debuffs_survived":
            current = game_state.get("debuffs_survived", 0)
        elif ctype == "challenges_completed":
            current = game_state.get("challenges_completed", 0)
        elif ctype == "play_time":
            current = game_state.get("play_time", 0)
        elif ctype == "prestige_count":
            current = game_state.get("prestige_count", 0)
        elif ctype == "themes_owned":
            current = game_state.get("themes_owned", 1)
        elif ctype == "clicks_per_second":
            current = self._current_cps
        else:
            current = 0

        return min(current, target), target

    def get_unlocked_count(self):
        """Количество разблокированных достижений."""
        unlocked = self.save_manager.get_save_data("achievements", [])
        return len(unlocked)

    def get_total_count(self):
        """Общее количество достижений."""
        return len(ACHIEVEMENTS)

    def get_unlocked_ids(self):
        """Список ID разблокированных достижений."""
        return self.save_manager.get_save_data("achievements", [])
