"""
botyaraclick - ui/style.py
Маленькая библиотека оформления: градиенты, карточки, тени, «пилюли».

Всё кешируется по размеру/цветам, поэтому рисовать панели каждый кадр
дёшево: тяжёлые поверхности создаются один раз.
"""

import pygame


# =====================================================================
# ЦВЕТА
# =====================================================================

def clamp(value, low=0.0, high=1.0):
    return low if value < low else high if value > high else value


def mix(c1, c2, t):
    """Линейно смешивает два цвета."""
    t = clamp(t)
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def lighten(color, amount=0.15):
    """Осветляет цвет (amount = доля пути к белому)."""
    return mix(color, (255, 255, 255), amount)


def darken(color, amount=0.15):
    """Затемняет цвет."""
    return mix(color, (0, 0, 0), amount)


def with_alpha(color, alpha):
    """Добавляет альфу к RGB-цвету."""
    alpha = max(0, min(255, int(alpha)))
    if len(color) >= 4:
        return (color[0], color[1], color[2], alpha)
    return (color[0], color[1], color[2], alpha)


def is_dark(color):
    """Тёмный ли цвет (для выбора цвета текста поверх него)."""
    luminance = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
    return luminance < 140


# =====================================================================
# КЕШ ПОВЕРХНОСТЕЙ
# =====================================================================

_gradient_cache = {}
_panel_cache = {}


def _cache_store(cache, key, value, limit=256):
    if len(cache) > limit:
        cache.clear()
    cache[key] = value


def vertical_gradient(size, top, bottom):
    """Вертикальный градиент (кешируется)."""
    key = (size, top, bottom)
    cached = _gradient_cache.get(key)
    if cached is not None:
        return cached

    width, height = size
    surf = pygame.Surface((max(1, width), max(1, height)), pygame.SRCALPHA)
    height = max(1, height)
    for y in range(height):
        ratio = y / max(1, height - 1)
        pygame.draw.line(
            surf, mix(top, bottom, ratio), (0, y), (max(1, width), y)
        )

    _cache_store(_gradient_cache, key, surf)
    return surf


def rounded_gradient(size, top, bottom, radius):
    """Градиент со скруглёнными углами."""
    key = ("rounded", size, top, bottom, radius)
    cached = _gradient_cache.get(key)
    if cached is not None:
        return cached

    width, height = max(1, size[0]), max(1, size[1])
    surf = vertical_gradient((width, height), top, bottom).copy()

    mask = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(
        mask, (255, 255, 255, 255),
        (0, 0, width, height), border_radius=radius
    )
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    _cache_store(_gradient_cache, key, surf)
    return surf


# =====================================================================
# ПАНЕЛИ И ТЕНИ
# =====================================================================

def draw_soft_rect(surface, rect, color, alpha=255, radius=8, border_width=0):
    """
    Полупрозрачный прямоугольник: рисуется на отдельном слое,
    поэтому альфа реально работает на любом экране.
    """
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0 or alpha <= 0:
        return

    layer = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(
        layer, with_alpha(color, alpha), (0, 0, rect.width, rect.height),
        border_radius=radius, width=border_width
    )
    surface.blit(layer, rect.topleft)


def draw_shadow(surface, rect, radius=12, spread=10, alpha=70, offset=(0, 4)):
    """
    Мягкая тень под прямоугольником (несколько слоёв с малой альфой).
    """
    if alpha <= 0:
        return

    rect = pygame.Rect(rect)
    pad = spread
    size = (rect.width + pad * 2, rect.height + pad * 2)
    layer = pygame.Surface(size, pygame.SRCALPHA)

    layers = 4
    for i in range(layers, 0, -1):
        grow = int(spread * i / layers)
        layer_alpha = int(alpha * (0.35 if i > 1 else 0.75) / layers)
        if layer_alpha <= 0:
            continue
        shadow_rect = pygame.Rect(
            pad - grow, pad - grow + 2,
            rect.width + grow * 2, rect.height + grow * 2,
        )
        try:
            pygame.draw.rect(
                layer, (0, 0, 0, layer_alpha), shadow_rect,
                border_radius=max(2, radius + grow)
            )
        except TypeError:
            return

    surface.blit(layer, (rect.x - pad + offset[0], rect.y - pad + offset[1]))


