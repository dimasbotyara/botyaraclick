"""
botyaraclick - locales/locale_manager.py
Менеджер локализации.

Автоматически обнаруживает все файлы локализации в папке locales/
и позволяет переключаться между ними с автоматическим фолбэком.
"""

import os
import importlib
import sys

from config import LOCALES_DIR, BASE_DIR


class LocaleManager:
    """Менеджер локализации с автообнаружением языков и безопасным фолбэком."""

    def __init__(self):
        self.current_locale = "ru"
        self.available_locales = {}
        self.strings = {}
        self.fallback_strings = {}
        self._discover_locales()
        self._load_fallback()

    def _discover_locales(self):
        """Автоматически находит все файлы локализации."""
        locales_dir = os.path.join(BASE_DIR, "locales")
        if not os.path.exists(locales_dir):
            os.makedirs(locales_dir, exist_ok=True)
            return

        for filename in os.listdir(locales_dir):
            if filename.startswith("lang_") and filename.endswith(".py"):
                lang_code = filename[5:-3]
                self.available_locales[lang_code] = filename

    def _load_fallback(self):
        """Загружает дефолтный языковой файл для фолбэка (ru/en)."""
        locales_path = os.path.join(BASE_DIR, "locales")
        if locales_path not in sys.path:
            sys.path.insert(0, locales_path)

        for lang_code in ["ru", "en"]:
            if lang_code in self.available_locales:
                module_name = self.available_locales[lang_code][:-3]
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, "STRINGS"):
                        self.fallback_strings = module.STRINGS
                        break
                except Exception as e:
                    print(f"[LocaleManager] Failed to load fallback '{lang_code}': {e}")

    def load_locale(self, lang_code: str) -> bool:
        """Загружает языковой файл."""
        if lang_code not in self.available_locales:
            print(f"[LocaleManager] Language '{lang_code}' not found!")
            return False

        filename = self.available_locales[lang_code]
        module_name = filename[:-3]  # убираем .py

        try:
            locales_path = os.path.join(BASE_DIR, "locales")
            if locales_path not in sys.path:
                sys.path.insert(0, locales_path)

            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)

            if hasattr(module, "STRINGS"):
                self.strings = module.STRINGS
                self.current_locale = lang_code
                print(f"[LocaleManager] Loaded locale: {lang_code}")
                return True
            else:
                print(f"[LocaleManager] Module {module_name} has no STRINGS dict!")
                return False

        except Exception as e:
            print(f"[LocaleManager] Error loading locale {lang_code}: {e}")
            return False

    def get(self, key: str, **kwargs) -> str:
        """
        Получает локализованную строку по ключу.
        1. Ищет в текущей локали
        2. Ищет в резервной локали (fallback)
        3. Преобразует имя ключа в читаемый формат без уродующих скобок [key]
        """
        keys = key.split(".")

        # 1. Поиск в текущей локали
        value = self._lookup(self.strings, keys)

        # 2. Поиск в резервной локали
        if value is None and self.fallback_strings:
            value = self._lookup(self.fallback_strings, keys)

        # 3. Грациозный фолбэк вместо [key]
        if value is None:
            raw_name = keys[-1].replace("_", " ")
            value = raw_name.capitalize()

        if isinstance(value, str):
            if kwargs:
                try:
                    return value.format(**kwargs)
                except (KeyError, IndexError):
                    # Простая ручная замена, если именованные аргументы не совпали полностью
                    res = value
                    for k, v in kwargs.items():
                        res = res.replace(f"{{{k}}}", str(v))
                    return res
            return value

        return str(value)

    def _lookup(self, dict_tree: dict, keys: list):
        """Вспомогательный рекурсивный/итеративный поиск в словаре."""
        val = dict_tree
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return None
        return val

    def get_available_languages(self) -> list:
        """Возвращает список доступных языков в формате [(code, name), ...]"""
        result = []
        for code in sorted(self.available_locales.keys()):
            try:
                self.load_locale(code)
                name = self.strings.get("_language_name", code.upper())
                result.append((code, name))
            except Exception:
                result.append((code, code.upper()))

        if self.current_locale:
            self.load_locale(self.current_locale)

        return result

    def get_language_name(self, lang_code: str) -> str:
        """Возвращает человекочитаемое название языка."""
        old_locale = self.current_locale
        old_strings = self.strings.copy()

        if self.load_locale(lang_code):
            name = self.strings.get("_language_name", lang_code.upper())
        else:
            name = lang_code.upper()

        self.strings = old_strings
        self.current_locale = old_locale

        return name


# Глобальный экземпляр
locale = LocaleManager()


def t(key: str, **kwargs) -> str:
    """Shortcut для получения локализованной строки."""
    return locale.get(key, **kwargs)
