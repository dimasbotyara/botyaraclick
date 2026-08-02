"""
botyaraclick - effects/bg_effects.py
Фоновые визуальные эффекты для разных тем.

Поддерживаемые эффекты:
- none: без эффекта
- matrix_rain: падающие символы (Киберпанк, Хакер)
- stars: мерцающие звёзды (Глубокий Космос)
- falling_leaves: падающие листья (Уютный Лес)
- snowflakes: падающие снежинки (Зимняя Сказка)
- bubbles: всплывающие пузырьки (Конфетная Страна, Океан)
- embers: летящие угольки (Лавовая Пещера)
- bats: летучие мыши (Хэллоуин)
- scanlines: ретро-сканлайны (Ретро 8-bit)
- gold_sparkle: золотые искорки (Королевское Золото)
"""

import pygame
import random
import math


class MatrixRainDrop:
    """Одна 'капля' матричного дождя — столбец падающих символов."""

    __slots__ = ['x', 'y', 'speed', 'chars', 'char_size',
                 'color', 'max_length', 'timer', 'interval']

    MATRIX_CHARS = "01アイウエオカキクケコサシスセソタチツテト0110ナニヌネノ"

    def __init__(self, x, screen_height, color=(0, 255, 0), char_size=14):
        self.x = x
        self.y = random.randint(-screen_height, 0)
        self.speed = random.uniform(80, 250)
        self.char_size = char_size
        self.color = color
        self.max_length = random.randint(5, 25)
        self.chars = [random.choice(self.MATRIX_CHARS) for _ in range(self.max_length)]
        self.timer = 0
        self.interval = random.uniform(0.05, 0.15)

    def update(self, dt, screen_height):
        self.y += self.speed * dt
        self.timer += dt
        if self.timer >= self.interval:
            self.timer = 0
            # Меняем случайный символ
            idx = random.randint(0, len(self.chars) - 1)
            self.chars[idx] = random.choice(self.MATRIX_CHARS)

        if self.y - self.max_length * self.char_size > screen_height:
            self.y = random.randint(-200, -20)
            self.speed = random.uniform(80, 250)


class Star:
    """Мерцающая звезда."""

    __slots__ = ['x', 'y', 'base_brightness', 'brightness',
                 'twinkle_speed', 'twinkle_phase', 'size']

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.choice([1, 1, 1, 2, 2, 3])
        self.base_brightness = random.randint(100, 255)
        self.brightness = self.base_brightness
        self.twinkle_speed = random.uniform(1, 5)
        self.twinkle_phase = random.uniform(0, math.pi * 2)

    def update(self, dt):
        self.twinkle_phase += self.twinkle_speed * dt
        variation = math.sin(self.twinkle_phase) * 80
        self.brightness = max(30, min(255,
                                      int(self.base_brightness + variation)))


class FallingLeaf:
    """Падающий листок."""

    __slots__ = ['x', 'y', 'vx', 'vy', 'rotation', 'rot_speed',
                 'color', 'size', 'sway_phase', 'sway_speed', 'sway_amp']

    LEAF_COLORS = [
        (120, 180, 60), (100, 160, 40), (80, 140, 30),
        (160, 140, 40), (140, 120, 30), (180, 160, 50)
    ]

    def __init__(self, screen_width):
        self.x = random.uniform(0, screen_width)
        self.y = random.uniform(-50, -10)
        self.vx = random.uniform(-15, 15)
        self.vy = random.uniform(20, 60)
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-100, 100)
        self.color = random.choice(self.LEAF_COLORS)
        self.size = random.uniform(3, 7)
        self.sway_phase = random.uniform(0, math.pi * 2)
        self.sway_speed = random.uniform(1, 3)
        self.sway_amp = random.uniform(20, 50)

    def update(self, dt, screen_height, screen_width):
        self.sway_phase += self.sway_speed * dt
        self.x += self.vx * dt + math.sin(self.sway_phase) * self.sway_amp * dt
        self.y += self.vy * dt
        self.rotation += self.rot_speed * dt

        if self.y > screen_height + 20:
            self.y = random.uniform(-50, -10)
            self.x = random.uniform(0, screen_width)