def draw_panel(surface, rect, color, radius=12, border_color=None,
               border_width=1, alpha=255, shadow=False, gradient=0.10,
               shadow_alpha=70):
    """
    Панель с градиентом, рамкой и (опционально) тенью.

    gradient — насколько нижняя часть темнее верхней (0 = плоский цвет).
    """
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return

    top = lighten(color, gradient * 0.4)
    bottom = darken(color, gradient)

    key = ("panel", rect.width, rect.height, top, bottom, radius, alpha)
    cached = _panel_cache.get(key)
    if cached is None:
        cached = rounded_gradient((rect.width, rect.height), top, bottom, radius)
        if alpha < 255:
            cached = cached.copy()
            cached.set_alpha(alpha)
        _cache_store(_panel_cache, key, cached)

    if shadow:
        draw_shadow(surface, rect, radius=radius, alpha=shadow_alpha)

    surface.blit(cached, rect.topleft)

    if border_color and border_width > 0:
        pygame.draw.rect(
            surface, border_color, rect,
            width=border_width, border_radius=radius
        )


def draw_glow_circle(surface, center, radius, color, alpha=60, layers=6):
    """Мягкое свечение вокруг точки."""
    if radius <= 0 or alpha <= 0:
        return

    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for i in range(layers, 0, -1):
        r = int(radius * i / layers)
        if r <= 0:
            continue
        layer_alpha = int(alpha * (1.0 - (i - 1) / layers) / layers * 2.2)
        if layer_alpha <= 0:
            continue
        pygame.draw.circle(
            glow, with_alpha(color, layer_alpha), (radius, radius), r
        )
    surface.blit(glow, (center[0] - radius, center[1] - radius))


def draw_check(surface, center, size=10, color=(120, 220, 150), width=2):
    """Рисует галочку линиями (символ «✓» есть не во всех шрифтах)."""
    cx, cy = center
    half = size / 2.0
    points = [
        (cx - half, cy + size * 0.02),
        (cx - half * 0.30, cy + half * 0.72),
        (cx + half, cy - half * 0.62),
    ]
    pygame.draw.lines(surface, color, False, points, width)


_glow_cache = {}


def ellipse_glow(size, color, alpha=90, power=2.0):
    """
    Мягкое эллиптическое свечение (гладкое, без видимых границ слоёв).
    """
    w, h = int(size[0]), int(size[1])
    key = (w, h, color, alpha, power)
    cached = _glow_cache.get(key)
    if cached is not None:
        return cached

    import math

    low_w, low_h = 96, max(12, int(96 * h / max(1, w)))
    small = pygame.Surface((low_w, low_h), pygame.SRCALPHA)
    cx, cy = (low_w - 1) / 2, (low_h - 1) / 2
    for y in range(low_h):
        for x in range(low_w):
            dx = (x - cx) / max(0.5, cx)
            dy = (y - cy) / max(0.5, cy)
            d = min(1.0, (dx * dx + dy * dy) ** 0.5)
            a = int(alpha * ((1 - d) ** power))
            if a > 0:
                small.set_at((x, y), (color[0], color[1], color[2], a))

    surface = pygame.transform.smoothscale(small, (w, h))
    _cache_store(_glow_cache, key, surface, limit=32)
    return surface


_dome_cache = {}


