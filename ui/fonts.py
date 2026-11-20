"""
botyaraclick - ui/fonts.py
Оффлайн-шрифты: загрузка из assets/fonts + автоматический фолбэк.

Зачем это нужно:
- В pygame один шрифт не умеет подставлять глифы из другого шрифта
  (нет fontconfig-фолбэка). Из-за этого эмодзи (🚀, 🏆, 🤮) и кириллица
  в «латинских» темах превращались в квадратики «тофу».
- Здесь реализован FallbackFont: он разбивает строку на кластеры
  (буква / эмодзи / составное эмодзи) и рисует каждый кусок тем шрифтом,
  в котором этот символ реально есть.

Порядок поиска глифа:
    1. основной шрифт темы (например Orbitron)
    2. Montserrat — универсальный фолбэк с кириллицей
    3. NotoEmoji-Regular.ttf — монохромные эмодзи

Все шрифты лежат в репозитории (assets/fonts), интернет не нужен.
"""

import os
import struct
import unicodedata

import pygame

from config import FONTS_DIR


# === ФАЙЛЫ ШРИФТОВ ===
EMOJI_FONT_FILE = "NotoEmoji-Regular.ttf"
DEFAULT_FAMILY = "Montserrat"
FALLBACK_FAMILY = "Montserrat"


# =====================================================================
# ЧТЕНИЕ cmap: какие символы реально есть в шрифте
# =====================================================================

_CMAP_CACHE = {}


def _u16(data, offset):
    return struct.unpack(">H", data[offset:offset + 2])[0]


def _cmap_format4(data, base):
    """Формат 4 — BMP (U+0000..U+FFFF)."""
    covered = set()
    seg_count = _u16(data, base + 6) // 2
    end_pos = base + 14
    start_pos = end_pos + seg_count * 2 + 2
    delta_pos = start_pos + seg_count * 2
    range_pos = delta_pos + seg_count * 2

    for seg in range(seg_count):
        end = _u16(data, end_pos + seg * 2)
        start = _u16(data, start_pos + seg * 2)
        delta = _u16(data, delta_pos + seg * 2)
        range_offset = _u16(data, range_pos + seg * 2)

        if start == 0xFFFF and end == 0xFFFF:
            continue
        for cp in range(start, min(end, 0xFFFE) + 1):
            if range_offset == 0:
                gid = (cp + delta) & 0xFFFF
            else:
                gid_pos = range_pos + seg * 2 + range_offset + (cp - start) * 2
                if gid_pos + 2 > len(data):
                    continue
                gid = _u16(data, gid_pos)
                if gid:
                    gid = (gid + delta) & 0xFFFF
            if gid:
                covered.add(cp)
    return covered


def _cmap_format12(data, base):
    """Формат 12 — полный Unicode (в том числе эмодзи вне BMP)."""
    covered = set()
    try:
        n_groups = struct.unpack(">I", data[base + 12:base + 16])[0]
    except struct.error:
        return covered

    pos = base + 16
    for _ in range(n_groups):
        if pos + 12 > len(data):
            break
        start, end, start_gid = struct.unpack(">III", data[pos:pos + 12])
        pos += 12
        if end - start > 0x20000:  # защита от битых таблиц
            continue
        for cp in range(start, end + 1):
            covered.add(cp)
    return covered


def _read_cmap_codepoints(path):
    """Возвращает множество кодпоинтов, для которых в шрифте есть глиф."""
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return set()

    if len(data) < 12:
        return set()

    num_tables = _u16(data, 4)
    cmap_offset = None
    for i in range(num_tables):
        rec = 12 + i * 16
        if rec + 16 > len(data):
            break
        if data[rec:rec + 4] == b"cmap":
            cmap_offset = struct.unpack(">I", data[rec + 8:rec + 12])[0]
            break

    if cmap_offset is None:
        return set()

    sub_count = _u16(data, cmap_offset + 2)
    covered = set()
    for i in range(sub_count):
        rec = cmap_offset + 4 + i * 8
        if rec + 8 > len(data):
            break
        platform, encoding, sub_offset = struct.unpack(">HHI", data[rec:rec + 8])
        base = cmap_offset + sub_offset
        if base + 2 > len(data):
            continue
        fmt = _u16(data, base)
        try:
            if fmt == 4:
                covered |= _cmap_format4(data, base)
            elif fmt == 12:
                covered |= _cmap_format12(data, base)
        except (struct.error, IndexError, ValueError):
            continue
    return covered


