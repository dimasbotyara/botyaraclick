"""
botyaraclick - effects/animations.py
Анимации UI-элементов: пульсация, тряска, масштабирование,
переходы между экранами, анимация смены эры.
"""

import pygame
import math
import time
from ui.fonts import get_font


class Animation:
    """Базовый класс анимации."""

    def __init__(self, duration, on_complete=None, loop=False):
        self.duration = duration
        self.elapsed = 0.0
        self.on_complete = on_complete
        self.loop = loop
        self.alive = True
        self.paused = False

    @property
    def progress(self):
        """Прогресс 0.0-1.0."""
        if self.duration <= 0:
            return 1.0
        return min(1.0, self.elapsed / self.duration)

    def update(self, dt):
        """Обновляет анимацию."""
        if self.paused or not self.alive:
            return

        self.elapsed += dt

        if self.elapsed >= self.duration:
            if self.loop:
                self.elapsed -= self.duration
            else:
                self.elapsed = self.duration
                self.alive = False
                if self.on_complete:
                    self.on_complete()

    def reset(self):
        """Сбрасывает анимацию."""
        self.elapsed = 0.0
        self.alive = True


class PulseAnimation(Animation):
    """
    Пульсация — плавное изменение масштаба.

    ВНИМАНИЕ: к кнопке клика НЕ применяется.
    Раньше кнопка «дышала» в простое — это раздражало и выглядело дёшево.
    Теперь в idle кнопка полностью статична: анимация есть только на
    наведение и на нажатие (ClickBounce). Класс оставлен для других
    декоративных элементов.
    """

    def __init__(self, min_scale=0.95, max_scale=1.05,
                 speed=2.0, loop=True):
        super().__init__(duration=0, loop=True)
        self.min_scale = min_scale
        self.max_scale = max_scale
        self.speed = speed
        self._phase = 0.0

    @property
    def scale(self):
        """Текущий масштаб."""
        t = (math.sin(self._phase) + 1) / 2  # 0..1
        return self.min_scale + (self.max_scale - self.min_scale) * t

    def update(self, dt):
        self._phase += self.speed * dt * math.pi * 2


class ShakeAnimation(Animation):
    """
    Тряска — быстрое случайное смещение.
    Используется при дебаффах, критах, ивентах.
    """

    def __init__(self, intensity=5, duration=0.3, decay=True,
                 on_complete=None):
        super().__init__(duration=duration, on_complete=on_complete)
        self.intensity = intensity
        self.decay = decay
        self._offset_x = 0
        self._offset_y = 0
        self._timer = 0

    @property
    def offset(self):
        """Текущее смещение (x, y)."""
        return self._offset_x, self._offset_y

    def update(self, dt):
        super().update(dt)

        if not self.alive:
            self._offset_x = 0
            self._offset_y = 0
            return

        self._timer += dt

        # Генерируем случайное смещение
        if self.decay:
            current_intensity = self.intensity * (1.0 - self.progress)
        else:
            current_intensity = self.intensity

        import random
        self._offset_x = random.uniform(
            -current_intensity, current_intensity
        )
        self._offset_y = random.uniform(
            -current_intensity, current_intensity
        )


class ScaleAnimation(Animation):
    """
    Масштабирование — плавное изменение размера.
    Используется при нажатии на кнопку клика.
    """

    def __init__(self, start_scale=1.0, end_scale=0.9,
                 duration=0.1, bounce=True, on_complete=None):
        super().__init__(duration=duration, on_complete=on_complete)
        self.start_scale = start_scale
        self.end_scale = end_scale
        self.bounce = bounce
        self._current_scale = start_scale

    @property
    def scale(self):
        return self._current_scale

    def update(self, dt):
        super().update(dt)

        t = self.progress
        if self.bounce:
            # Ease out bounce
            if t < 0.5:
                self._current_scale = self.start_scale + \
                    (self.end_scale - self.start_scale) * (t * 2)
            else:
                self._current_scale = self.end_scale + \
                    (self.start_scale - self.end_scale) * ((t - 0.5) * 2)
        else:
            # Linear
            self._current_scale = self.start_scale + \
                (self.end_scale - self.start_scale) * t


