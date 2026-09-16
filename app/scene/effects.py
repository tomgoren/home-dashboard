"""Occasional flourishes layered on top of everything else: lightning and
small bird flocks. A natural home for future additions (fireflies,
leaves, ...).
"""

from __future__ import annotations

import math
import random

import pygame

from app import palette
from app.weather.model import Condition

_FLASH_INTERVAL_RANGE = (4.5, 11.0)  # seconds between flashes — atmospheric, not a strobe
_FLASH_DURATION = 0.12
_DOUBLE_FLASH_CHANCE = 0.3  # a quick second pulse, like a distant follow-up strike
_DOUBLE_FLASH_GAP = 0.1

# Birds only make sense in calm daylight — not storming, not the middle of
# the night.
_BIRD_CONDITIONS = frozenset({Condition.CLEAR, Condition.PARTLY_CLOUDY, Condition.CLOUDY})
_FLOCK_INTERVAL_RANGE = (20.0, 45.0)
_FLOCK_SIZE_RANGE = (3, 7)
_BIRD_SPEED_RANGE = (26.0, 44.0)  # px/s
_BIRD_COLOR = (32, 34, 46)


class EffectsLayer:
    def __init__(self, size: tuple[int, int]):
        self.size = size
        self._thunderstorm = False
        self._flash_timer = 0.0
        self._next_flash_in = random.uniform(*_FLASH_INTERVAL_RANGE)
        self._pending_second_flash = 0.0

        self._birds_enabled = False
        self._birds: list[list[float]] = []  # [x, y, wing_phase, bob_phase]
        self._bird_direction = 1
        self._bird_speed = 0.0
        self._next_flock_in = random.uniform(*_FLOCK_INTERVAL_RANGE)

    def configure(self, condition: Condition, is_day: bool) -> None:
        was_storm = self._thunderstorm
        self._thunderstorm = condition.is_thunderstorm
        if self._thunderstorm and not was_storm:
            self._next_flash_in = random.uniform(*_FLASH_INTERVAL_RANGE)

        self._birds_enabled = is_day and condition in _BIRD_CONDITIONS

    def update(self, dt: float) -> None:
        if self._flash_timer > 0:
            self._flash_timer -= dt

        if self._pending_second_flash > 0:
            self._pending_second_flash -= dt
            if self._pending_second_flash <= 0 and self._flash_timer <= 0:
                self._flash_timer = _FLASH_DURATION

        if self._thunderstorm:
            self._next_flash_in -= dt
            if self._next_flash_in <= 0:
                self._flash_timer = _FLASH_DURATION
                self._next_flash_in = random.uniform(*_FLASH_INTERVAL_RANGE)
                if random.random() < _DOUBLE_FLASH_CHANCE:
                    self._pending_second_flash = _DOUBLE_FLASH_GAP

        self._update_birds(dt)

    def _update_birds(self, dt: float) -> None:
        if self._birds_enabled and not self._birds:
            self._next_flock_in -= dt
            if self._next_flock_in <= 0:
                self._spawn_flock()
                self._next_flock_in = random.uniform(*_FLOCK_INTERVAL_RANGE)

        if not self._birds:
            return

        for bird in self._birds:
            bird[0] += self._bird_speed * self._bird_direction * dt
            bird[2] += dt * 6.0
            bird[3] += dt * 1.2

        margin = 40
        w = self.size[0]
        if self._bird_direction > 0 and min(b[0] for b in self._birds) - margin > w:
            self._birds = []
        elif self._bird_direction < 0 and max(b[0] for b in self._birds) + margin < 0:
            self._birds = []

    def _spawn_flock(self) -> None:
        w, h = self.size
        self._bird_direction = random.choice((1, -1))
        self._bird_speed = random.uniform(*_BIRD_SPEED_RANGE)
        start_x = -40.0 if self._bird_direction > 0 else w + 40.0
        base_y = random.uniform(h * 0.10, h * 0.30)
        n = random.randint(*_FLOCK_SIZE_RANGE)

        self._birds = []
        for i in range(n):
            offset_x = -i * 16 * self._bird_direction
            offset_y = abs(i - n // 2) * 8
            self._birds.append([
                start_x + offset_x,
                base_y + offset_y,
                random.uniform(0, math.tau),
                random.uniform(0, math.tau),
            ])

    def draw(self, target: pygame.Surface) -> None:
        for x, y, wing_phase, bob_phase in self._birds:
            flap = math.sin(wing_phase) * 5
            bob = math.sin(bob_phase) * 3
            cy = y + bob
            points = [(x - 7, cy - flap), (x, cy + 3), (x + 7, cy - flap)]
            pygame.draw.lines(target, _BIRD_COLOR, False, points, 2)

        if self._flash_timer > 0:
            alpha = round(180 * min(1.0, self._flash_timer / _FLASH_DURATION))
            flash = pygame.Surface(self.size, pygame.SRCALPHA)
            flash.fill((*palette.LIGHTNING_FLASH, alpha))
            target.blit(flash, (0, 0))
