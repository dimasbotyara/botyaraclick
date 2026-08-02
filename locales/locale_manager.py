"""
botyaraclick - locales/locale_manager.py
Менеджер локализации.

Автоматически обнаруживает все файлы локализации в папке locales/
и позволяет переключаться между ними.
"""

import os
import importlib
import sys

from config import LOCALES_DIR, BASE_DIR


class LocaleManager:
    """Менеджер локализации с автообнаружением языков."""

    def __init__(self):
        self.current_locale = "en"
        self.available_locales = {}
        self.strings = {}
        self._discover_locales()

    def _discover_locales(self):
        """Автоматически находит все файлы локализации."""
        locales_dir = os.path.join(BASE_DIR, "locales")
        if not os.path.exists(locales_dir):
            os.makedirs(locales_dir, exist_ok=True)
            return

        for filename in os.listdir(locales_dir):
            if filename.startswith("lang_") and filename.endswith(".py"):
                # lang_en.py -> "en"
                lang_code = filename[5:-3]
                self.available_locales[lang_code] = filename

    def load_locale(self, lang_code: str) -> bool:
        """Загружает языковой файл."""
        if lang_code not in self.available_locales:
            print(f"[LocaleManager] Language '{lang_code}' not found!")
            return False

        filename = self.available_locales[lang_code]
        module_name = filename[:-3]  # убираем .py

        try:
            # Динамический импорт языкового модуля
            locales_path = os.path.join(BASE_DIR, "locales")
            if locales_path not in sys.path:
                sys.path.insert(0, locales_path)

            # Если модуль уже загружен, перезагружаем
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
        Поддерживает вложенные ключи через точку: "menu.play"
        Поддерживает форматирование: get("earned", amount=100)
        """
        keys = key.split(".")
        value = self.strings

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Ключ не найден — возвращаем сам ключ
                return f"[{key}]"

        if isinstance(value, str):
            try:
                return value.format(**kwargs) if kwargs else value
            except (KeyError, IndexError):
                return value

        return f"[{key}]"

    def get_available_languages(self) -> list:
        """Возвращает список доступных языков в формате [(code, name), ...]"""
        result = []
        for code in sorted(self.available_locales.keys()):
            # Пробуем получить название языка из файла
            try:
                self.load_locale(code)
                name = self.strings.get("_language_name", code.upper())
                result.append((code, name))
            except Exception:
                result.append((code, code.upper()))

        # Восстанавливаем текущую локаль
        if self.current_locale:
            self.load_locale(self.current_locale)

        return result

    def get_language_name(self, lang_code: str) -> str:
        """Возвращает человекочитаемое название языка."""
        # Временно загружаем локаль чтобы получить имя
        old_locale = self.current_locale
        old_strings = self.strings.copy()

        if self.load_locale(lang_code):
            name = self.strings.get("_language_name", lang_code.upper())
        else:
            name = lang_code.upper()

        # Восстанавливаем
        self.strings = old_strings
        self.current_locale = old_locale

        return name


# Глобальный экземпляр
locale = LocaleManager()


def t(key: str, **kwargs) -> str:
    """Shortcut для получения локализованной строки."""
    return locale.get(key, **kwargs)
