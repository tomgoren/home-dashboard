"""Occasional flourishes layered on top of everything else. Currently just
lightning; a natural home for future additions (fireflies, leaves, ...).
"""

from __future__ import annotations

import random

import pygame

from app import palette
from app.weather.model import Condition

_FLASH_INTERVAL_RANGE = (4.5, 11.0)  # seconds between flashes — atmospheric, not a strobe
_FLASH_DURATION = 0.12
_DOUBLE_FLASH_CHANCE = 0.3  # a quick second pulse, like a distant follow-up strike
_DOUBLE_FLASH_GAP = 0.1


class EffectsLayer:
    def __init__(self, size: tuple[int, int]):
        self.size = size
        self._thunderstorm = False
        self._flash_timer = 0.0
        self._next_flash_in = random.uniform(*_FLASH_INTERVAL_RANGE)
        self._pending_second_flash = 0.0

    def configure(self, condition: Condition) -> None:
        was_storm = self._thunderstorm
        self._thunderstorm = condition.is_thunderstorm
        if self._thunderstorm and not was_storm:
            self._next_flash_in = random.uniform(*_FLASH_INTERVAL_RANGE)

    def update(self, dt: float) -> None:
        if self._flash_timer > 0:
            self._flash_timer -= dt

        if self._pending_second_flash > 0:
            self._pending_second_flash -= dt
            if self._pending_second_flash <= 0 and self._flash_timer <= 0:
                self._flash_timer = _FLASH_DURATION

        if not self._thunderstorm:
            return

        self._next_flash_in -= dt
        if self._next_flash_in <= 0:
            self._flash_timer = _FLASH_DURATION
            self._next_flash_in = random.uniform(*_FLASH_INTERVAL_RANGE)
            if random.random() < _DOUBLE_FLASH_CHANCE:
                self._pending_second_flash = _DOUBLE_FLASH_GAP

    def draw(self, target: pygame.Surface) -> None:
        if self._flash_timer > 0:
            alpha = round(180 * min(1.0, self._flash_timer / _FLASH_DURATION))
            flash = pygame.Surface(self.size, pygame.SRCALPHA)
            flash.fill((*palette.LIGHTNING_FLASH, alpha))
            target.blit(flash, (0, 0))
