"""
botyaraclick - effects/particles.py
Система частиц для визуальных эффектов при клике,
покупке, достижениях и других событиях.

Поддерживаемые типы частиц:
- spark: маленькие искорки
- coin: монетки (кружочки)
- star: звёздочки
- confetti: конфетти (прямоугольники)
- burst: взрыв (расходящиеся точки)
- ring: расходящееся кольцо
"""

import pygame
import random
import math


class Particle:
    """Одна частица."""

    __slots__ = [
        'x', 'y', 'vx', 'vy', 'size', 'color',
        'lifetime', 'max_lifetime', 'gravity',
        'friction', 'rotation', 'rotation_speed',
        'shape', 'alpha', 'shrink', 'glow'
    ]

    def __init__(self, x, y, vx, vy, size, color,
                 lifetime=1.0, gravity=0.0, friction=0.98,
                 rotation=0, rotation_speed=0,
                 shape="circle", shrink=True, glow=False):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity = gravity
        self.friction = friction
        self.rotation = rotation
        self.rotation_speed = rotation_speed
        self.shape = shape
        self.alpha = 255
        self.shrink = shrink
        self.glow = glow

    def update(self, dt):
        """Обновляет позицию и состояние частицы."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.vx *= self.friction
        self.vy *= self.friction
        self.rotation += self.rotation_speed * dt
        self.lifetime -= dt

        # Прозрачность зависит от оставшегося времени
        life_ratio = max(0, self.lifetime / self.max_lifetime)
        self.alpha = int(255 * life_ratio)

    @property
    def alive(self):
        return self.lifetime > 0

    @property
    def current_size(self):
        if self.shrink:
            life_ratio = max(0, self.lifetime / self.max_lifetime)
            return max(0.5, self.size * life_ratio)
        return self.size


class ParticleSystem:
    """
    Система управления частицами.
    Создаёт, обновляет и рисует частицы.
    """

    def __init__(self, max_particles=500, enabled=True):
        """
        Параметры:
            max_particles: максимальное количество частиц одновременно
            enabled: включены ли эффекты
        """
        self.particles = []
        self.max_particles = max_particles
        self.enabled = enabled

    def emit_click(self, x, y, colors=None, count=8, power=1.0):
        """
        Создаёт частицы при клике.
        Искорки разлетаются из точки клика.
        """
        if not self.enabled:
            return

        if colors is None:
            colors = [(255, 255, 255), (255, 220, 100), (100, 200, 255)]

        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(80, 250) * power
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            size = random.uniform(2, 5) * power
            color = random.choice(colors)
            lifetime = random.uniform(0.4, 0.9)

            particle = Particle(
                x=x, y=y, vx=vx, vy=vy,
                size=size, color=color,
                lifetime=lifetime,
                gravity=200,  # немного падают вниз
                friction=0.96,
                shape="circle",
                shrink=True,
                glow=True
            )
            self._add_particle(particle)

    def emit_crit(self, x, y, colors=None, count=20):
        """
        Создаёт мощный взрыв частиц при критическом ударе.
        """
        if not self.enabled:
            return

        if colors is None:
            colors = [(255, 200, 0), (255, 150, 0), (255, 255, 100)]

        # Кольцо
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(150, 400)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            size = random.uniform(3, 7)
            color = random.choice(colors)
            lifetime = random.uniform(0.5, 1.2)

            particle = Particle(
                x=x, y=y, vx=vx, vy=vy,
                size=size, color=color,
                lifetime=lifetime,
                gravity=100,
                friction=0.95,
                shape="circle",
                shrink=True,
                glow=True
            )
            self._add_particle(particle)

        # Звёздочки
        for _ in range(count // 3):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(50, 200)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            particle = Particle(
                x=x, y=y, vx=vx, vy=vy,
                size=random.uniform(4, 8),
                color=(255, 255, 200),
                lifetime=random.uniform(0.8, 1.5),
                gravity=50,
                friction=0.97,
                shape="star",
                shrink=True,
                glow=True,
                rotation=random.uniform(0, 360),
                rotation_speed=random.uniform(-300, 300)
            )
            self._add_particle(particle)

    def emit_purchase(self, x, y, colors=None, count=12):
        """Частицы при покупке — монетки летят вверх."""
        if not self.enabled:
            return

        if colors is None:
            colors = [(255, 215, 0), (255, 200, 50), (200, 170, 40)]

        for _ in range(count):
            vx = random.uniform(-100, 100)
            vy = random.uniform(-250, -100)

            particle = Particle(
                x=x + random.uniform(-20, 20),
                y=y + random.uniform(-10, 10),
                vx=vx, vy=vy,
                size=random.uniform(3, 6),
                color=random.choice(colors),
                lifetime=random.uniform(0.8, 1.5),
                gravity=300,
                friction=0.98,
                shape="coin",
                shrink=False,
                glow=False,
                rotation=random.uniform(0, 360),
                rotation_speed=random.uniform(-200, 200)
            )
            self._add_particle(particle)

    def emit_confetti(self, x, y, colors=None, count=30):
        """Конфетти для достижений и престижа."""
        if not self.enabled:
            return

        if colors is None:
            colors = [
                (255, 100, 100), (100, 255, 100), (100, 100, 255),
                (255, 255, 100), (255, 100, 255), (100, 255, 255),
                (255, 200, 50), (255, 150, 200)
            ]

        for _ in range(count):
            vx = random.uniform(-200, 200)
            vy = random.uniform(-350, -150)

            particle = Particle(
                x=x + random.uniform(-50, 50),
                y=y,
                vx=vx, vy=vy,
                size=random.uniform(3, 7),
                color=random.choice(colors),
                lifetime=random.uniform(1.5, 3.0),
                gravity=200,
                friction=0.99,
                shape="confetti",
                shrink=False,
                glow=False,
                rotation=random.uniform(0, 360),
                rotation_speed=random.uniform(-500, 500)
            )
            self._add_particle(particle)

    def emit_ring(self, x, y, color=(255, 255, 255), count=24, speed=200):
        """Расходящееся кольцо из частиц."""
        if not self.enabled:
            return

        for i in range(count):
            angle = (math.pi * 2 / count) * i
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            particle = Particle(
                x=x, y=y, vx=vx, vy=vy,
                size=3,
                color=color,
                lifetime=0.6,
                gravity=0,
                friction=0.95,
                shape="circle",
                shrink=True,
                glow=True
            )
            self._add_particle(particle)

    def emit_trail(self, x, y, color=(100, 200, 255), count=3):
        """Маленький след (для движущихся объектов)."""
        if not self.enabled:
            return

        for _ in range(count):
            particle = Particle(
                x=x + random.uniform(-5, 5),
                y=y + random.uniform(-5, 5),
                vx=random.uniform(-20, 20),
                vy=random.uniform(-20, 20),
                size=random.uniform(1.5, 3),
                color=color,
                lifetime=random.uniform(0.3, 0.6),
                gravity=0,
                friction=0.95,
                shape="circle",
                shrink=True,
                glow=True
            )
            self._add_particle(particle)

    def emit_custom(self, x, y, count=10, colors=None,
                    speed_range=(50, 200), size_range=(2, 5),
                    lifetime_range=(0.5, 1.0), gravity=100,
                    shape="circle", angle_range=(0, math.pi * 2),
                    glow=False):
        """Кастомные частицы для особых случаев."""
        if not self.enabled:
            return

        if colors is None:
            colors = [(255, 255, 255)]

        for _ in range(count):
            angle = random.uniform(*angle_range)
            speed = random.uniform(*speed_range)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            particle = Particle(
                x=x, y=y, vx=vx, vy=vy,
                size=random.uniform(*size_range),
                color=random.choice(colors),
                lifetime=random.uniform(*lifetime_range),
                gravity=gravity,
                friction=0.97,
                shape=shape,
                shrink=True,
                glow=glow,
                rotation=random.uniform(0, 360),
                rotation_speed=random.uniform(-200, 200)
            )
            self._add_particle(particle)

    def _add_particle(self, particle):
        """Добавляет частицу с ограничением максимального количества."""
        if len(self.particles) >= self.max_particles:
            # Удаляем самую старую
            if self.particles:
                self.particles.pop(0)
        self.particles.append(particle)

    def update(self, dt):
        """Обновляет все частицы."""
        for p in self.particles:
            p.update(dt)

        # Удаляем мёртвые
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, surface):
        """Рисует все частицы."""
        for p in self.particles:
            if p.alpha <= 0:
                continue

            size = p.current_size
            if size < 0.5:
                continue

            x = int(p.x)
            y = int(p.y)

            if p.shape == "circle":
                self._draw_circle(surface, p, x, y, size)
            elif p.shape == "star":
                self._draw_star(surface, p, x, y, size)
            elif p.shape == "coin":
                self._draw_coin(surface, p, x, y, size)
            elif p.shape == "confetti":
                self._draw_confetti(surface, p, x, y, size)
            else:
                self._draw_circle(surface, p, x, y, size)

    def _draw_circle(self, surface, p, x, y, size):
        """Рисует круглую частицу."""
        r = max(1, int(size))

        if p.glow and r >= 2:
            # Свечение — больший полупрозрачный круг
            glow_r = r * 3
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            glow_alpha = max(0, min(80, p.alpha // 3))
            pygame.draw.circle(
                glow_surf,
                (*p.color[:3], glow_alpha),
                (glow_r, glow_r), glow_r
            )
            surface.blit(glow_surf, (x - glow_r, y - glow_r))

        # Основная частица
        particle_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        alpha = max(0, min(255, p.alpha))
        pygame.draw.circle(
            particle_surf,
            (*p.color[:3], alpha),
            (r, r), r
        )
        surface.blit(particle_surf, (x - r, y - r))

    def _draw_star(self, surface, p, x, y, size):
        """Рисует звёздочку."""
        r = max(2, int(size))
        star_surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        center = (r * 2, r * 2)
        alpha = max(0, min(255, p.alpha))

        # Рисуем звезду из линий
        points = 5
        for i in range(points):
            angle1 = math.radians(p.rotation + (360 / points) * i - 90)
            angle2 = math.radians(p.rotation + (360 / points) * (i + 0.5) - 90)

            outer_x = center[0] + int(math.cos(angle1) * r * 1.5)
            outer_y = center[1] + int(math.sin(angle1) * r * 1.5)
            inner_x = center[0] + int(math.cos(angle2) * r * 0.6)
            inner_y = center[1] + int(math.sin(angle2) * r * 0.6)

            pygame.draw.line(
                star_surf,
                (*p.color[:3], alpha),
                center, (outer_x, outer_y), max(1, r // 3)
            )
            pygame.draw.line(
                star_surf,
                (*p.color[:3], alpha // 2),
                center, (inner_x, inner_y), max(1, r // 4)
            )

        surface.blit(star_surf, (x - r * 2, y - r * 2))

    def _draw_coin(self, surface, p, x, y, size):
        """Рисует монетку."""
        r = max(2, int(size))

        # Эллипс для эффекта вращения
        squeeze = abs(math.sin(p.rotation * 0.05))
        width = max(1, int(r * 2 * max(0.2, squeeze)))
        height = r * 2

        coin_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        alpha = max(0, min(255, p.alpha))

        ellipse_rect = pygame.Rect(
            r + 1 - width // 2, 1,
            width, height
        )
        pygame.draw.ellipse(
            coin_surf,
            (*p.color[:3], alpha),
            ellipse_rect
        )

        surface.blit(coin_surf, (x - r - 1, y - r - 1))

    def _draw_confetti(self, surface, p, x, y, size):
        """Рисует конфетти (вращающийся прямоугольник)."""
        w = max(2, int(size * 1.5))
        h = max(1, int(size * 0.6))

        confetti_surf = pygame.Surface((w * 3, h * 3), pygame.SRCALPHA)
        alpha = max(0, min(255, p.alpha))

        # Вращающийся прямоугольник
        center = (w * 1.5, h * 1.5)
        angle = p.rotation

        # 4 точки прямоугольника
        corners = [
            (-w / 2, -h / 2), (w / 2, -h / 2),
            (w / 2, h / 2), (-w / 2, h / 2)
        ]

        cos_a = math.cos(math.radians(angle))
        sin_a = math.sin(math.radians(angle))

        rotated = []
        for cx, cy in corners:
            rx = cx * cos_a - cy * sin_a + center[0]
            ry = cx * sin_a + cy * cos_a + center[1]
            rotated.append((rx, ry))

        pygame.draw.polygon(
            confetti_surf,
            (*p.color[:3], alpha),
            rotated
        )

        surface.blit(
            confetti_surf,
            (x - int(w * 1.5), y - int(h * 1.5))
        )

    def clear(self):
        """Удаляет все частицы."""
        self.particles.clear()

    @property
    def count(self):
        """Количество активных частиц."""
        return len(self.particles)