class Snowflake:
    """Снежинка."""

    __slots__ = ['x', 'y', 'vy', 'size', 'alpha',
                 'sway_phase', 'sway_speed', 'sway_amp']

    def __init__(self, screen_width):
        self.x = random.uniform(0, screen_width)
        self.y = random.uniform(-30, -5)
        self.vy = random.uniform(20, 80)
        self.size = random.uniform(1.5, 4)
        self.alpha = random.randint(120, 255)
        self.sway_phase = random.uniform(0, math.pi * 2)
        self.sway_speed = random.uniform(0.5, 2)
        self.sway_amp = random.uniform(10, 40)

    def update(self, dt, screen_height, screen_width):
        self.sway_phase += self.sway_speed * dt
        self.x += math.sin(self.sway_phase) * self.sway_amp * dt
        self.y += self.vy * dt

        if self.y > screen_height + 10:
            self.y = random.uniform(-30, -5)
            self.x = random.uniform(0, screen_width)


class Bubble:
    """Пузырёк."""

    __slots__ = ['x', 'y', 'vy', 'size', 'alpha',
                 'wobble_phase', 'wobble_speed', 'color']

    def __init__(self, screen_width, screen_height, color=None):
        self.x = random.uniform(0, screen_width)
        self.y = screen_height + random.uniform(10, 50)
        self.vy = random.uniform(-30, -80)
        self.size = random.uniform(3, 12)
        self.alpha = random.randint(40, 120)
        self.wobble_phase = random.uniform(0, math.pi * 2)
        self.wobble_speed = random.uniform(1, 3)
        self.color = color or (200, 230, 255)

    def update(self, dt, screen_height, screen_width):
        self.wobble_phase += self.wobble_speed * dt
        self.x += math.sin(self.wobble_phase) * 15 * dt
        self.y += self.vy * dt

        if self.y < -20:
            self.y = screen_height + random.uniform(10, 50)
            self.x = random.uniform(0, screen_width)


class Ember:
    """Уголёк / искра."""

    __slots__ = ['x', 'y', 'vx', 'vy', 'size', 'lifetime',
                 'max_lifetime', 'color', 'glow']

    EMBER_COLORS = [
        (255, 100, 20), (255, 150, 30), (255, 200, 50),
        (255, 80, 10), (220, 60, 10)
    ]

    def __init__(self, screen_width, screen_height):
        self.x = random.uniform(0, screen_width)
        self.y = screen_height + random.uniform(10, 30)
        self.vx = random.uniform(-20, 20)
        self.vy = random.uniform(-80, -30)
        self.size = random.uniform(1.5, 4)
        self.lifetime = random.uniform(2, 5)
        self.max_lifetime = self.lifetime
        self.color = random.choice(self.EMBER_COLORS)
        self.glow = random.random() < 0.3

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx += random.uniform(-10, 10) * dt
        self.lifetime -= dt


class Bat:
    """Летучая мышь."""

    __slots__ = ['x', 'y', 'vx', 'vy', 'wing_phase',
                 'wing_speed', 'size', 'direction']

    def __init__(self, screen_width, screen_height):
        side = random.choice(["left", "right"])
        if side == "left":
            self.x = -30
            self.vx = random.uniform(40, 100)
        else:
            self.x = screen_width + 30
            self.vx = random.uniform(-100, -40)

        self.y = random.uniform(50, screen_height * 0.6)
        self.vy = random.uniform(-30, 30)
        self.wing_phase = random.uniform(0, math.pi * 2)
        self.wing_speed = random.uniform(8, 15)
        self.size = random.uniform(8, 15)
        self.direction = 1 if self.vx > 0 else -1

    def update(self, dt, screen_width, screen_height):
        self.x += self.vx * dt
        self.y += self.vy * dt + math.sin(self.wing_phase * 0.5) * 20 * dt
        self.wing_phase += self.wing_speed * dt
        self.vy += random.uniform(-5, 5) * dt

    @property
    def alive(self):
        return -50 < self.x < 2000 and -50 < self.y < 1000