def coverage(path):
    """Кешированное множество символов шрифта."""
    if path not in _CMAP_CACHE:
        _CMAP_CACHE[path] = _read_cmap_codepoints(path)
    return _CMAP_CACHE[path]


# =====================================================================
# РАЗБИЕНИЕ СТРОКИ НА КЛАСТЕРЫ (буква / эмодзи / составное эмодзи)
# =====================================================================

_ZWJ = 0x200D
_VARIATION_SELECTORS = {0xFE0E, 0xFE0F}
_SKIN_TONES = range(0x1F3FB, 0x1F400)
_TAGS = range(0xE0020, 0xE0080)
_KEYCAP = 0x20E3
_REGIONAL = range(0x1F1E6, 0x1F200)


def _visible_codepoints(cluster):
    """Кодпоинты кластера, наличие которых надо проверять в шрифте."""
    result = []
    for ch in cluster:
        cp = ord(ch)
        if cp in _VARIATION_SELECTORS or cp == _ZWJ:
            continue
        if cp in _SKIN_TONES or cp in _TAGS or cp == _KEYCAP:
            continue
        result.append(cp)
    return result


def split_clusters(text):
    """Делит строку на кластеры, не разрывая составные эмодзи и диакритику."""
    clusters = []
    i = 0
    n = len(text)
    while i < n:
        start = i
        cp = ord(text[i])
        i += 1

        # Флаги: пара региональных индикаторов — один кластер
        if cp in _REGIONAL and i < n and ord(text[i]) in _REGIONAL:
            i += 1

        while i < n:
            cp2 = ord(text[i])
            ch2 = text[i]
            if cp2 in _VARIATION_SELECTORS or cp2 in _SKIN_TONES or cp2 == _KEYCAP:
                i += 1
            elif cp2 in _TAGS:
                i += 1
            elif unicodedata.combining(ch2):
                i += 1
            elif cp2 == _ZWJ:
                if i + 1 < n:
                    i += 2
                else:
                    i += 1
            else:
                break
        clusters.append(text[start:i])
    return clusters


# =====================================================================
# FALLBACK FONT
# =====================================================================

