"""Sky gradient, derived continuously from time-of-day + sunrise/sunset
rather than a hard day/night switch. Color interpolation only — no
astronomical simulation.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pygame

from app import palette
from app.weather.model import Astronomy, Condition

TRANSITION = timedelta(minutes=50)


def _phase_blend(now: datetime, astronomy: Astronomy) -> tuple[palette.Color, palette.Color]:
    sunrise, sunset = astronomy.sunrise, astronomy.sunset

    dawn_start, dawn_mid, dawn_end = sunrise - TRANSITION, sunrise, sunrise + TRANSITION
    dusk_start, dusk_mid, dusk_end = sunset - TRANSITION, sunset, sunset + TRANSITION

    def blend(a, b, t):
        top = palette.lerp_color(a[0], b[0], t)
        horizon = palette.lerp_color(a[1], b[1], t)
        return top, horizon

    if dawn_start <= now < dawn_mid:
        t = (now - dawn_start) / (dawn_mid - dawn_start)
        return blend(palette.SKY_NIGHT, palette.SKY_DAWN, t)
    if dawn_mid <= now < dawn_end:
        t = (now - dawn_mid) / (dawn_end - dawn_mid)
        return blend(palette.SKY_DAWN, palette.SKY_DAY, t)
    if dusk_start <= now < dusk_mid:
        t = (now - dusk_start) / (dusk_mid - dusk_start)
        return blend(palette.SKY_DAY, palette.SKY_DUSK, t)
    if dusk_mid <= now < dusk_end:
        t = (now - dusk_mid) / (dusk_end - dusk_mid)
        return blend(palette.SKY_DUSK, palette.SKY_NIGHT, t)
    if dawn_end <= now < dusk_start:
        return palette.SKY_DAY
    return palette.SKY_NIGHT


class SkyLayer:
    def __init__(self, size: tuple[int, int]):
        self.size = size
        self._surface = pygame.Surface(size)
        self._cache_key: tuple | None = None

    def configure(self, now: datetime, astronomy: Astronomy, condition: Condition) -> None:
        top, horizon = _phase_blend(now, astronomy)
        # Overcast/precipitation flattens and darkens the sky toward a
        # muted slate regardless of time of day.
        coverage = condition.cloud_coverage
        if coverage > 0.55:
            overcast_t = min(1.0, (coverage - 0.55) / 0.45) * 0.8
            top = palette.lerp_color(top, palette.SKY_DAY_OVERCAST[0], overcast_t)
            horizon = palette.lerp_color(horizon, palette.SKY_DAY_OVERCAST[1], overcast_t)

        key = (top, horizon)
        if key != self._cache_key:
            self._render(top, horizon)
            self._cache_key = key

        self.is_day = astronomy.is_day(now)
        self.coverage = coverage
        self.horizon_color = horizon

    def _render(self, top: palette.Color, horizon: palette.Color) -> None:
        w, h = self.size
        for y in range(h):
            t = y / max(1, h - 1)
            color = palette.lerp_color(top, horizon, t)
            pygame.draw.line(self._surface, color, (0, y), (w, y))

    def draw(self, target: pygame.Surface) -> None:
        target.blit(self._surface, (0, 0))