class BackgroundEffect:
    """Базовый класс фонового эффекта."""

    def update(self, dt, screen_width, screen_height):
        pass

    def draw(self, surface):
        pass


class MatrixRainEffect(BackgroundEffect):
    """Эффект матричного дождя."""

    def __init__(self, screen_width, screen_height,
                 color=(0, 255, 0), density=0.03, char_size=14):
        self.color = color
        self.char_size = char_size
        self.drops = []
        self._font = None

        # Создаём столбцы
        num_columns = int(screen_width * density)
        for _ in range(num_columns):
            x = random.uniform(0, screen_width)
            drop = MatrixRainDrop(x, screen_height, color, char_size)
            self.drops.append(drop)

    def update(self, dt, screen_width, screen_height):
        for drop in self.drops:
            drop.update(dt, screen_height)

    def draw(self, surface):
        if not self._font:
            try:
                self._font = pygame.font.Font(None, 14)
            except pygame.error:
                return

        for drop in self.drops:
            for i, char in enumerate(drop.chars):
                char_y = int(drop.y - i * drop.char_size)
                if char_y < -drop.char_size or char_y > surface.get_height():
                    continue

                # Яркость уменьшается по длине хвоста
                brightness = max(0, 1.0 - i / drop.max_length)
                alpha = int(brightness * 180)
                if alpha <= 0:
                    continue

                # Первый символ — самый яркий
                if i == 0:
                    color = (
                        min(255, drop.color[0] + 100),
                        min(255, drop.color[1] + 100),
                        min(255, drop.color[2] + 100)
                    )
                    alpha = 255
                else:
                    color = drop.color

                char_surf = self._font.render(char, True, color)
                char_surf.set_alpha(alpha)
                surface.blit(char_surf, (int(drop.x), char_y))


class StarsEffect(BackgroundEffect):
    """Мерцающие звёзды."""

    def __init__(self, screen_width, screen_height, count=150):
        self.stars = []
        for _ in range(count):
            star = Star(
                random.uniform(0, screen_width),
                random.uniform(0, screen_height)
            )
            self.stars.append(star)

    def update(self, dt, screen_width, screen_height):
        for star in self.stars:
            star.update(dt)

    def draw(self, surface):
        for star in self.stars:
            alpha = star.brightness
            if star.size <= 1:
                color = (alpha, alpha, alpha)
                surface.set_at((int(star.x), int(star.y)), color)
            else:
                star_surf = pygame.Surface(
                    (star.size * 2, star.size * 2), pygame.SRCALPHA
                )
                pygame.draw.circle(
                    star_surf,
                    (255, 255, 255, alpha),
                    (star.size, star.size), star.size
                )
                surface.blit(star_surf,
                             (int(star.x - star.size),
                              int(star.y - star.size)))


