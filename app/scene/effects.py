"""Occasional flourishes layered on top of everything else. Currently just
lightning; a natural home for future additions (fireflies, leaves, ...).
"""

from __future__ import annotations

import random

import pygame

from app import palette
from app.weather.model import Condition

_FLASH_CHANCE_PER_SEC = 0.15
_FLASH_DURATION = 0.12


class EffectsLayer:
    def __init__(self, size: tuple[int, int]):
        self.size = size
        self._thunderstorm = False
        self._flash_timer = 0.0

    def configure(self, condition: Condition) -> None:
        self._thunderstorm = condition.is_thunderstorm

    def update(self, dt: float) -> None:
        if self._flash_timer > 0:
            self._flash_timer -= dt
            return
        if self._thunderstorm and random.random() < _FLASH_CHANCE_PER_SEC * dt * 10:
            self._flash_timer = _FLASH_DURATION

    def draw(self, target: pygame.Surface) -> None:
        if self._flash_timer > 0:
            alpha = round(180 * min(1.0, self._flash_timer / _FLASH_DURATION))
            flash = pygame.Surface(self.size, pygame.SRCALPHA)
            flash.fill((*palette.LIGHTNING_FLASH, alpha))
            target.blit(flash, (0, 0))
