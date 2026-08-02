"""
botyaraclick - core/save_manager.py
Система сохранения и загрузки.

- 5 слотов сохранения (slot_1.json .. slot_5.json)
- 1 глобальный файл (global.json) — купленные темы, настройки, язык
- Автосохранение каждые 30 секунд
- Сохранение при выходе по умолчанию
"""

import json
import os
import time
import copy

from config import SAVES_DIR, MAX_SAVE_SLOTS, GLOBAL_SAVE_FILE


class SaveManager:
    """Менеджер сохранений."""

    def __init__(self):
        os.makedirs(SAVES_DIR, exist_ok=True)

        self.current_slot = None  # номер текущего слота (1-5)
        self.global_data = self._default_global()
        self.save_data = None  # данные текущего сохранения

        # Загружаем глобальные данные при старте
        self.load_global()

    # ================================================================
    # ГЛОБАЛЬНЫЕ ДАННЫЕ (настройки, купленные темы)
    # ================================================================

    def _default_global(self):
        """Дефолтные глобальные данные."""
        return {
            "language": None,  # None = ещё не выбран (первый запуск)
            "music_volume": 0.7,
            "sfx_volume": 0.7,
            "mute_all": False,
            "number_format": "short",
            "particles_enabled": True,
            "floating_text_enabled": True,
            "unlocked_themes": ["default"],
            "last_slot": None,  # последний использованный слот
            "first_launch": True,
        }

    def _global_path(self):
        """Путь к глобальному файлу."""
        return os.path.join(SAVES_DIR, GLOBAL_SAVE_FILE)

    def load_global(self):
        """Загружает глобальные данные."""
        path = self._global_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                # Мержим с дефолтными (на случай новых полей)
                default = self._default_global()
                default.update(loaded)
                self.global_data = default
            except (json.JSONDecodeError, IOError, OSError) as e:
                print(f"[SaveManager] Error loading global data: {e}")
                self.global_data = self._default_global()
        else:
            self.global_data = self._default_global()

    def save_global(self):
        """Сохраняет глобальные данные."""
        path = self._global_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.global_data, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            print(f"[SaveManager] Error saving global data: {e}")

    def is_first_launch(self):
        """Проверяет, первый ли это запуск."""
        return self.global_data.get("first_launch", True)

    def set_first_launch_done(self):
        """Отмечает что первый запуск прошёл."""
        self.global_data["first_launch"] = False
        self.save_global()

    def get_language(self):
        """Возвращает выбранный язык (или None если не выбран)."""
        return self.global_data.get("language", None)

    def set_language(self, lang_code):
        """Устанавливает язык."""
        self.global_data["language"] = lang_code
        self.save_global()

    def get_setting(self, key, default=None):
        """Получает глобальную настройку."""
        return self.global_data.get(key, default)

    def set_setting(self, key, value):
        """Устанавливает глобальную настройку."""
        self.global_data[key] = value
        self.save_global()

    def unlock_theme(self, theme_id):
        """Разблокирует тему (глобально)."""
        themes = self.global_data.get("unlocked_themes", ["default"])
        if theme_id not in themes:
            themes.append(theme_id)
            self.global_data["unlocked_themes"] = themes
            self.save_global()

    def is_theme_unlocked(self, theme_id):
        """Проверяет, разблокирована ли тема."""
        return theme_id in self.global_data.get("unlocked_themes", ["default"])

    def get_unlocked_themes(self):
        """Возвращает список разблокированных тем."""
        return self.global_data.get("unlocked_themes", ["default"])

    # ================================================================
    # СЛОТЫ СОХРАНЕНИЯ
    # ================================================================

    def _slot_path(self, slot_num):
        """Путь к файлу слота."""
        return os.path.join(SAVES_DIR, f"slot_{slot_num}.json")

    def _default_save(self):
        """Дефолтные данные нового сохранения."""
        return {
            "money": 0.0,
            "total_earned": 0.0,
            "total_clicks": 0,
            "total_purchases": 0,

            # Улучшения: {upgrade_id: count}
            "upgrades": {},

            # Достижения: [achievement_id, ...]
            "achievements": [],

            # Текущая эра
            "current_era": 0,

            # Текущая тема (для этого сохранения)
            "current_theme": "default",

            # Время игры (секунды)
            "play_time": 0.0,

            # Статистика ивентов
            "golden_caught": 0,
            "golden_missed": 0,
            "deals_won": 0,
            "deals_lost": 0,
            "challenges_completed": 0,
            "challenges_failed": 0,
            "debuffs_survived": 0,

            # Престиж
            "prestige_count": 0,
            "total_rp": 0,
            "available_rp": 0,
            "prestige_upgrades": {},  # {prestige_upgrade_id: count}

            # Секретные трекеры
            "clicks_without_pause": 0,
            "money_earned_without_buying": 0.0,
            "deals_lost_in_row": 0,

            # Метаданные
            "created_at": None,
            "last_saved_at": None,
            "version": "1.0.0",
        }

    def slot_exists(self, slot_num):
        """Проверяет, существует ли сохранение в слоте."""
        return os.path.exists(self._slot_path(slot_num))

    def get_slot_info(self, slot_num):
        """
        Возвращает краткую информацию о слоте для отображения.
        Возвращает None если слот пуст.
        """
        path = self._slot_path(slot_num)
        if not os.path.exists(path):
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                "slot": slot_num,
                "money": data.get("money", 0),
                "total_earned": data.get("total_earned", 0),
                "play_time": data.get("play_time", 0),
                "current_era": data.get("current_era", 0),
                "prestige_count": data.get("prestige_count", 0),
                "last_saved_at": data.get("last_saved_at", ""),
                "total_clicks": data.get("total_clicks", 0),
            }
        except (json.JSONDecodeError, IOError, OSError):
            return None

    def get_all_slots_info(self):
        """Возвращает информацию обо всех слотах."""
        slots = []
        for i in range(1, MAX_SAVE_SLOTS + 1):
            info = self.get_slot_info(i)
            slots.append({
                "slot": i,
                "info": info,
                "exists": info is not None,
            })
        return slots

    def new_game(self, slot_num):
        """Создаёт новое сохранение в слоте."""
        self.save_data = self._default_save()
        self.save_data["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.current_slot = slot_num
        self.global_data["last_slot"] = slot_num
        self.save_current()
        self.save_global()
        return self.save_data

    def load_game(self, slot_num):
        """Загружает сохранение из слота."""
        path = self._slot_path(slot_num)
        if not os.path.exists(path):
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)

            # Мержим с дефолтными данными (для совместимости версий)
            default = self._default_save()
            default.update(loaded)
            self.save_data = default
            self.current_slot = slot_num
            self.global_data["last_slot"] = slot_num
            self.save_global()
            return self.save_data

        except (json.JSONDecodeError, IOError, OSError) as e:
            print(f"[SaveManager] Error loading slot {slot_num}: {e}")
            return None

    def save_current(self):
        """Сохраняет текущее сохранение."""
        if self.save_data is None or self.current_slot is None:
            return False

        self.save_data["last_saved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

        path = self._slot_path(self.current_slot)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.save_data, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError) as e:
            print(f"[SaveManager] Error saving slot {self.current_slot}: {e}")
            return False

    def delete_slot(self, slot_num):
        """Удаляет сохранение из слота."""
        path = self._slot_path(slot_num)
        if os.path.exists(path):
            try:
                os.remove(path)
                if self.current_slot == slot_num:
                    self.current_slot = None
                    self.save_data = None
                return True
            except OSError as e:
                print(f"[SaveManager] Error deleting slot {slot_num}: {e}")
                return False
        return True

    def has_any_save(self):
        """Проверяет, есть ли хотя бы одно сохранение."""
        for i in range(1, MAX_SAVE_SLOTS + 1):
            if self.slot_exists(i):
                return True
        return False

    # ================================================================
    # ОБНОВЛЕНИЕ ДАННЫХ СОХРАНЕНИЯ
    # ================================================================

    def update_save_data(self, key, value):
        """Обновляет поле в текущем сохранении."""
        if self.save_data is not None:
            self.save_data[key] = value

    def get_save_data(self, key, default=None):
        """Получает поле из текущего сохранения."""
        if self.save_data is not None:
            return self.save_data.get(key, default)
        return default

    def increment_stat(self, key, amount=1):
        """Увеличивает числовую статистику."""
        if self.save_data is not None:
            current = self.save_data.get(key, 0)
            self.save_data[key] = current + amount

    def add_achievement(self, achievement_id):
        """Добавляет достижение."""
        if self.save_data is None:
            return
        achievements = self.save_data.get("achievements", [])
        if achievement_id not in achievements:
            achievements.append(achievement_id)
            self.save_data["achievements"] = achievements

    def has_achievement(self, achievement_id):
        """Проверяет, есть ли достижение."""
        if self.save_data is None:
            return False
        return achievement_id in self.save_data.get("achievements", [])

    def get_upgrade_count(self, upgrade_id):
        """Возвращает количество купленных единиц улучшения."""
        if self.save_data is None:
            return 0
        return self.save_data.get("upgrades", {}).get(upgrade_id, 0)

    def set_upgrade_count(self, upgrade_id, count):
        """Устанавливает количество улучшения."""
        if self.save_data is None:
            return
        if "upgrades" not in self.save_data:
            self.save_data["upgrades"] = {}
        self.save_data["upgrades"][upgrade_id] = count

    def get_prestige_upgrade_count(self, upgrade_id):
        """Возвращает количество престиж-улучшений."""
        if self.save_data is None:
            return 0
        return self.save_data.get("prestige_upgrades", {}).get(upgrade_id, 0)

    def set_prestige_upgrade_count(self, upgrade_id, count):
        """Устанавливает количество престиж-улучшений."""
        if self.save_data is None:
            return
        if "prestige_upgrades" not in self.save_data:
            self.save_data["prestige_upgrades"] = {}
        self.save_data["prestige_upgrades"][upgrade_id] = count

    def do_prestige(self, rp_earned):
        """
        Выполняет престиж: сбрасывает прогресс, добавляет RP.
        Сохраняет: престиж-улучшения, достижения, статистику.
        """
        if self.save_data is None:
            return

        # Сохраняем то что не сбрасывается
        prestige_count = self.save_data.get("prestige_count", 0) + 1
        total_rp = self.save_data.get("total_rp", 0) + rp_earned
        available_rp = self.save_data.get("available_rp", 0) + rp_earned
        prestige_upgrades = copy.deepcopy(
            self.save_data.get("prestige_upgrades", {})
        )
        achievements = copy.deepcopy(
            self.save_data.get("achievements", [])
        )
        play_time = self.save_data.get("play_time", 0)
        total_clicks_all = self.save_data.get("total_clicks", 0)
        golden_caught = self.save_data.get("golden_caught", 0)
        deals_won = self.save_data.get("deals_won", 0)
        deals_lost = self.save_data.get("deals_lost", 0)
        challenges_completed = self.save_data.get("challenges_completed", 0)
        debuffs_survived = self.save_data.get("debuffs_survived", 0)
        created_at = self.save_data.get("created_at", "")
        current_theme = self.save_data.get("current_theme", "default")

        # Сбрасываем
        self.save_data = self._default_save()

        # Восстанавливаем
        self.save_data["prestige_count"] = prestige_count
        self.save_data["total_rp"] = total_rp
        self.save_data["available_rp"] = available_rp
        self.save_data["prestige_upgrades"] = prestige_upgrades
        self.save_data["achievements"] = achievements
        self.save_data["play_time"] = play_time
        self.save_data["total_clicks"] = total_clicks_all
        self.save_data["golden_caught"] = golden_caught
        self.save_data["deals_won"] = deals_won
        self.save_data["deals_lost"] = deals_lost
        self.save_data["challenges_completed"] = challenges_completed
        self.save_data["debuffs_survived"] = debuffs_survived
        self.save_data["created_at"] = created_at
        self.save_data["current_theme"] = current_theme

        # Применяем стартовые бонусы от престиж-улучшений
        starting_money = 0
        for up_id, count in prestige_upgrades.items():
            if up_id == "prestige_starting_money":
                starting_money += 1000 * count

        self.save_data["money"] = starting_money

        self.save_current()