class FallingLeavesEffect(BackgroundEffect):
    """Падающие листья."""

    def __init__(self, screen_width, screen_height, count=25):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.leaves = []
        for _ in range(count):
            leaf = FallingLeaf(screen_width)
            leaf.y = random.uniform(0, screen_height)  # распределяем по экрану
            self.leaves.append(leaf)

    def update(self, dt, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        for leaf in self.leaves:
            leaf.update(dt, screen_height, screen_width)

    def draw(self, surface):
        for leaf in self.leaves:
            # Рисуем листок как эллипс с вращением
            size = leaf.size
            leaf_surf = pygame.Surface(
                (int(size * 3), int(size * 3)), pygame.SRCALPHA
            )
            center = (int(size * 1.5), int(size * 1.5))

            # Основной эллипс
            angle = math.radians(leaf.rotation)
            w = size * 2
            h = size

            points = []
            for i in range(12):
                a = (math.pi * 2 / 12) * i
                px = math.cos(a) * w / 2
                py = math.sin(a) * h / 2
                # Вращаем
                rx = px * math.cos(angle) - py * math.sin(angle)
                ry = px * math.sin(angle) + py * math.cos(angle)
                points.append((center[0] + rx, center[1] + ry))

            if len(points) >= 3:
                pygame.draw.polygon(leaf_surf, (*leaf.color, 180), points)

            surface.blit(leaf_surf,
                         (int(leaf.x - size * 1.5),
                          int(leaf.y - size * 1.5)))


class SnowflakesEffect(BackgroundEffect):
    """Падающие снежинки."""

    def __init__(self, screen_width, screen_height, count=60):
        self.flakes = []
        for _ in range(count):
            flake = Snowflake(screen_width)
            flake.y = random.uniform(0, screen_height)
            self.flakes.append(flake)

    def update(self, dt, screen_width, screen_height):
        for flake in self.flakes:
            flake.update(dt, screen_height, screen_width)

    def draw(self, surface):
        for flake in self.flakes:
            r = max(1, int(flake.size))
            flake_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                flake_surf,
                (255, 255, 255, flake.alpha),
                (r, r), r
            )
            surface.blit(flake_surf,
                         (int(flake.x - r), int(flake.y - r)))


