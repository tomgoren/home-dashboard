"""Sun, moon, and stars. Positions are an approximate arc across the sky
between sunrise/sunset (or sunset/sunrise for the moon), not an
astronomical simulation.
"""

from __future__ import annotations

import math
import random
from datetime import datetime

import pygame

from app import palette
from app.weather.model import Astronomy

_STAR_COUNT = 60


class CelestialLayer:
    def __init__(self, size: tuple[int, int]):
        self.size = size
        rng = random.Random(1)
        w, h = size
        band_h = h * 0.55
        self._stars = [
            (rng.uniform(0, w), rng.uniform(0, band_h), rng.uniform(0.6, 1.0), rng.uniform(0, math.tau))
            for _ in range(_STAR_COUNT)
        ]
        self._t = 0.0

    def configure(self, now: datetime, astronomy: Astronomy, cloud_coverage: float) -> None:
        self._now = now
        self._astronomy = astronomy
        # Visibility fades out as cloud cover thickens rather than an
        # abrupt on/off switch.
        self._visibility = max(0.0, 1.0 - cloud_coverage / 0.7)

    def update(self, dt: float) -> None:
        self._t += dt

    def _arc_position(self, start: datetime, end: datetime, now: datetime) -> tuple[float, float] | None:
        total = (end - start).total_seconds()
        if total <= 0:
            return None
        elapsed = (now - start).total_seconds()
        if not (0 <= elapsed <= total):
            return None
        t = elapsed / total
        w, h = self.size
        x = w * t
        y = h * 0.62 - math.sin(t * math.pi) * h * 0.5
        return x, y

    def draw(self, target: pygame.Surface) -> None:
        if self._visibility <= 0.02:
            return

        astro = self._astronomy
        now = self._now
        is_day = astro.is_day(now)

        if is_day:
            pos = self._arc_position(astro.sunrise, astro.sunset, now)
            if pos:
                self._draw_glow_disc(target, pos, palette.SUN, radius=26, glow=1.6)
        else:
            # star field, twinkling
            alpha_base = round(210 * self._visibility)
            for x, y, brightness, phase in self._stars:
                twinkle = 0.6 + 0.4 * math.sin(self._t * 1.6 + phase)
                a = max(0, min(255, round(alpha_base * brightness * twinkle)))
                if a <= 0:
                    continue
                s = pygame.Surface((2, 2), pygame.SRCALPHA)
                s.fill((*palette.STAR, a))
                target.blit(s, (round(x), round(y)))

            # moon arcs opposite the sun: sunset -> next sunrise
            from datetime import timedelta

            next_sunrise = astro.sunrise if now < astro.sunrise else astro.sunrise + timedelta(days=1)
            pos = self._arc_position(astro.sunset, next_sunrise, now)
            if pos:
                self._draw_glow_disc(target, pos, palette.MOON, radius=18, glow=1.3, alpha_scale=self._visibility)

    def _draw_glow_disc(self, target, pos, color, radius, glow, alpha_scale=1.0):
        x, y = pos
        glow_r = round(radius * glow * 1.8)
        halo = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        for r in range(glow_r, radius, -2):
            a = round(30 * (1 - (r - radius) / max(1, glow_r - radius)) * alpha_scale)
            pygame.draw.circle(halo, (*color, a), (glow_r, glow_r), r)
        target.blit(halo, (x - glow_r, y - glow_r))
        pygame.draw.circle(target, color, (round(x), round(y)), radius)
