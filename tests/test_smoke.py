"""
botyaraclick - tests/test_smoke.py
Дымовые тесты: шрифты, локализация, уведомления, меню паузы, кнопка клика.

Запуск:
    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

# Headless-режим — тесты работают без окна и звука
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

from config import FONTS_DIR, BOTTOM_PANEL_HEIGHT


def setUpModule():
    pygame.init()
    pygame.display.set_mode((1280, 720))


def tearDownModule():
    pygame.quit()


# =====================================================================
# 1. ЛОКАЛИЗАЦИЯ
# =====================================================================

class LocaleTests(unittest.TestCase):
    def setUp(self):
        from locales.locale_manager import LocaleManager
        self.locale = LocaleManager()
        self.assertTrue(self.locale.load_locale("ru"))

    def test_template_is_not_a_language(self):
        codes = [code for code, _ in self.locale.get_available_languages()]
        self.assertNotIn("template", codes)
        self.assertEqual(sorted(codes), ["en", "ru"])

    def test_listing_languages_keeps_current_locale(self):
        """Баг: после настроек всё превращалось в плейсхолдеры."""
        before_strings = self.locale.strings
        before_code = self.locale.current_locale

        self.locale.get_available_languages()

        self.assertIs(self.locale.strings, before_strings)
        self.assertEqual(self.locale.current_locale, before_code)

    def test_settings_strings_are_translated(self):
        for key in (
            "settings.title",
            "settings.effects_enabled",
            "settings.particles",
            "settings.floating_text",
            "settings.number_format",
        ):
            value = self.locale.get(key)
            self.assertTrue(value.strip(), f"{key} пустой")
            self.assertNotIn("[", value, f"{key} вернул плейсхолдер: {value}")

    def test_missing_key_never_returns_brackets(self):
        value = self.locale.get("settings.this_key_does_not_exist")
        self.assertTrue(value.strip())
        self.assertNotIn("[", value)
        self.assertNotIn("settings", value)

    def test_bracket_placeholders_are_resolved(self):
        """Строки вида "[settings.effects_enabled]" должны подставляться."""
        self.assertEqual(
            self.locale._resolve_refs("[settings.effects_enabled]"),
            self.locale.get("settings.effects_enabled"),
        )
        self.assertEqual(
            self.locale._resolve_refs("A [menu.play] B"),
            "A " + self.locale.get("menu.play") + " B",
        )

    def test_language_switch_roundtrip(self):
        ru_value = self.locale.get("settings.effects_enabled")
        self.assertTrue(self.locale.load_locale("en"))
        en_value = self.locale.get("settings.effects_enabled")
        self.assertNotEqual(ru_value, en_value)
        self.assertTrue(self.locale.load_locale("ru"))
        self.assertEqual(self.locale.get("settings.effects_enabled"), ru_value)

    def test_formatting_still_works(self):
        value = self.locale.get("pause.save")  # обычная строка без аргументов
        self.assertTrue(value)
        formatted = self.locale.get("prestige.current_rp", rp=5)
        self.assertIn("5", formatted)


# =====================================================================
# 2. ШРИФТЫ И ЭМОДЗИ
# =====================================================================

class FontTests(unittest.TestCase):
    def test_bundled_fonts_exist(self):
        required = [
            "Montserrat-Regular.ttf",
            "Montserrat-Bold.ttf",
            "NotoEmoji-Regular.ttf",
        ]
        for name in required:
            path = os.path.join(FONTS_DIR, name)
            self.assertTrue(os.path.exists(path), f"нет файла шрифта {name}")

    def test_theme_fonts_exist(self):
        from data.themes import THEME_FONTS
        for family, info in THEME_FONTS.items():
            for key in ("regular", "bold"):
                path = os.path.join(FONTS_DIR, info[key])
                self.assertTrue(
                    os.path.exists(path),
                    f"{family}: нет {info[key]}",
                )

    def test_emoji_falls_back_to_emoji_font(self):
        from ui.fonts import get_font
        font = get_font(28, family="Montserrat")
        layer = font._layer_for_cluster("🤮")
        self.assertEqual(
            layer, len(font._layers) - 1,
            "эмодзи должно рисоваться эмодзи-шрифтом (последний слой)",
        )
        self.assertGreater(font.size("🤮")[0], 0)

    def test_cyrillic_falls_back_in_latin_theme(self):
        """Orbitron без кириллицы — буквы должны браться из Montserrat."""
        from ui.fonts import get_font
        font = get_font(24, family="Orbitron")
        layer = font._layer_for_cluster("Ж")
        self.assertNotEqual(layer, 0, "кириллица должна уходить в фолбэк")
        self.assertEqual(font.size("Ж")[1], font.get_height())

    def test_mixed_string_renders(self):
        from ui.fonts import get_font
        font = get_font(20)
        surf = font.render("Привет 🚀 мир 🏆", True, (255, 255, 255))
        self.assertGreater(surf.get_width(), 10)
        self.assertGreater(surf.get_height(), 10)


# =====================================================================
# 3. МЕНЮ ПАУЗЫ
# =====================================================================

class PauseMenuTests(unittest.TestCase):
    def _build(self, w, h):
        from core.save_manager import SaveManager
        from core.sound_manager import SoundManager
        from locales.locale_manager import locale
        from screens.pause_menu import PauseMenuScreen
        from ui.fonts import load_theme_fonts

        locale.load_locale("ru")
        save = SaveManager()
        save.new_game(1)
        menu = PauseMenuScreen(w, h, save, SoundManager())
        menu.init_fonts(load_theme_fonts())
        menu._init_ui()
        return menu

    def test_buttons_fit_inside_panel(self):
        """Кнопка «Выйти»/«Главное меню» не должна вылезать за рамку."""
        for w, h in ((1280, 720), (1024, 600), (800, 480), (640, 400)):
            menu = self._build(w, h)
            panel = menu._panel_rect
            self.assertLessEqual(panel.bottom, h, f"{w}x{h}: панель ниже экрана")
            for bid, btn in menu._buttons.items():
                self.assertGreaterEqual(
                    btn.rect.top, panel.top,
                    f"{w}x{h}: {bid} выше панели",
                )
                self.assertLessEqual(
                    btn.rect.bottom, panel.bottom,
                    f"{w}x{h}: {bid} вылезает из панели",
                )
                self.assertGreaterEqual(btn.rect.left, panel.left)
                self.assertLessEqual(btn.rect.right, panel.right)

    def test_title_and_buttons_do_not_overlap(self):
        menu = self._build(1280, 720)
        first = min(menu._buttons.values(), key=lambda b: b.rect.top)
        self.assertGreater(first.rect.top, menu._title_pos[1])


# =====================================================================
# 4. УВЕДОМЛЕНИЯ
# =====================================================================

class NotificationTests(unittest.TestCase):
    def _manager(self, w=1280, h=720):
        from ui.fonts import get_font
        from ui.notification import NotificationManager
        return NotificationManager(w, h, font=get_font(16), small_font=get_font(16))

    def test_notifications_are_at_the_bottom(self):
        manager = self._manager()
        manager.add("Тест", icon="🏆")
        for _ in range(20):
            manager.update(1 / 60)

        notif = manager.notifications[0]
        self.assertGreater(notif.rect.top, 720 // 2, "уведомление должно быть снизу")
        self.assertLessEqual(
            notif.rect.bottom, 720 - BOTTOM_PANEL_HEIGHT,
            "уведомление не должно перекрывать нижнюю панель",
        )

    def test_click_dismisses_notification(self):
        manager = self._manager()
        notif = manager.add("Тест", icon="🏆")
        for _ in range(20):
            manager.update(1 / 60)

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=notif.rect.center
        )
        self.assertTrue(manager.handle_event(event), "клик должен обрабатываться")

        for _ in range(30):
            manager.update(1 / 60)
        self.assertFalse(notif.alive)

    def test_duration_is_short(self):
        manager = self._manager()
        notif = manager.add("Тест")
        self.assertLessEqual(notif.duration, 2.0)

        manager.add_achievement("Ачивка", "Описание")
        self.assertLessEqual(manager.notifications[0].duration, 3.0)

    def test_max_visible_is_small(self):
        manager = self._manager()
        self.assertLessEqual(manager.max_visible, 3)

    def test_queue_overflow(self):
        manager = self._manager()
        for i in range(6):
            manager.add(f"Сообщение {i}")
        self.assertLessEqual(len(manager.notifications), manager.max_visible)
        self.assertGreater(len(manager.queue), 0)


# =====================================================================
# 5. КНОПКА КЛИКА — БЕЗ ПУЛЬСАЦИИ В IDLE
# =====================================================================

class ClickButtonIdleTests(unittest.TestCase):
    def test_idle_frames_are_identical(self):
        from core.save_manager import SaveManager
        from core.sound_manager import SoundManager
        from locales.locale_manager import locale
        from screens.game_screen import GameScreen
        from ui.fonts import load_theme_fonts

        locale.load_locale("ru")
        save = SaveManager()
        save.new_game(1)
        screen = GameScreen(1280, 720, save, SoundManager(), locale)
        screen.init_fonts(load_theme_fonts())
        screen._init_ui()

        surface = pygame.Surface((1280, 720))
        cx, cy = screen._click_center
        r = screen._click_button_radius
        crop = pygame.Rect(cx - r - 24, cy - r - 24, 2 * r + 48, 2 * r + 48)

        screen.update(1 / 60)
        screen.draw(surface)
        first = pygame.image.tobytes(surface.subsurface(crop), "RGB")

        for _ in range(40):
            screen.update(1 / 60)
            screen.draw(surface)
            current = pygame.image.tobytes(surface.subsurface(crop), "RGB")
            self.assertEqual(first, current, "кнопка клика «пульсирует» в idle")

    def test_no_pulse_animation_applied(self):
        from effects.animations import AnimationManager
        manager = AnimationManager()
        self.assertFalse(
            hasattr(manager, "pulse"),
            "PulseAnimation не должен применяться к кнопке клика",
        )


# =====================================================================
# 6. ДИАЛОГИ (POPUP) — ВСЁ ДОЛЖНО ВЛЕЗАТЬ В ОКНО
# =====================================================================

class PopupLayoutTests(unittest.TestCase):
    CHOICES = [
        {"text": "Сохранить и выйти", "value": "save_quit"},
        {"text": "Выйти без сохранения", "value": "no_save", "danger": True},
        {"text": "Отмена", "value": "cancel", "neutral": True},
    ]

    def _build(self, w, h):
        from data.themes import get_theme
        from ui.popup import Popup
        from ui.fonts import load_theme_fonts

        fonts = load_theme_fonts()
        popup = Popup(
            title="Вернуться в главное меню?",
            message="Есть несохранённый прогресс! Он будет потерян.",
            popup_type="choice",
            buttons=[dict(c) for c in self.CHOICES],
            width=500,
        )
        popup._alpha = 255
        popup._scale = 1.0
        surface = pygame.Surface((w, h))
        popup.draw(surface, get_theme("default"),
                   fonts.get("button"), fonts.get("title"))
        return popup

    def test_dialog_and_buttons_fit_screen(self):
        """Окно и все кнопки целиком помещаются в экран."""
        for w, h in ((1280, 720), (1024, 768), (900, 600), (800, 480),
                     (640, 480), (1024, 300)):
            popup = self._build(w, h)
            panel = popup._panel_rect
            self.assertGreaterEqual(panel.left, 0, f"{w}x{h}: панель слева за экраном")
            self.assertGreaterEqual(panel.top, 0, f"{w}x{h}: панель сверху за экраном")
            self.assertLessEqual(panel.right, w, f"{w}x{h}: панель справа за экраном")
            self.assertLessEqual(panel.bottom, h, f"{w}x{h}: панель снизу за экраном")

            for btn in popup._buttons:
                self.assertGreaterEqual(
                    btn.rect.left, panel.left,
                    f"{w}x{h}: «{btn.text}» вылезает влево")
                self.assertLessEqual(
                    btn.rect.right, panel.right,
                    f"{w}x{h}: «{btn.text}» вылезает вправо")
                self.assertGreaterEqual(
                    btn.rect.top, panel.top,
                    f"{w}x{h}: «{btn.text}» вылезает вверх")
                self.assertLessEqual(
                    btn.rect.bottom, panel.bottom,
                    f"{w}x{h}: «{btn.text}» вылезает вниз")

    def test_buttons_do_not_overlap(self):
        popup = self._build(1280, 720)
        rects = [b.rect for b in popup._buttons]
        for i, rect in enumerate(rects):
            for other in rects[i + 1:]:
                self.assertFalse(rect.colliderect(other), "кнопки диалога накладываются")

    def test_button_labels_fit_their_buttons(self):
        """Текст кнопки не шире самой кнопки (иначе он вылезал за края)."""
        popup = self._build(1280, 720)
        for btn in popup._buttons:
            text_w = btn.font.size(btn.text)[0]
            self.assertLessEqual(
                text_w, btn.rect.width,
                f"подпись «{btn.text}» шире кнопки",
            )


# =====================================================================
# 7. ПРОКРУТКА СПИСКОВ В ПАУЗЕ
# =====================================================================

class SubScreenScrollTests(unittest.TestCase):
    def _menu(self, w=1024, h=600):
        from core.save_manager import SaveManager
        from core.sound_manager import SoundManager
        from locales.locale_manager import locale
        from screens.pause_menu import PauseMenuScreen
        from ui.fonts import load_theme_fonts
        from data.themes import get_theme

        locale.load_locale("ru")
        save = SaveManager()
        save.new_game(1)
        menu = PauseMenuScreen(w, h, save, SoundManager())
        menu.init_fonts(load_theme_fonts())
        menu._init_ui()
        menu._panel_alpha = 255
        menu._theme = get_theme("default")
        menu._surface = pygame.Surface((w, h))
        self._w, self._h = w, h
        return menu

    def _frame(self, menu):
        menu.update(1 / 60)
        menu._surface.fill((20, 20, 30))
        menu.draw(menu._surface, menu._theme)

    def _wheel(self, menu, y=-1):
        event = pygame.event.Event(
            pygame.MOUSEWHEEL, x=0, y=y, flipped=False, which=0,
            touch=False, precise_x=0.0, precise_y=float(y),
        )
        menu.handle_event(event)

    def test_wheel_scrolls_without_closing(self):
        for screen in ("achievements", "statistics"):
            menu = self._menu(1024, 400)
            menu._handle_button(screen)
            self._frame(menu)

            self._wheel(menu)
            self._frame(menu)

            self.assertEqual(
                menu._sub_screen, screen,
                f"{screen}: колесо мыши закрыло список",
            )
            self.assertGreater(menu._sub_scroll, 0, f"{screen}: колесо не листает")

    def test_legacy_wheel_buttons_do_not_close(self):
        """Колесо под видом кнопок 4/5 не должно закрывать список."""
        menu = self._menu(1024, 400)
        menu._handle_button("achievements")
        self._frame(menu)

        for button in (4, 5):
            menu.handle_event(pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, button=button, pos=(menu._sub_panel_rect.center)
            ))
        self.assertEqual(menu._sub_screen, "achievements")

    def test_drag_scrolls_list(self):
        menu = self._menu(1024, 400)
        menu._handle_button("achievements")
        self._frame(menu)

        center = menu._sub_panel_rect.center
        menu.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=center
        ))
        self.assertEqual(menu._sub_screen, "achievements",
                         "нажатие внутри списка закрыло его")
        self.assertTrue(menu._sub_dragging)

        menu.handle_event(pygame.event.Event(
            pygame.MOUSEMOTION, pos=(center[0], center[1] - 80),
            rel=(0, -80), buttons=(1, 0, 0),
        ))
        self._frame(menu)
        self.assertGreater(menu._sub_scroll, 0, "перетаскивание не листает")

        menu.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONUP, button=1, pos=(center[0], center[1] - 80)
        ))
        self.assertFalse(menu._sub_dragging)

    def test_click_outside_closes(self):
        menu = self._menu(1024, 400)
        menu._handle_button("achievements")
        self._frame(menu)

        menu.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=(2, 2)
        ))
        self.assertIsNone(menu._sub_screen)

    def test_scroll_is_clamped(self):
        menu = self._menu(1024, 400)
        menu._handle_button("achievements")
        self._frame(menu)

        for _ in range(200):
            self._wheel(menu)
        self._frame(menu)
        self.assertLessEqual(menu._sub_scroll, menu._sub_max_scroll)
        self.assertGreaterEqual(menu._sub_scroll, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
