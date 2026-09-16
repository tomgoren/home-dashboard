"""A stylized landscape silhouette between the sky and the forecast strip —
Pacific Northwest flavored (a Hood-like snow-capped peak, forested
foothills, a river catching the sky's light through the valley) rather
than a literal/photographic backdrop. Static geometry, colored each frame
from the sky's own current horizon color so it stays consistent through
every time-of-day and weather blend without its own separate palette
logic.
"""

from __future__ import annotations

import math
import random

import pygame

from app import palette

# Silhouette polygons as (x, y) fractions of canvas size — hand-placed, not
# procedural, so the skyline reads as an actual place rather than noise.
# Everything is kept above y=0.78 so it never competes with the forecast
# strip that starts at 0.80.
_FAR_RIDGE = [
    (0.0, 0.72), (0.10, 0.62), (0.20, 0.66), (0.30, 0.58),
    (0.38, 0.63), (0.46, 0.44), (0.54, 0.58), (0.62, 0.63),
    (0.72, 0.56), (0.82, 0.64), (0.92, 0.59), (1.0, 0.66),
    (1.0, 0.78), (0.0, 0.78),
]
_NEAR_RIDGE = [
    (0.0, 0.76), (0.09, 0.71), (0.18, 0.74), (0.27, 0.69),
    (0.36, 0.73), (0.46, 0.68), (0.56, 0.72), (0.66, 0.67),
    (0.76, 0.72), (0.86, 0.68), (1.0, 0.73),
    (1.0, 0.78), (0.0, 0.78),
]
_SNOW_CAP = [(0.435, 0.475), (0.46, 0.44), (0.485, 0.475), (0.46, 0.485)]

# Treeline clusters avoid the peak itself — no trees above the snowline.
_TREE_X_RANGES = [(0.02, 0.34), (0.58, 0.98)]
_TREE_BASE_Y = 0.775

# A narrow, gently meandering ribbon nestled in the saddle between the two
# ridgelines, visible only through the valley gap — not a literal
# foreground river reaching the bottom of the frame. Left edge top-to-
# bottom, then right edge bottom-to-top, so the polygon traces a soft S.
_RIVER = [
    (0.452, 0.50), (0.444, 0.56), (0.459, 0.62), (0.447, 0.685),
    (0.469, 0.685), (0.480, 0.62), (0.463, 0.56), (0.471, 0.50),
]


def _darken(color: palette.Color, t: float, tint: palette.Color = (10, 13, 22)) -> palette.Color:
    return palette.lerp_color(color, tint, t)


def _lighten(color: palette.Color, t: float, tint: palette.Color = (255, 255, 255)) -> palette.Color:
    return palette.lerp_color(color, tint, t)


class HorizonLayer:
    def __init__(self, size: tuple[int, int]):
        self.size = size
        w, h = size
        self._far_poly = [(x * w, y * h) for x, y in _FAR_RIDGE]
        self._near_poly = [(x * w, y * h) for x, y in _NEAR_RIDGE]
        self._snow_poly = [(x * w, y * h) for x, y in _SNOW_CAP]
        self._river_poly = [(x * w, y * h) for x, y in _RIVER]

        rng = random.Random(7)
        self._trees: list[tuple[float, float, float]] = []  # x, y, size
        for x0, x1 in _TREE_X_RANGES:
            x = x0
            while x < x1:
                tx = x * w
                ty = (_TREE_BASE_Y + rng.uniform(-0.015, 0.02)) * h
                tsize = rng.uniform(10, 18)
                self._trees.append((tx, ty, tsize))
                x += rng.uniform(0.018, 0.035)

        self._shimmer_t = 0.0
        self._horizon_color: palette.Color = (60, 66, 82)

    def configure(self, horizon_color: palette.Color) -> None:
        self._horizon_color = horizon_color

    def update(self, dt: float) -> None:
        self._shimmer_t += dt

    def draw(self, target: pygame.Surface) -> None:
        c = self._horizon_color
        far_color = _darken(c, 0.35, tint=(35, 45, 65))
        near_color = _darken(c, 0.6, tint=(15, 20, 30))
        tree_color = _darken(c, 0.78, tint=(14, 22, 16))
        snow_color = _lighten(c, 0.6)
        river_color = _lighten(c, 0.22)

        pygame.draw.polygon(target, far_color, self._far_poly)
        pygame.draw.polygon(target, snow_color, self._snow_poly)

        # Soft/translucent rather than a flat opaque fill — reads as water
        # catching the sky's light, not a solid pale wedge.
        river_veil = pygame.Surface(self.size, pygame.SRCALPHA)
        pygame.draw.polygon(river_veil, (*river_color, 165), self._river_poly)
        target.blit(river_veil, (0, 0))

        pygame.draw.polygon(target, near_color, self._near_poly)

        for tx, ty, tsize in self._trees:
            points = [(tx, ty - tsize), (tx - tsize * 0.4, ty), (tx + tsize * 0.4, ty)]
            pygame.draw.polygon(target, tree_color, points)

        # one or two small drifting glints, not full-width bars — a hint of
        # sparkle rather than a ladder of rungs
        shimmer_color = _lighten(c, 0.6)
        xs = [p[0] for p in self._river_poly]
        ys = [p[1] for p in self._river_poly]
        river_top_y, river_bottom_y = min(ys), max(ys)
        cx = sum(xs) / len(xs)
        for i in range(2):
            t = (self._shimmer_t * 0.1 + i / 2) % 1.0
            y = river_top_y + (river_bottom_y - river_top_y) * t
            alpha_fade = math.sin(t * math.pi)
            if alpha_fade <= 0.05:
                continue
            glint = pygame.Surface((5, 1), pygame.SRCALPHA)
            glint.fill((*shimmer_color, round(150 * alpha_fade)))
            target.blit(glint, (cx - 2 + (i * 3 - 1), y))
