"""
botyaraclick - effects package
Визуальные эффекты: частицы, всплывающий текст, анимации, фоновые эффекты.
"""

from effects.particles import ParticleSystem
from effects.floating_text import FloatingTextManager
from effects.animations import AnimationManager
from effects.bg_effects import BackgroundEffectManager

__all__ = [
    "ParticleSystem", "FloatingTextManager",
    "AnimationManager", "BackgroundEffectManager"
]