def radial_dome(diameter, color, light_lighten=0.42, edge_darken=0.52):
    """
    Гладкая «сфера» с бликом — для главной кнопки клика.

    Рисуется в низком разрешении попиксельно и растягивается smoothscale,
    поэтому нет видимых колец-бандинга, как при наложении кругов.
    """
    diameter = max(8, int(diameter))
    key = (diameter, color, light_lighten, edge_darken)
    cached = _dome_cache.get(key)
    if cached is not None:
        return cached

    import math

    low = 160
    r = low / 2.0
    light_color = lighten(color, light_lighten)
    edge_color = darken(color, edge_darken)

    # Кэш цветов по «расстоянию до источника света» — экономим пересчёты
    shade_table = []
    for i in range(65):
        ratio = i / 64
        shade_table.append(mix(light_color, edge_color, ratio))

    base = pygame.Surface((low, low), pygame.SRCALPHA)
    light_cx, light_cy = r - 0.20 * r, r - 0.26 * r

    for y in range(low):
        for x in range(low):
            # внутри круга?
            cdx, cdy = x - r, y - r
            circle_dist = math.hypot(cdx, cdy) / r
            if circle_dist > 1.0:
                continue

            dist = math.hypot(x - light_cx, y - light_cy) / r
            ratio = min(1.0, dist / 1.55)
            col = list(shade_table[int(ratio * 64)])

            # Вертикальное затемнение к низу
            bottom = max(0.0, (y - r * 1.05) / (0.95 * r))
            if bottom > 0:
                k = 0.22 * bottom
                col = [int(c * (1 - k)) for c in col]

            # Верхний блик (мягкий эллипс)
            ex = (x - r) / (0.60 * r)
            ey = (y - 0.36 * r) / (0.26 * r)
            e = ex * ex + ey * ey
            if e < 1.0:
                strength = (1.0 - e) ** 2 * 0.55
                col = [
                    int(c + (255 - c) * strength) for c in col
                ]

            # Ободок по краю (запекаем — тогда он гладкий)
            if circle_dist > 0.93:
                k = (circle_dist - 0.93) / 0.07
                col = [
                    int(c + (255 - c) * 0.45 * k) for c in col
                ]

            # Мягкий край (антиалиасинг)
            alpha = 255
            if circle_dist > 0.985:
                alpha = int(255 * (1.0 - (circle_dist - 0.985) / 0.015))
                alpha = max(0, min(255, alpha))

            base.set_at((x, y), (col[0], col[1], col[2], alpha))

    surface = pygame.transform.smoothscale(base, (diameter, diameter))
    _cache_store(_dome_cache, key, surface, limit=64)
    return surface


def draw_pill(surface, center, text_surf, color, padding=(10, 5),
              radius=None, text_color=None):
    """«Пилюля» с текстом (для цен, счётчиков, ярлыков)."""
    pad_x, pad_y = padding
    width = text_surf.get_width() + pad_x * 2
    height = text_surf.get_height() + pad_y * 2
    rect = pygame.Rect(0, 0, width, height)
    rect.center = center
    radius = height // 2 if radius is None else radius

    pygame.draw.rect(surface, color, rect, border_radius=radius)
    surface.blit(text_surf, text_surf.get_rect(center=rect.center))
    return rect


def draw_separator(surface, x1, x2, y, color, alpha=110):
    """Тонкая полупрозрачная линия."""
    if isinstance(x1, pygame.Rect):
        rect = x1
        x1, x2 = rect.left, rect.right
        y = rect.top
    line = pygame.Surface((max(1, int(x2) - int(x1)), 1), pygame.SRCALPHA)
    line.fill(with_alpha(color, alpha))
    surface.blit(line, (int(x1), int(y)))


def draw_progress_bar(surface, rect, progress, color, bg_color,
                      radius=None, bg_alpha=40):
    """Полоска прогресса (фон — полупрозрачный)."""
    rect = pygame.Rect(rect)
    radius = rect.height // 2 if radius is None else radius

    if isinstance(bg_color, tuple) and len(bg_color) == 4:
        bg_alpha = bg_color[3]
        bg_color = bg_color[:3]
    draw_soft_rect(surface, rect, bg_color, bg_alpha, radius=radius)

    progress = clamp(progress)
    if progress > 0:
        filled = pygame.Rect(
            rect.x, rect.y, max(2, int(rect.width * progress)),
            rect.height
        )
        pygame.draw.rect(surface, color, filled, border_radius=radius)


def fit_text(text, font, max_width, ellipsis="…"):
    """Обрезает текст по фактической ширине в пикселях."""
    if not font or not text:
        return text or ""
    if font.size(text)[0] <= max_width:
        return text

    result = text
    while result and font.size(result + ellipsis)[0] > max_width:
        result = result[:-1]
    result = result.rstrip()
    return (result + ellipsis) if result else ellipsis