class BubblesEffect(BackgroundEffect):
    """Всплывающие пузырьки."""

    def __init__(self, screen_width, screen_height,
                 count=20, color=None):
        self.bubbles = []
        for _ in range(count):
            bubble = Bubble(screen_width, screen_height, color)
            bubble.y = random.uniform(0, screen_height)
            self.bubbles.append(bubble)

    def update(self, dt, screen_width, screen_height):
        for bubble in self.bubbles:
            bubble.update(dt, screen_height, screen_width)

    def draw(self, surface):
        for bubble in self.bubbles:
            r = max(2, int(bubble.size))
            bubble_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)

            # Обводка пузырька
            pygame.draw.circle(
                bubble_surf,
                (*bubble.color, bubble.alpha),
                (r + 1, r + 1), r, 1
            )

            # Блик
            highlight_r = max(1, r // 3)
            pygame.draw.circle(
                bubble_surf,
                (255, 255, 255, bubble.alpha // 2),
                (r + 1 - r // 3, r + 1 - r // 3),
                highlight_r
            )

            surface.blit(bubble_surf,
                         (int(bubble.x - r - 1),
                          int(bubble.y - r - 1)))


class EmbersEffect(BackgroundEffect):
    """Летящие угольки."""

    def __init__(self, screen_width, screen_height, count=30):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.embers = []
        for _ in range(count):
            ember = Ember(screen_width, screen_height)
            ember.y = random.uniform(0, screen_height)
            ember.lifetime = random.uniform(0, ember.max_lifetime)
            self.embers.append(ember)

    def update(self, dt, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        for ember in self.embers:
            ember.update(dt)

        # Удаляем и заменяем мёртвые
        self.embers = [e for e in self.embers if e.lifetime > 0]
        while len(self.embers) < 30:
            self.embers.append(Ember(screen_width, screen_height))

    def draw(self, surface):
        for ember in self.embers:
            life_ratio = max(0, ember.lifetime / ember.max_lifetime)
            alpha = int(255 * life_ratio)
            r = max(1, int(ember.size * life_ratio))

            if ember.glow and r >= 2:
                glow_surf = pygame.Surface((r * 6, r * 6), pygame.SRCALPHA)
                glow_alpha = min(60, alpha // 3)
                pygame.draw.circle(
                    glow_surf,
                    (*ember.color, glow_alpha),
                    (r * 3, r * 3), r * 3
                )
                surface.blit(glow_surf,
                             (int(ember.x - r * 3),
                              int(ember.y - r * 3)))

            ember_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                ember_surf,
                (*ember.color, alpha),
                (r, r), r
            )
            surface.blit(ember_surf,
                         (int(ember.x - r), int(ember.y - r)))


class BatsEffect(BackgroundEffect):
    """Летучие мыши."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.bats = []
        self.spawn_timer = 0
        self.spawn_interval = random.uniform(2, 5)

    def update(self, dt, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Спавн
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval and len(self.bats) < 8:
            self.bats.append(Bat(screen_width, screen_height))
            self.spawn_timer = 0
            self.spawn_interval = random.uniform(2, 5)

        # Обновление
        for bat in self.bats:
            bat.update(dt, screen_width, screen_height)

        # Удаление улетевших
        self.bats = [b for b in self.bats if b.alive]

    def draw(self, surface):
        for bat in self.bats:
            # Рисуем простую летучую мышь из линий
            wing_angle = math.sin(bat.wing_phase) * 30
            cx, cy = int(bat.x), int(bat.y)
            size = bat.size

            # Тело
            bat_surf = pygame.Surface(
                (int(size * 4), int(size * 3)), pygame.SRCALPHA
            )
            bcx = int(size * 2)
            bcy = int(size * 1.5)

            body_color = (40, 10, 50, 200)

            # Тело
            pygame.draw.circle(bat_surf, body_color, (bcx, bcy), int(size * 0.4))

            # Крылья
            wing_y = int(math.sin(math.radians(wing_angle)) * size * 0.8)

            # Левое крыло
            points_l = [
                (bcx, bcy),
                (bcx - int(size * 1.2), bcy + wing_y - int(size * 0.3)),
                (bcx - int(size * 1.5), bcy + wing_y),
                (bcx - int(size * 0.5), bcy + int(size * 0.2)),
            ]
            pygame.draw.polygon(bat_surf, body_color, points_l)

            # Правое крыло
            points_r = [
                (bcx, bcy),
                (bcx + int(size * 1.2), bcy + wing_y - int(size * 0.3)),
                (bcx + int(size * 1.5), bcy + wing_y),
                (bcx + int(size * 0.5), bcy + int(size * 0.2)),
            ]
            pygame.draw.polygon(bat_surf, body_color, points_r)

            surface.blit(bat_surf,
                         (cx - int(size * 2), cy - int(size * 1.5)))


class ScanlinesEffect(BackgroundEffect):
    """Ретро сканлайны."""

    def __init__(self, screen_width, screen_height):
        self.line_spacing = 3
        self.alpha = 30

    def update(self, dt, screen_width, screen_height):
        pass

    def draw(self, surface):
        sw, sh = surface.get_size()
        scanline_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)

        for y in range(0, sh, self.line_spacing):
            pygame.draw.line(
                scanline_surf,
                (0, 0, 0, self.alpha),
                (0, y), (sw, y)
            )

        surface.blit(scanline_surf, (0, 0))


class GoldSparkleEffect(BackgroundEffect):
    """Золотые искорки."""

    def __init__(self, screen_width, screen_height, count=20):
        self.sparkles = []
        self.screen_width = screen_width
        self.screen_height = screen_height

        for _ in range(count):
            self.sparkles.append(self._new_sparkle())

    def _new_sparkle(self):
        return {
            'x': random.uniform(0, self.screen_width),
            'y': random.uniform(0, self.screen_height),
            'phase': random.uniform(0, math.pi * 2),
            'speed': random.uniform(1, 4),
            'size': random.uniform(1, 3),
            'color': random.choice([
                (255, 215, 0), (255, 200, 50),
                (255, 230, 100), (200, 170, 40)
            ]),
        }

    def update(self, dt, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        for s in self.sparkles:
            s['phase'] += s['speed'] * dt

    def draw(self, surface):
        for s in self.sparkles:
            brightness = (math.sin(s['phase']) + 1) / 2
            if brightness < 0.3:
                continue

            alpha = int(brightness * 200)
            r = max(1, int(s['size'] * brightness))

            sparkle_surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)

            # Свечение
            glow_alpha = min(60, alpha // 3)
            pygame.draw.circle(
                sparkle_surf,
                (*s['color'], glow_alpha),
                (r * 2, r * 2), r * 2
            )

            # Точка
            pygame.draw.circle(
                sparkle_surf,
                (*s['color'], alpha),
                (r * 2, r * 2), r
            )

            # Крестик
            line_len = int(r * 1.5)
            cx, cy = r * 2, r * 2
            line_alpha = min(150, alpha)
            pygame.draw.line(
                sparkle_surf,
                (*s['color'], line_alpha),
                (cx - line_len, cy), (cx + line_len, cy)
            )
            pygame.draw.line(
                sparkle_surf,
                (*s['color'], line_alpha),
                (cx, cy - line_len), (cx, cy + line_len)
            )

            surface.blit(sparkle_surf,
                         (int(s['x'] - r * 2),
                          int(s['y'] - r * 2)))


# ============================================================================
# МЕНЕДЖЕР ФОНОВЫХ ЭФФЕКТОВ
# ============================================================================

class BackgroundEffectManager:
    """
    Менеджер фоновых эффектов.
    Создаёт и управляет нужным эффектом на основе текущей темы.
    """

    EFFECT_CLASSES = {
        "none": None,
        "matrix_rain": MatrixRainEffect,
        "stars": StarsEffect,
        "falling_leaves": FallingLeavesEffect,
        "snowflakes": SnowflakesEffect,
        "bubbles": BubblesEffect,
        "embers": EmbersEffect,
        "bats": BatsEffect,
        "scanlines": ScanlinesEffect,
        "gold_sparkle": GoldSparkleEffect,
    }

    def __init__(self, screen_width, screen_height, enabled=True):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.enabled = enabled
        self.current_effect = None
        self.current_effect_name = "none"

    def set_effect(self, effect_name, theme=None):
        """Устанавливает фоновый эффект по имени."""
        if effect_name == self.current_effect_name:
            return

        self.current_effect_name = effect_name

        if effect_name == "none" or effect_name not in self.EFFECT_CLASSES:
            self.current_effect = None
            return

        effect_class = self.EFFECT_CLASSES[effect_name]
        if effect_class is None:
            self.current_effect = None
            return

        # Определяем параметры из темы
        if effect_name == "matrix_rain":
            color = (0, 255, 0)
            if theme:
                # Для киберпанка — фиолетовый/голубой
                if theme.get("id") == "cyberpunk":
                    color = (0, 255, 255)
            self.current_effect = MatrixRainEffect(
                self.screen_width, self.screen_height,
                color=color
            )
        elif effect_name == "bubbles":
            color = None
            if theme:
                if theme.get("id") == "candy_land":
                    color = (255, 200, 230)
                elif theme.get("id") == "deep_ocean":
                    color = (100, 200, 230)
            self.current_effect = BubblesEffect(
                self.screen_width, self.screen_height,
                color=color
            )
        else:
            self.current_effect = effect_class(
                self.screen_width, self.screen_height
            )

    def update(self, dt):
        """Обновляет текущий эффект."""
        if not self.enabled or not self.current_effect:
            return

        self.current_effect.update(dt, self.screen_width, self.screen_height)

    def draw(self, surface):
        """Рисует текущий эффект."""
        if not self.enabled or not self.current_effect:
            return

        self.current_effect.draw(surface)

    def resize(self, screen_width, screen_height):
        """Обновляет размеры экрана."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        # Пересоздаём эффект для нового размера
        if self.current_effect_name != "none":
            old_name = self.current_effect_name
            self.current_effect_name = "none"  # чтобы set_effect сработал
            self.set_effect(old_name)

    def set_enabled(self, enabled):
        """Включает/выключает эффекты."""
        self.enabled = enabled