class FallbackFont:
    """
    Шрифт-обёртка с фолбэком на другие шрифты (кириллица + эмодзи).

    Повторяет API pygame.font.Font для render()/size()/метрик,
    поэтому его можно использовать везде, где раньше был pygame.font.Font.
    """

    def __init__(self, layers, size):
        """
        layers: список путей к шрифтам в порядке приоритета
                [основной, фолбэк, эмодзи]
        size: размер в пикселях (как у pygame.font.Font)
        """
        self.size_px = int(size)
        self.path = layers[0] if layers else None
        self._layers = []  # [(font, coverage_set)]

        for path in layers:
            if not path:
                continue
            try:
                font = pygame.font.Font(path, self.size_px)
            except (pygame.error, FileNotFoundError, OSError):
                continue
            cov = coverage(path)
            if not cov:
                # Не смогли прочитать cmap — считаем, что шрифт умеет всё,
                # чтобы не сломать отрисовку.
                cov = None
            self._layers.append((font, cov))

        if not self._layers:
            try:
                fallback = pygame.font.Font(None, self.size_px)
            except pygame.error:
                fallback = None
            self._layers.append((fallback, None))

        self._height = max(f.get_height() for f, _ in self._layers if f)
        self._ascent = max(f.get_ascent() for f, _ in self._layers if f)
        self._descent = max(f.get_descent() for f, _ in self._layers if f)
        self._linesize = max(f.get_linesize() for f, _ in self._layers if f)

        self._cache = {}
        self._cluster_layer_cache = {}

    # --- выбор шрифта для кластера ---------------------------------

    def _layer_for_cluster(self, cluster):
        cached = self._cluster_layer_cache.get(cluster)
        if cached is not None:
            return cached

        needed = _visible_codepoints(cluster)
        choice = 0
        for idx, (_, cov) in enumerate(self._layers):
            if cov is None:  # неизвестное покрытие — доверяем шрифту
                choice = idx
                break
            if all(cp in cov for cp in needed):
                choice = idx
                break
        else:
            choice = 0  # нигде нет — пусть рисует основной (тофу)

        if len(self._cluster_layer_cache) > 4096:
            self._cluster_layer_cache.clear()
        self._cluster_layer_cache[cluster] = choice
        return choice

    def _build_runs(self, text):
        """Группирует соседние кластеры, рисуемые одним шрифтом."""
        runs = []
        for cluster in split_clusters(text):
            idx = self._layer_for_cluster(cluster)
            if runs and runs[-1][0] == idx:
                runs[-1][1] += cluster
            else:
                runs.append([idx, cluster])
        return [(idx, run) for idx, run in runs]

    # --- API, совместимый с pygame.font.Font ------------------------

    def render(self, text, antialias=True, color=(255, 255, 255),
               background=None):
        """Рисует строку с фолбэком на другие шрифты."""
        text = "" if text is None else str(text)
        key = (text, bool(antialias), tuple(color), background)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        runs = self._build_runs(text)

        if not runs:
            surf = pygame.Surface((0, self._height), pygame.SRCALPHA)
            if background is not None:
                surf.fill(background)
            self._cache[key] = surf
            return surf

        rendered = []
        width = 0
        for idx, run in runs:
            font = self._layers[idx][0]
            if font is None:
                continue
            try:
                if background is not None:
                    run_surf = font.render(run, antialias, color, background)
                else:
                    run_surf = font.render(run, antialias, color)
            except (pygame.error, TypeError):
                continue
            rendered.append((run_surf, font.get_ascent()))
            width += run_surf.get_width()

        if not rendered:
            surf = pygame.Surface((0, self._height), pygame.SRCALPHA)
            self._cache[key] = surf
            return surf

        if background is None:
            surf = pygame.Surface((max(1, width), self._height), pygame.SRCALPHA)
        else:
            surf = pygame.Surface((max(1, width), self._height), pygame.SRCALPHA)
            surf.fill(background)

        x = 0
        for run_surf, ascent in rendered:
            surf.blit(run_surf, (x, self._ascent - ascent))
            x += run_surf.get_width()

        if len(self._cache) > 2048:
            self._cache.clear()
        self._cache[key] = surf
        return surf

    def size(self, text):
        """Ширина/высота строки (с учётом фолбэка)."""
        text = "" if text is None else str(text)
        key = ("__size__", text)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        width = 0
        for idx, run in self._build_runs(text):
            font = self._layers[idx][0]
            if font is None:
                continue
            width += font.size(run)[0]

        result = (width, self._height)
        if len(self._cache) > 2048:
            self._cache.clear()
        self._cache[key] = result
        return result

    def get_height(self):
        return self._height

    def get_ascent(self):
        return self._ascent

    def get_descent(self):
        return self._descent

    def get_linesize(self):
        return self._linesize

    def get_bold(self):
        return self._layers[0][0].get_bold() if self._layers[0][0] else False

    def get_italic(self):
        return self._layers[0][0].get_italic() if self._layers[0][0] else False

    def get_underline(self):
        return self._layers[0][0].get_underline() if self._layers[0][0] else False

    def set_bold(self, value):
        for font, _ in self._layers:
            if font:
                font.set_bold(value)

    def set_italic(self, value):
        for font, _ in self._layers:
            if font:
                font.set_italic(value)

    def set_underline(self, value):
        for font, _ in self._layers:
            if font:
                font.set_underline(value)

    def __getattr__(self, item):
        # Всё остальное — у основного шрифта
        layers = self.__dict__.get("_layers")
        if layers and layers[0][0] is not None:
            return getattr(layers[0][0], item)
        raise AttributeError(item)


