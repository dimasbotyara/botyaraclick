"""
botyaraclick - screens/main_menu.py
Главное меню игры с анимированным фоном и стильными кнопками.
"""

import pygame
import math
import random
import time

from ui.button import Button
from ui.panel import Panel
from locales.locale_manager import t
from ui.fonts import get_font


class MainMenuScreen:
    """Главное меню игры."""

    def __init__(self, screen_width, screen_height, save_manager, sound_manager):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.save = save_manager
        self.sound = sound_manager

        # Результат (что делать после меню)
        self.result = None  # "play", "continue", "settings", "quit"
        self.finished = False

        # Анимации
        self._alpha = 0
        self._target_alpha = 255
        self._title_phase = 0
        self._bg_code_lines = []
        self._bg_particles = []

        # Шрифты
        self._title_font = None
        self._subtitle_font = None
        self._button_font = None
        self._small_font = None
        self._code_font = None

        # Кнопки
        self._buttons = {}
        self._initialized = False

        # Генерируем фоновые элементы
        self._generate_bg()

    def _generate_bg(self):
        """Генерирует анимированный фон."""
        # Строки кода на фоне
        code_snippets = [
            "import startup", "from garage import *",
            "class Business:", "    def grow(self):",
            "        self.money += 1", "    def hire(self):",
            "        team.append(dev)", "while True:",
            "    if click:", "        earn_money()",
            "# TODO: world domination", "deploy(production)",
            "git push origin main", "pip install success",
            "async def make_profit():", "    await future",
            "try:", "    become_rich()", "except Crisis:",
            "    keep_clicking()", "return billions",
            "def prestige():", "    reset()", "    bonus *= 2",
            "server.scale(infinity)", "ai.train(model)",
            "launch(rocket)", "terraform(mars)",
        ]

        for i in range(30):
            self._bg_code_lines.append({
                "text": random.choice(code_snippets),
                "x": random.uniform(-100, self.screen_width + 100),
                "y": random.uniform(0, self.screen_height),
                "speed": random.uniform(15, 50),
                "alpha": random.randint(15, 40),
                "size": random.randint(12, 16),
            })

        # Частицы-точки
        for _ in range(50):
            self._bg_particles.append({
                "x": random.uniform(0, self.screen_width),
                "y": random.uniform(0, self.screen_height),
                "size": random.uniform(1, 3),
                "alpha": random.randint(30, 80),
                "phase": random.uniform(0, math.pi * 2),
                "speed": random.uniform(1, 4),
            })

    def init_fonts(self, fonts_dict=None):
        """Инициализирует шрифты."""
        if fonts_dict:
            self._title_font = fonts_dict.get("title")
            self._subtitle_font = fonts_dict.get("subtitle")
            self._button_font = fonts_dict.get("button")
            self._small_font = fonts_dict.get("small")
        
        if not self._title_font:
            self._title_font = get_font(72, bold=True)
        if not self._subtitle_font:
            self._subtitle_font = get_font(24)
        if not self._button_font:
            self._button_font = get_font(30)
        if not self._small_font:
            self._small_font = get_font(18)

        self._code_font = get_font(14, family="FiraCode")

    def _init_buttons(self):
        """Создаёт кнопки меню."""
        if self._initialized:
            return

        if not self._button_font:
            self.init_fonts()

        cx = self.screen_width // 2
        btn_w = 280
        btn_h = 55
        gap = 15
        start_y = self.screen_height // 2 + 20

        has_saves = self.save.has_any_save()

        buttons_list = []

        if has_saves:
            buttons_list.append({
                "id": "continue",
                "text": t("menu.continue"),
                "color": (50, 140, 80),
                "hover_color": (60, 170, 95),
            })

        buttons_list.append({
            "id": "play",
            "text": t("menu.play"),
            "color": (50, 100, 200),
            "hover_color": (70, 130, 240),
        })

        buttons_list.append({
            "id": "settings",
            "text": t("menu.settings"),
            "color": (70, 70, 90),
            "hover_color": (90, 90, 115),
        })

        buttons_list.append({
            "id": "quit",
            "text": t("menu.quit"),
            "color": (140, 50, 50),
            "hover_color": (170, 65, 65),
        })

        total_h = len(buttons_list) * (btn_h + gap) - gap
        start_y = self.screen_height // 2 + 30 - total_h // 2 + 50

        for i, bdef in enumerate(buttons_list):
            btn = Button(
                cx - btn_w // 2,
                start_y + i * (btn_h + gap),
                btn_w, btn_h,
                text=bdef["text"],
                font=self._button_font,
                color=bdef["color"],
                hover_color=bdef["hover_color"],
                text_color=(230, 230, 240),
                border_radius=10,
                tag=bdef["id"],
            )
            self._buttons[bdef["id"]] = btn

        self._initialized = True

    def handle_event(self, event):
        """Обрабатывает события."""
        self._init_buttons()

        for btn_id, btn in self._buttons.items():
            if btn.handle_event(event):
                self.result = btn_id
                self._target_alpha = 0  # Затухание
                self.sound.play("click")
                return True

        return False

    def update(self, dt):
        """Обновляет экран."""
        self._init_buttons()

        # Альфа
        speed = 350 * dt
        if self._alpha < self._target_alpha:
            self._alpha = min(self._alpha + speed, self._target_alpha)
        elif self._alpha > self._target_alpha:
            self._alpha = max(self._alpha - speed * 1.5, self._target_alpha)

        if self.result and self._alpha <= 0:
            self.finished = True

        # Анимация заголовка
        self._title_phase += dt * 1.5

        # Анимация фона
        for line in self._bg_code_lines:
            line["y"] += line["speed"] * dt
            if line["y"] > self.screen_height + 30:
                line["y"] = -20
                line["x"] = random.uniform(-100, self.screen_width + 100)
                line["speed"] = random.uniform(15, 50)

        for p in self._bg_particles:
            p["phase"] += p["speed"] * dt

        # Кнопки
        mouse_pos = pygame.mouse.get_pos()
        for btn in self._buttons.values():
            btn.update(dt, mouse_pos)

    def draw(self, surface):
        """Рисует главное меню."""
        self._init_buttons()

        # Фон
        self._draw_background(surface)

        alpha_ratio = max(0, self._alpha / 255.0)

        # Заголовок "botyaraclick"
        self._draw_title(surface, alpha_ratio)

        # Подзаголовок
        if self._subtitle_font:
            sub_text = self._subtitle_font.render(
                "From Garage to Galaxy", True, (120, 140, 180)
            )
            sub_text.set_alpha(int(self._alpha * 0.8))
            sub_rect = sub_text.get_rect(
                center=(self.screen_width // 2,
                        self.screen_height // 2 - 40)
            )
            surface.blit(sub_text, sub_rect)

        # Кнопки
        for btn in self._buttons.values():
            btn.draw(surface)

        # Версия и автор
        if self._small_font:
            ver_text = self._small_font.render(
                "v1.0.0 | by dimasbotyara", True, (80, 80, 100)
            )
            ver_text.set_alpha(int(self._alpha * 0.6))
            ver_rect = ver_text.get_rect(
                midbottom=(self.screen_width // 2,
                           self.screen_height - 15)
            )
            surface.blit(ver_text, ver_rect)

    def _draw_background(self, surface):
        """Рисует анимированный фон."""
        # Градиент
        for y in range(self.screen_height):
            t_val = y / self.screen_height
            r = int(15 + 15 * t_val)
            g = int(15 + 10 * t_val)
            b = int(30 + 15 * t_val)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.screen_width, y))

        # Строки кода
        if self._code_font:
            for line in self._bg_code_lines:
                text_surf = self._code_font.render(
                    line["text"], True, (40, 50, 80)
                )
                text_surf.set_alpha(line["alpha"])
                surface.blit(text_surf, (int(line["x"]), int(line["y"])))

        # Частицы
        for p in self._bg_particles:
            brightness = (math.sin(p["phase"]) + 1) / 2
            alpha = int(p["alpha"] * brightness)
            if alpha > 5:
                r = max(1, int(p["size"]))
                particle_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    particle_surf,
                    (100, 130, 200, alpha),
                    (r, r), r
                )
                surface.blit(particle_surf,
                             (int(p["x"]) - r, int(p["y"]) - r))

    def _draw_title(self, surface, alpha_ratio):
        """Рисует анимированный заголовок."""
        if not self._title_font:
            return

        # Пульсация масштаба
        pulse = 1.0 + math.sin(self._title_phase) * 0.02
        title_y = self.screen_height // 2 - 100

        # Свечение за заголовком
        glow_alpha = int(40 * alpha_ratio * ((math.sin(self._title_phase * 0.7) + 1) / 2))
        if glow_alpha > 0:
            glow_surf = pygame.Surface(
                (400, 60), pygame.SRCALPHA
            )
            pygame.draw.ellipse(
                glow_surf,
                (50, 100, 255, glow_alpha),
                (0, 0, 400, 60)
            )
            glow_rect = glow_surf.get_rect(
                center=(self.screen_width // 2, title_y)
            )
            surface.blit(glow_surf, glow_rect)

        # Заголовок
        title_surf = self._title_font.render(
            "botyaraclick", True, (80, 160, 255)
        )
        title_surf.set_alpha(int(self._alpha))

        # Масштабирование
        if pulse != 1.0:
            new_w = int(title_surf.get_width() * pulse)
            new_h = int(title_surf.get_height() * pulse)
            title_surf = pygame.transform.smoothscale(
                title_surf, (new_w, new_h)
            )

        title_rect = title_surf.get_rect(
            center=(self.screen_width // 2, title_y)
        )
        surface.blit(title_surf, title_rect)

    def reset(self):
        """Сбрасывает состояние меню для повторного показа."""
        self.result = None
        self.finished = False
        self._alpha = 0
        self._target_alpha = 255
        self._buttons.clear()
        self._initialized = False

    def resize(self, width, height):
        """Обновляет размеры."""
        self.screen_width = width
        self.screen_height = height
        self._buttons.clear()
        self._initialized = False
        self._bg_code_lines.clear()
        self._bg_particles.clear()
        self._generate_bg()
