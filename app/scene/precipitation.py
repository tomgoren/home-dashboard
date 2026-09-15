"""Rain, snow, and fog. One layer because a scene shows at most one of
these at a time, driven by the condition's intensity tiers.
"""

from __future__ import annotations

import math
import random

import pygame

from app import palette
from app.weather.model import Condition

MAX_RAIN_DROPS = 140
MAX_SNOW_FLAKES = 90


class PrecipitationLayer:
    def __init__(self, size: tuple[int, int]):
        self.size = size
        self._rain: list[list[float]] = []  # [x, y, length, speed]
        self._snow: list[list[float]] = []  # [x, y, radius, speed, sway_phase]
        self._fog_alpha = 0
        self._mode = "none"

    def configure(self, condition: Condition, wind_speed: float, wind_direction_deg: float) -> None:
        w, h = self.size
        # visual wind vector (downwind direction)
        angle = math.radians(wind_direction_deg + 180)
        self._wind_x = math.sin(angle)
        self._rain_slant = self._wind_x * min(1.0, wind_speed / 40.0)

        rain_i = condition.rain_intensity
        snow_i = condition.snow_intensity
        fog_i = condition.fog_intensity

        if rain_i > 0:
            self._mode = "rain"
            self._fog_alpha = 0
            target_n = round(MAX_RAIN_DROPS * rain_i)
            if len(self._rain) != target_n:
                rng = random.Random(42)
                self._rain = [
                    [rng.uniform(0, w), rng.uniform(0, h), rng.uniform(10, 22), rng.uniform(420, 620)]
                    for _ in range(target_n)
                ]
            self._rain_intensity = rain_i
        elif snow_i > 0:
            self._mode = "snow"
            self._fog_alpha = 0
            target_n = round(MAX_SNOW_FLAKES * snow_i)
            if len(self._snow) != target_n:
                rng = random.Random(7)
                self._snow = [
                    [
                        rng.uniform(0, w),
                        rng.uniform(0, h),
                        rng.uniform(1.5, 3.5),
                        rng.uniform(30, 70),
                        rng.uniform(0, math.tau),
                    ]
                    for _ in range(target_n)
                ]
        elif fog_i > 0:
            self._mode = "fog"
            self._fog_alpha = round(70 * fog_i)
        else:
            self._mode = "none"
            self._fog_alpha = 0

    def update(self, dt: float) -> None:
        w, h = self.size
        if self._mode == "rain":
            for drop in self._rain:
                drop[1] += drop[3] * dt
                drop[0] += drop[3] * self._rain_slant * dt
                if drop[1] > h:
                    drop[1] = -drop[2]
                    drop[0] = random.uniform(0, w)
                if drop[0] > w:
                    drop[0] -= w
                elif drop[0] < 0:
                    drop[0] += w
        elif self._mode == "snow":
            for flake in self._snow:
                flake[1] += flake[3] * dt
                flake[4] += dt * 1.4
                flake[0] += math.sin(flake[4]) * 18 * dt
                if flake[1] > h:
                    flake[1] = -flake[2]
                    flake[0] = random.uniform(0, w)

    def draw(self, target: pygame.Surface) -> None:
        if self._mode == "rain":
            for x, y, length, _speed in self._rain:
                dx = length * 0.35 * self._rain_slant
                pygame.draw.line(
                    target,
                    palette.RAIN_STREAK,
                    (x, y),
                    (x + dx, y + length),
                    1,
                )
        elif self._mode == "snow":
            for x, y, radius, *_ in self._snow:
                pygame.draw.circle(target, palette.SNOW_FLAKE, (round(x), round(y)), round(radius))
        elif self._mode == "fog" and self._fog_alpha:
            veil = pygame.Surface(self.size, pygame.SRCALPHA)
            veil.fill((*palette.FOG, self._fog_alpha))
            target.blit(veil, (0, 0))
