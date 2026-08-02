"""
botyaraclick - screens/save_load.py
Экран выбора слотов сохранения.
Поддерживает: новая игра, загрузка, удаление.
"""

import pygame
import time

from ui.button import Button
from ui.panel import Panel
from ui.popup import PopupManager
from locales.locale_manager import t
from economy import format_money, format_time


class SaveLoadScreen:
    """Экран выбора слотов сохранения."""

    def __init__(self, screen_width, screen_height, save_manager,
                 sound_manager, mode="select"):
        """
        mode: "select" — выбор слота (показывает загрузить/новую игру)
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.save = save_manager
        self.sound = sound_manager
        self.mode = mode

        # Результат
        self.result = None  # {"action": "load"/"new", "slot": 1-5} или "back"
        self.finished = False

        # UI
        self._slot_buttons = []
        self._delete_buttons = []
        self._back_button = None
        self._popup_manager = PopupManager(screen_width, screen_height)

        # Шрифты
        self._title_font = None
        self._button_font = None
        self._info_font = None
        self._small_font = None

        # Анимации
        self._alpha = 0
        self._target_alpha = 255

        self._initialized = False
        self._pending_delete_slot = None

    def init_fonts(self, fonts_dict=None):
        """Инициализирует шрифты."""
        if fonts_dict:
            self._title_font = fonts_dict.get("title")
            self._button_font = fonts_dict.get("button")
            self._info_font = fonts_dict.get("normal")
            self._small_font = fonts_dict.get("small")

        if not self._title_font:
            self._title_font = pygame.font.Font(None, 42)
        if not self._button_font:
            self._button_font = pygame.font.Font(None, 26)
        if not self._info_font:
            self._info_font = pygame.font.Font(None, 20)
        if not self._small_font:
            self._small_font = pygame.font.Font(None, 16)

    def _init_ui(self):
        """Создаёт UI элементы."""
        if self._initialized:
            return

        if not self._button_font:
            self.init_fonts()

        self._rebuild_slots()

        # Кнопка "Назад"
        self._back_button = Button(
            self.screen_width // 2 - 100,
            self.screen_height - 80,
            200, 45,
            text=t("menu.back"),
            font=self._button_font,
            color=(80, 80, 100),
            hover_color=(100, 100, 125),
            border_radius=8,
            tag="back",
        )

        self._initialized = True

    def _rebuild_slots(self):
        """Перестраивает кнопки слотов."""
        self._slot_buttons.clear()
        self._delete_buttons.clear()

        slots = self.save.get_all_slots_info()

        slot_w = 500
        slot_h = 80
        gap = 12
        total_h = len(slots) * (slot_h + gap) - gap
        start_y = self.screen_height // 2 - total_h // 2 - 10
        cx = self.screen_width // 2

        for i, slot_data in enumerate(slots):
            slot_num = slot_data["slot"]
            exists = slot_data["exists"]
            info = slot_data["info"]

            # Определяем текст и цвет
            if exists and info:
                money_str = format_money(info.get("money", 0))
                time_str = format_time(info.get("play_time", 0))
                era_idx = info.get("current_era", 0)
                prestige = info.get("prestige_count", 0)

                text = f"{t('menu.slot', num=slot_num)}  |  {money_str}  |  {time_str}"
                if prestige > 0:
                    text += f"  |  P{prestige}"

                color = (50, 90, 140)
                hover = (65, 110, 170)
            else:
                text = f"{t('menu.slot', num=slot_num)}  —  {t('menu.empty_slot')}"
                color = (60, 60, 80)
                hover = (80, 80, 105)

            # Кнопка слота
            btn = Button(
                cx - slot_w // 2,
                start_y + i * (slot_h + gap),
                slot_w, slot_h,
                text=text,
                font=self._info_font or self._button_font,
                color=color,
                hover_color=hover,
                text_color=(220, 220, 235),
                border_radius=10,
                border_width=1,
                border_color=(80, 100, 130),
                tag={"slot": slot_num, "exists": exists},
            )
            self._slot_buttons.append(btn)

            # Кнопка удаления (если есть сохранение)
            if exists:
                del_btn = Button(
                    cx + slot_w // 2 + 10,
                    start_y + i * (slot_h + gap) + (slot_h - 35) // 2,
                    35, 35,
                    text="✕",
                    font=self._button_font,
                    color=(140, 50, 50),
                    hover_color=(180, 65, 65),
                    text_color=(255, 200, 200),
                    border_radius=6,
                    tag=slot_num,
                )
                self._delete_buttons.append(del_btn)

    def handle_event(self, event):
        """Обрабатывает события."""
        self._init_ui()

        # Попапы перехватывают события
        if self._popup_manager.has_popup:
            self._popup_manager.handle_event(
                event, self._button_font
            )
            return False

        # Кнопка назад
        if self._back_button and self._back_button.handle_event(event):
            self.result = "back"
            self._target_alpha = 0
            self.sound.play("click")
            return True

        # Кнопки слотов
        for btn in self._slot_buttons:
            if btn.handle_event(event):
                tag = btn.tag
                slot_num = tag["slot"]
                exists = tag["exists"]

                if exists:
                    # Загрузка
                    self.result = {"action": "load", "slot": slot_num}
                    self._target_alpha = 0
                else:
                    # Новая игра
                    self.result = {"action": "new", "slot": slot_num}
                    self._target_alpha = 0

                self.sound.play("click")
                return True

        # Кнопки удаления
        for btn in self._delete_buttons:
            if btn.handle_event(event):
                self._pending_delete_slot = btn.tag
                self._popup_manager.show_confirm(
                    title=t("menu.delete_save"),
                    message=t("menu.delete_confirm"),
                    on_result=self._on_delete_confirm,
                    yes_text=t("menu.yes"),
                    no_text=t("menu.no"),
                )
                self.sound.play("click")
                return True

        # ESC = назад
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.result = "back"
            self._target_alpha = 0
            return True

        return False

    def _on_delete_confirm(self, result):
        """Обработчик подтверждения удаления."""
        if result == "yes" and self._pending_delete_slot:
            self.save.delete_slot(self._pending_delete_slot)
            self.sound.play("click")
            self._rebuild_slots()
        self._pending_delete_slot = None

    def update(self, dt):
        """Обновляет экран."""
        self._init_ui()

        # Альфа
        speed = 400 * dt
        if self._alpha < self._target_alpha:
            self._alpha = min(self._alpha + speed, self._target_alpha)
        elif self._alpha > self._target_alpha:
            self._alpha = max(self._alpha - speed, self._target_alpha)

        if self.result and self._alpha <= 0:
            self.finished = True

        # Попапы
        mouse_pos = pygame.mouse.get_pos()
        self._popup_manager.update(dt, mouse_pos)

        # Кнопки
        for btn in self._slot_buttons:
            btn.update(dt, mouse_pos)
        for btn in self._delete_buttons:
            btn.update(dt, mouse_pos)
        if self._back_button:
            self._back_button.update(dt, mouse_pos)

    def draw(self, surface, theme=None):
        """Рисует экран."""
        self._init_ui()

        # Фон
        surface.fill((25, 25, 38))

        # Заголовок
        if self._title_font:
            title_text = t("menu.select_slot")
            title_surf = self._title_font.render(
                title_text, True, (200, 210, 230)
            )
            title_surf.set_alpha(int(self._alpha))
            title_rect = title_surf.get_rect(
                center=(self.screen_width // 2, 60)
            )
            surface.blit(title_surf, title_rect)

        # Слоты
        for btn in self._slot_buttons:
            btn.draw(surface, theme)

        # Кнопки удаления
        for btn in self._delete_buttons:
            btn.draw(surface, theme)

        # Назад
        if self._back_button:
            self._back_button.draw(surface, theme)

        # Попапы
        self._popup_manager.draw(surface, theme, self._button_font, self._title_font)

    def reset(self):
        """Сбрасывает экран."""
        self.result = None
        self.finished = False
        self._alpha = 0
        self._target_alpha = 255
        self._initialized = False
        self._slot_buttons.clear()
        self._delete_buttons.clear()

    def resize(self, width, height):
        """Обновляет размеры."""
        self.screen_width = width
        self.screen_height = height
        self._popup_manager.resize(width, height)
        self._initialized = False
        self._slot_buttons.clear()
        self._delete_buttons.clear()
