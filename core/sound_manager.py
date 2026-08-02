"""
botyaraclick - core/sound_manager.py
Менеджер звуков и музыки.

Корректно обрабатывает отсутствие звуковых файлов —
игра работает и без них.
"""

import pygame
import os

from config import SOUNDS_DIR, MUSIC_DIR


class SoundManager:
    """Менеджер звуков и музыки."""

    def __init__(self):
        self._sounds = {}
        self._music_loaded = False
        self._current_music = None

        self.sfx_volume = 0.7
        self.music_volume = 0.7
        self.muted = False

        self._initialized = False
        self._init_mixer()

    def _init_mixer(self):
        """Инициализирует аудио-микшер."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._initialized = True
        except pygame.error as e:
            print(f"[SoundManager] Could not initialize mixer: {e}")
            self._initialized = False

    def load_all_sounds(self):
        """Загружает все звуковые файлы."""
        if not self._initialized:
            return

        sound_files = {
            "click": "click.wav",
            "click_crit": "click_crit.wav",
            "buy": "buy.wav",
            "error": "error.wav",
            "achievement": "achievement.wav",
            "era_up": "era_up.wav",
            "golden_appear": "golden_appear.wav",
            "golden_catch": "golden_catch.wav",
            "golden_miss": "golden_miss.wav",
            "event_positive": "event_positive.wav",
            "event_negative": "event_negative.wav",
            "event_choice": "event_choice.wav",
            "deal_won": "deal_won.wav",
            "deal_lost": "deal_lost.wav",
            "pause": "pause.wav",
            "save": "save.wav",
            "prestige": "prestige.wav",
            "theme_change": "theme_change.wav",
            "hover": "hover.wav",
            "challenge_tick": "challenge_tick.wav",
        }

        for sound_id, filename in sound_files.items():
            self._load_sound(sound_id, filename)

    def _load_sound(self, sound_id, filename):
        """Загружает один звуковой файл."""
        path = os.path.join(SOUNDS_DIR, filename)
        if os.path.exists(path):
            try:
                sound = pygame.mixer.Sound(path)
                self._sounds[sound_id] = sound
            except pygame.error as e:
                print(f"[SoundManager] Could not load {filename}: {e}")
        # Если файла нет — просто не загружаем, без ошибок

    def play(self, sound_id, volume_mult=1.0):
        """
        Воспроизводит звук.
        Если звук не загружен — ничего не делает.
        """
        if not self._initialized or self.muted:
            return

        sound = self._sounds.get(sound_id)
        if sound:
            volume = self.sfx_volume * volume_mult
            sound.set_volume(max(0.0, min(1.0, volume)))
            sound.play()

    def play_music(self, music_id):
        """
        Начинает воспроизведение музыки.
        music_id: "menu_theme", "game_theme", "prestige_theme"
        """
        if not self._initialized or self.muted:
            return

        filename = f"{music_id}.ogg"
        path = os.path.join(MUSIC_DIR, filename)

        if not os.path.exists(path):
            # Пробуем .wav
            filename = f"{music_id}.wav"
            path = os.path.join(MUSIC_DIR, filename)

        if not os.path.exists(path):
            return

        try:
            if self._current_music == music_id:
                return  # Уже играет

            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(
                max(0.0, min(1.0, self.music_volume))
            )
            pygame.mixer.music.play(-1)  # Зацикливаем
            self._current_music = music_id
        except pygame.error as e:
            print(f"[SoundManager] Could not play music {filename}: {e}")

    def stop_music(self, fadeout_ms=1000):
        """Останавливает музыку с затуханием."""
        if not self._initialized:
            return

        try:
            pygame.mixer.music.fadeout(fadeout_ms)
            self._current_music = None
        except pygame.error:
            pass

    def set_sfx_volume(self, volume):
        """Устанавливает громкость эффектов (0.0 - 1.0)."""
        self.sfx_volume = max(0.0, min(1.0, volume))

    def set_music_volume(self, volume):
        """Устанавливает громкость музыки (0.0 - 1.0)."""
        self.music_volume = max(0.0, min(1.0, volume))
        if self._initialized:
            try:
                pygame.mixer.music.set_volume(self.music_volume)
            except pygame.error:
                pass

    def set_muted(self, muted):
        """Включает/выключает звук."""
        self.muted = muted
        if muted:
            try:
                pygame.mixer.music.pause()
            except pygame.error:
                pass
        else:
            try:
                pygame.mixer.music.unpause()
            except pygame.error:
                pass

    def pause_music(self):
        """Ставит музыку на паузу."""
        if self._initialized:
            try:
                pygame.mixer.music.pause()
            except pygame.error:
                pass

    def unpause_music(self):
        """Снимает музыку с паузы."""
        if self._initialized and not self.muted:
            try:
                pygame.mixer.music.unpause()
            except pygame.error:
                pass
