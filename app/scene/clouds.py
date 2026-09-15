"""Layered, parallax-drifting cloud clusters. Density and tint come from
the condition's cloud_coverage; drift speed/direction from wind.
"""

from __future__ import annotations

import math
import random

import pygame

from app import palette
from app.weather.model import Condition


class _Cloud:
    __slots__ = ("x", "y", "w", "h", "depth", "alpha", "puffs")

    def __init__(self, x: float, y: float, w: float, h: float, depth: float, alpha: int):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.depth = depth  # 0 = far/slow, 1 = near/fast
        self.alpha = alpha
        # Precomputed relative puff offsets so the cloud has a blocky,
        # hand-drawn silhouette instead of a single smooth ellipse.
        rng = random.Random(int(x * 1000) ^ int(w))
        count = rng.randint(4, 6)
        self.puffs = [
            (
                rng.uniform(-0.4, 0.4) * w,
                rng.uniform(-0.15, 0.25) * h,
                rng.uniform(0.35, 0.65) * w,
                rng.uniform(0.5, 0.9) * h,
            )
            for _ in range(count)
        ]


class CloudLayer:
    def __init__(self, size: tuple[int, int]):
        self.size = size
        self._clouds: list[_Cloud] = []
        self._condition: Condition | None = None
        self._drift_px_s = 0.0

    def configure(self, condition: Condition, wind_speed: float, wind_direction_deg: float) -> None:
        # wind_direction_deg is "coming from"; visual drift goes downwind.
        self._drift_px_s = max(4.0, wind_speed * 0.9)
        self._drift_dir = 1.0 if math.sin(math.radians(wind_direction_deg + 180)) >= 0 else -1.0
        self._storm = condition.is_thunderstorm

        if condition != self._condition:
            self._condition = condition
            self._regenerate(condition)

    def _regenerate(self, condition: Condition) -> None:
        w, h = self.size
        coverage = condition.cloud_coverage
        rng = random.Random(hash(condition.value))
        self._clouds = []
        if coverage <= 0.02:
            return

        band_top, band_bottom = h * 0.06, h * 0.38
        n_far = round(2 + coverage * 5)
        n_near = round(1 + coverage * 4)

        for _ in range(n_far):
            cw = rng.uniform(90, 160)
            ch = cw * rng.uniform(0.28, 0.4)
            self._clouds.append(
                _Cloud(
                    x=rng.uniform(0, w),
                    y=rng.uniform(band_top, band_top + (band_bottom - band_top) * 0.5),
                    w=cw,
                    h=ch,
                    depth=0.0,
                    alpha=round(120 + coverage * 60),
                )
            )
        for _ in range(n_near):
            cw = rng.uniform(130, 230)
            ch = cw * rng.uniform(0.3, 0.42)
            self._clouds.append(
                _Cloud(
                    x=rng.uniform(0, w),
                    y=rng.uniform(band_top + (band_bottom - band_top) * 0.4, band_bottom),
                    w=cw,
                    h=ch,
                    depth=1.0,
                    alpha=round(160 + coverage * 70),
                )
            )

    def update(self, dt: float) -> None:
        w, _ = self.size
        for cloud in self._clouds:
            speed = self._drift_px_s * (0.35 + 0.65 * cloud.depth)
            cloud.x += speed * self._drift_dir * dt
            if cloud.x - cloud.w > w:
                cloud.x = -cloud.w
            elif cloud.x + cloud.w < 0:
                cloud.x = w

    def draw(self, target: pygame.Surface) -> None:
        base_color = palette.CLOUD_STORM if self._storm else None
        for cloud in sorted(self._clouds, key=lambda c: c.depth):
            color = base_color or (palette.CLOUD_NEAR if cloud.depth > 0.5 else palette.CLOUD_FAR)
            cloud_surf = pygame.Surface((round(cloud.w * 2), round(cloud.h * 2.5)), pygame.SRCALPHA)
            cx, cy = cloud_surf.get_width() / 2, cloud_surf.get_height() / 2
            for ox, oy, pw, ph in cloud.puffs:
                rect = pygame.Rect(0, 0, round(pw), round(ph))
                rect.center = (round(cx + ox), round(cy + oy))
                pygame.draw.ellipse(cloud_surf, (*color, cloud.alpha), rect)
            target.blit(cloud_surf, (cloud.x - cx, cloud.y - cy))