# =====================================================================
# МЕНЕДЖЕР ШРИФТОВ
# =====================================================================

class FontManager:
    """Загружает оффлайн-шрифты и кеширует FallbackFont по размеру."""

    def __init__(self):
        self._cache = {}
        self._families = {}

    # --- пути ------------------------------------------------------

    def family_files(self, family):
        """Возвращает (regular_path, bold_path) для семейства шрифтов."""
        if family in self._families:
            return self._families[family]

        regular, bold = None, None
        try:
            from data.themes import THEME_FONTS
            info = THEME_FONTS.get(family, {})
            regular = info.get("regular")
            bold = info.get("bold")
        except Exception:
            info = {}

        regular_path = os.path.join(FONTS_DIR, regular) if regular else None
        bold_path = os.path.join(FONTS_DIR, bold) if bold else None

        if not regular_path or not os.path.exists(regular_path):
            regular_path = os.path.join(
                FONTS_DIR, "Montserrat-Regular.ttf"
            )
            if not os.path.exists(regular_path):
                regular_path = None
            bold_path = os.path.join(FONTS_DIR, "Montserrat-Bold.ttf")
            if not os.path.exists(bold_path):
                bold_path = regular_path

        if not bold_path or not os.path.exists(bold_path):
            bold_path = regular_path

        self._families[family] = (regular_path, bold_path)
        return regular_path, bold_path

    def emoji_path(self):
        path = os.path.join(FONTS_DIR, EMOJI_FONT_FILE)
        return path if os.path.exists(path) else None

    def _layers_for(self, family, bold):
        regular_path, bold_path = self.family_files(family)
        primary = bold_path if bold else regular_path

        layers = []
        if primary:
            layers.append(primary)

        # Универсальный фолбэк: кириллица + латиница
        fb_regular, fb_bold = self.family_files(FALLBACK_FAMILY)
        fallback = fb_bold if bold else fb_regular
        if fallback and fallback not in layers:
            layers.append(fallback)

        emoji = self.emoji_path()
        if emoji and emoji not in layers:
            layers.append(emoji)

        return layers

    # --- получение шрифта ------------------------------------------

    def get(self, size, bold=False, family=None):
        """Возвращает FallbackFont нужного размера."""
        family = family or DEFAULT_FAMILY
        size = max(6, int(size))
        key = (family, bool(bold), size)
        font = self._cache.get(key)
        if font is None:
            font = FallbackFont(self._layers_for(family, bold), size)
            self._cache[key] = font
        return font

    def load_theme_fonts(self, family):
        """Набор именованных шрифтов для экранов игры."""
        return {
            "title": self.get(36, bold=True, family=family),
            "large": self.get(30, bold=True, family=family),
            "money_big": self.get(32, bold=True, family=family),
            "button": self.get(24, family=family),
            "subtitle": self.get(22, family=family),
            "normal": self.get(20, family=family),
            "click_text": self.get(42, bold=True, family=family),
            "small": self.get(16, family=family),
            "tiny": self.get(14, family=family),
        }

    def clear(self):
        self._cache.clear()


# Глобальный менеджер
font_manager = FontManager()


def get_font(size, bold=False, family=None):
    """Короткий доступ к шрифту с фолбэком на эмодзи и кириллицу."""
    return font_manager.get(size, bold=bold, family=family)


def load_theme_fonts(family=DEFAULT_FAMILY):
    """Набор именованных шрифтов (title/normal/small/...)."""
    return font_manager.load_theme_fonts(family)
