"""
botyaraclick - locales/locale_manager.py
Менеджер локализации.

Автоматически обнаруживает все файлы локализации в папке locales/
и позволяет переключаться между ними с автоматическим фолбэком.

Важные гарантии:
- lang_template.py (шаблон для переводчиков) НЕ считается языком игры.
- Получение списка языков и названий НЕ меняет текущий язык.
- Пустая строка в переводе считается отсутствующим переводом.
- Ссылки-плейсхолдеры вида "[settings.effects_enabled]" внутри строк
  автоматически подставляются реальным переводом.
- t() никогда не возвращает "[ключ]" — только читаемый текст.
"""

import importlib.util
import os
import re
import sys

from config import BASE_DIR


# Файлы, которые не являются настоящими языками
_SKIPPED_CODES = {"template", "lang", "__init__", "example", "sample"}

# Плейсхолдер-ссылка на другой ключ: [section.key]
_REF_PATTERN = re.compile(r"\[([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+)\]")

_MAX_REF_DEPTH = 4


class LocaleManager:
    """Менеджер локализации с автообнаружением языков и безопасным фолбэком."""

    def __init__(self):
        self.current_locale = "ru"
        self.available_locales = {}      # code -> filename
        self.strings = {}                # текущие строки
        self.fallback_strings = {}       # строки резервного языка
        self.fallback_code = None

        self._module_cache = {}          # code -> STRINGS (или None)
        self._name_cache = {}            # code -> название языка

        self._discover_locales()
        self._load_fallback()

        if self.current_locale not in self.available_locales:
            self.current_locale = self._first_available()

        if self.current_locale:
            self.load_locale(self.current_locale)

    # ================================================================
    # ОБНАРУЖЕНИЕ И ЗАГРУЗКА
    # ================================================================

    def _discover_locales(self):
        """Автоматически находит все файлы локализации."""
        locales_dir = os.path.join(BASE_DIR, "locales")
        if not os.path.exists(locales_dir):
            os.makedirs(locales_dir, exist_ok=True)
            return

        for filename in sorted(os.listdir(locales_dir)):
            if not (filename.startswith("lang_") and filename.endswith(".py")):
                continue
            lang_code = filename[5:-3]
            if lang_code.lower() in _SKIPPED_CODES:
                continue
            self.available_locales[lang_code] = filename

    def _first_available(self):
        for code in ("ru", "en"):
            if code in self.available_locales:
                return code
        return next(iter(self.available_locales), None)

    def _strings_for(self, lang_code, reload=False):
        """
        Загружает STRINGS из файла языка.

        Возвращает dict или None, если файл битый / это не язык игры.
        Глобальное состояние менеджера НЕ меняется.
        """
        if not reload and lang_code in self._module_cache:
            return self._module_cache[lang_code]

        filename = self.available_locales.get(lang_code)
        if not filename:
            self._module_cache[lang_code] = None
            return None

        path = os.path.join(BASE_DIR, "locales", filename)
        module_name = f"botyaraclick_locale_{lang_code}"

        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                raise ImportError(f"cannot load {path}")
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"[LocaleManager] Error loading locale '{lang_code}': {e}")
            self._module_cache[lang_code] = None
            return None

        strings = getattr(module, "STRINGS", None)
        if not isinstance(strings, dict) or not strings:
            print(f"[LocaleManager] '{filename}' has no valid STRINGS dict")
            self._module_cache[lang_code] = None
            return None

        self._module_cache[lang_code] = strings
        return strings

    def _load_fallback(self):
        """Загружает резервный язык (ru, иначе en, иначе первый доступный)."""
        for code in ("ru", "en"):
            if code in self.available_locales:
                strings = self._strings_for(code)
                if strings:
                    self.fallback_strings = strings
                    self.fallback_code = code
                    return

        for code in self.available_locales:
            strings = self._strings_for(code)
            if strings:
                self.fallback_strings = strings
                self.fallback_code = code
                return

    def load_locale(self, lang_code: str, reload: bool = False) -> bool:
        """Загружает языковой файл. При неудаче оставляет текущий язык."""
        if lang_code not in self.available_locales:
            print(f"[LocaleManager] Language '{lang_code}' not found!")
            return False

        strings = self._strings_for(lang_code, reload=reload)
        if not strings:
            return False

        self.strings = strings
        self.current_locale = lang_code

        # Резервный язык не должен совпадать с текущим
        if lang_code == self.fallback_code:
            for code in ("ru", "en"):
                if code != lang_code and self._strings_for(code):
                    self.fallback_strings = self._strings_for(code)
                    self.fallback_code = code
                    break

        return True

    # ================================================================
    # ПОЛУЧЕНИЕ СТРОК
    # ================================================================

    def get(self, key: str, **kwargs) -> str:
        """
        Получает локализованную строку по ключу.

        Порядок поиска:
        1. текущий язык
        2. резервный язык
        3. читаемое имя ключа (например "Effects enabled") —
           никогда не "[settings.effects_enabled]"
        """
        if not isinstance(key, str):
            return str(key)

        keys = key.split(".")

        value = self._lookup(self.strings, keys)
        if self._is_empty(value):
            value = self._lookup(self.fallback_strings, keys)

        if self._is_empty(value):
            value = self._humanize(keys)

        if not isinstance(value, str):
            return str(value)

        # Подставляем ссылки-плейсхолдеры вида [section.key]
        value = self._resolve_refs(value)

        if kwargs:
            return self._format(value, kwargs)
        return value

    def _format(self, value, kwargs):
        """format() с безопасным фолбэком и ссылками на другие ключи."""
        try:
            return value.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            pass

        result = value
        for name, val in kwargs.items():
            result = result.replace("{" + name + "}", str(val))

        # Незаполненные {key} пробуем перевести как ключ локализации
        def replace_missing(match):
            name = match.group(1)
            if name in kwargs:
                return str(kwargs[name])
            if "." in name:
                translated = self.get(name)
                if translated and translated != self._humanize(name.split(".")):
                    return translated
            return match.group(0)

        return re.sub(r"\{([A-Za-z0-9_.]+)\}", replace_missing, result)

    def _is_empty(self, value):
        if value is None:
            return True
        if isinstance(value, str):
            return not value.strip()
        return False

    def _humanize(self, keys):
        """Читаемое имя ключа без квадратных скобок и подчёркиваний."""
        raw = keys[-1] if keys else "text"
        raw = raw.replace("_", " ").strip()
        if not raw:
            return ""
        return raw[0].upper() + raw[1:]

    def _resolve_refs(self, value, depth=0):
        """Заменяет "[section.key]" на перевод этого ключа."""
        if depth >= _MAX_REF_DEPTH or "[" not in value:
            return value

        def replace(match):
            ref_key = match.group(1)
            translated = self._lookup(self.strings, ref_key.split("."))
            if self._is_empty(translated):
                translated = self._lookup(self.fallback_strings, ref_key.split("."))
            if self._is_empty(translated) or not isinstance(translated, str):
                # Неизвестная ссылка — не показываем квадратные скобки
                return self._humanize(ref_key.split("."))
            return self._resolve_refs(translated, depth + 1)

        return _REF_PATTERN.sub(replace, value)

    def _lookup(self, dict_tree, keys):
        """Итеративный поиск в словаре по списку ключей."""
        val = dict_tree
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return None
        return val

    # ================================================================
    # СПИСОК ЯЗЫКОВ
    # ================================================================

    def get_available_languages(self) -> list:
        """
        Возвращает [(code, name), ...].

        Состояние менеджера НЕ меняется — это было причиной бага,
        когда после выхода из настроек всё превращалось в плейсхолдеры.
        """
        result = []
        for code in sorted(self.available_locales):
            result.append((code, self.get_language_name(code)))
        return result

    def get_language_name(self, lang_code: str) -> str:
        """Возвращает человекочитаемое название языка."""
        if lang_code in self._name_cache:
            return self._name_cache[lang_code]

        strings = self._strings_for(lang_code)
        name = None
        if strings:
            raw = strings.get("_language_name")
            if isinstance(raw, str) and raw.strip():
                name = raw.strip()

        if not name:
            name = lang_code.upper()

        self._name_cache[lang_code] = name
        return name

    def is_valid_language(self, lang_code: str) -> bool:
        """Есть ли такой язык и загружается ли он."""
        return bool(self._strings_for(lang_code))

    def reload(self):
        """Перечитывает файлы локализации с диска."""
        self._module_cache.clear()
        self._name_cache.clear()
        self._discover_locales()
        self._load_fallback()
        if self.current_locale in self.available_locales:
            self.load_locale(self.current_locale, reload=True)


# Глобальный экземпляр
locale = LocaleManager()


def t(key: str, **kwargs) -> str:
    """Shortcut для получения локализованной строки."""
    return locale.get(key, **kwargs)