class FadeAnimation(Animation):
    """Плавное появление/исчезновение."""

    def __init__(self, start_alpha=0, end_alpha=255,
                 duration=0.3, on_complete=None):
        super().__init__(duration=duration, on_complete=on_complete)
        self.start_alpha = start_alpha
        self.end_alpha = end_alpha

    @property
    def alpha(self):
        t = self._ease_out(self.progress)
        return int(self.start_alpha + (self.end_alpha - self.start_alpha) * t)

    @staticmethod
    def _ease_out(t):
        return 1 - (1 - t) ** 2


class SlideAnimation(Animation):
    """Анимация выезда/заезда."""

    def __init__(self, start_pos, end_pos, duration=0.4,
                 ease="ease_out", on_complete=None):
        super().__init__(duration=duration, on_complete=on_complete)
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.ease = ease

    @property
    def position(self):
        t = self.progress
        if self.ease == "ease_out":
            t = 1 - (1 - t) ** 3
        elif self.ease == "ease_in":
            t = t ** 3
        elif self.ease == "ease_in_out":
            if t < 0.5:
                t = 4 * t ** 3
            else:
                t = 1 - (-2 * t + 2) ** 3 / 2

        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * t
        y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * t
        return x, y


class EraTransition(Animation):
    """
    Анимация перехода между эрами.
    Красивый эффект при достижении новой эры.
    """

    def __init__(self, old_era_colors, new_era_colors,
                 duration=3.0, on_complete=None):
        super().__init__(duration=duration, on_complete=on_complete)
        self.old_colors = old_era_colors
        self.new_colors = new_era_colors
        self._flash_alpha = 0
        self._text_alpha = 0
        self._text_scale = 0.5
        self._phase = "flash"  # flash -> text -> fade

    @property
    def bg_colors(self):
        """Текущие цвета фона (интерполяция)."""
        t = min(1.0, self.progress * 2)  # быстрее переход фона
        top = self._lerp_color(
            self.old_colors.get("top", (30, 30, 45)),
            self.new_colors.get("top", (30, 30, 45)),
            t
        )
        bottom = self._lerp_color(
            self.old_colors.get("bottom", (20, 20, 30)),
            self.new_colors.get("bottom", (20, 20, 30)),
            t
        )
        return top, bottom

    @property
    def flash_alpha(self):
        return self._flash_alpha

    @property
    def text_alpha(self):
        return self._text_alpha

    @property
    def text_scale(self):
        return self._text_scale

    def update(self, dt):
        super().update(dt)

        p = self.progress

        # Фазы анимации
        if p < 0.15:
            # Вспышка нарастает
            self._phase = "flash"
            flash_p = p / 0.15
            self._flash_alpha = int(200 * flash_p)
            self._text_alpha = 0
        elif p < 0.3:
            # Вспышка спадает, текст появляется
            self._phase = "text"
            flash_p = (p - 0.15) / 0.15
            self._flash_alpha = int(200 * (1 - flash_p))
            text_p = (p - 0.15) / 0.15
            self._text_alpha = int(255 * text_p)
            self._text_scale = 0.5 + 0.7 * text_p
        elif p < 0.7:
            # Текст держится
            self._flash_alpha = 0
            self._text_alpha = 255
            self._text_scale = 1.2
        else:
            # Текст исчезает
            self._phase = "fade"
            fade_p = (p - 0.7) / 0.3
            self._flash_alpha = 0
            self._text_alpha = int(255 * (1 - fade_p))
            self._text_scale = 1.2 + 0.3 * fade_p

    @staticmethod
    def _lerp_color(c1, c2, t):
        t = max(0, min(1, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )

    def draw(self, surface, era_name="", font=None, title_font=None):
        """Рисует эффект перехода."""
        sw, sh = surface.get_size()

        # Вспышка
        if self._flash_alpha > 0:
            flash_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, min(255, self._flash_alpha)))
            surface.blit(flash_surf, (0, 0))

        # Текст новой эры
        if self._text_alpha > 0 and era_name:
            f = title_font or font
            if f:
                # Масштабированный текст
                base_size = 48
                scaled_size = max(12, int(base_size * self._text_scale))
                big_font = get_font(scaled_size, bold=True)

                text_surf = big_font.render(era_name, True, (255, 255, 255))
                text_surf.set_alpha(min(255, self._text_alpha))
                text_rect = text_surf.get_rect(center=(sw // 2, sh // 2))
                surface.blit(text_surf, text_rect)


class ClickBounce:
    """
    Анимация отскока при клике на главную кнопку.
    Управляет масштабом объекта клика.
    """

    def __init__(self):
        self._scale = 1.0
        self._target = 1.0
        self._velocity = 0.0
        self._spring = 300.0    # жёсткость пружины
        self._damping = 8.0     # затухание

    @property
    def scale(self):
        return self._scale

    def trigger(self, strength=0.12):
        """Запускает анимацию отскока."""
        self._scale = 1.0 - strength
        self._velocity = 0

    def update(self, dt):
        """Обновляет пружинную анимацию."""
        # Пружинная формула
        displacement = self._scale - self._target
        acceleration = -self._spring * displacement - self._damping * self._velocity
        self._velocity += acceleration * dt
        self._scale += self._velocity * dt

        # Стабилизация
        if abs(self._scale - 1.0) < 0.001 and abs(self._velocity) < 0.01:
            self._scale = 1.0
            self._velocity = 0


class AnimationManager:
    """
    Менеджер анимаций.
    Управляет всеми активными анимациями.
    """

    def __init__(self):
        self.animations = {}  # id -> Animation
        self.click_bounce = ClickBounce()
        self.era_transition = None
        self.screen_shake = None

    def add(self, anim_id, animation):
        """Добавляет анимацию по ID."""
        self.animations[anim_id] = animation

    def remove(self, anim_id):
        """Удаляет анимацию по ID."""
        self.animations.pop(anim_id, None)

    def get(self, anim_id):
        """Возвращает анимацию по ID."""
        return self.animations.get(anim_id)

    def trigger_click(self, strength=0.12):
        """Запускает анимацию клика."""
        self.click_bounce.trigger(strength)

    def trigger_shake(self, intensity=5, duration=0.3):
        """Запускает тряску экрана."""
        self.screen_shake = ShakeAnimation(
            intensity=intensity, duration=duration
        )

    def trigger_era_transition(self, old_colors, new_colors,
                               duration=3.0, on_complete=None):
        """Запускает переход между эрами."""
        self.era_transition = EraTransition(
            old_colors, new_colors, duration, on_complete
        )

    def update(self, dt):
        """Обновляет все анимации."""
        # Именованные анимации
        dead_keys = []
        for key, anim in self.animations.items():
            anim.update(dt)
            if not anim.alive and not anim.loop:
                dead_keys.append(key)
        for key in dead_keys:
            del self.animations[key]

        # Специальные анимации.
        # click_bounce — только отклик на нажатие (в простое масштаб = 1.0).
        self.click_bounce.update(dt)

        if self.screen_shake:
            self.screen_shake.update(dt)
            if not self.screen_shake.alive:
                self.screen_shake = None

        if self.era_transition:
            self.era_transition.update(dt)
            if not self.era_transition.alive:
                self.era_transition = None

    @property
    def shake_offset(self):
        """Текущее смещение от тряски."""
        if self.screen_shake:
            return self.screen_shake.offset
        return 0, 0

    @property
    def is_transitioning(self):
        """Идёт ли переход эры."""
        return self.era_transition is not None

    def clear(self):
        """Очищает все анимации."""
        self.animations.clear()
        self.screen_shake = None
        self.era_transition = None
