"""Tiny procedural condition glyphs (forecast strip, secondary labels).
Geometric primitives only — no bitmap icon set, so they always match the
current palette and never need asset licensing.
"""

from __future__ import annotations

import pygame

from app import palette
from app.weather.model import Condition


def draw(target: pygame.Surface, rect: pygame.Rect, condition: Condition) -> None:
    cx, cy = rect.center
    r = min(rect.width, rect.height) // 2

    def cloud(color, y_offset=0, scale=1.0):
        w, h = rect.width * 0.8 * scale, rect.height * 0.42 * scale
        y = cy + y_offset
        pygame.draw.ellipse(target, color, (cx - w * 0.5, y - h * 0.4, w * 0.55, h))
        pygame.draw.ellipse(target, color, (cx - w * 0.15, y - h * 0.6, w * 0.55, h * 1.1))
        pygame.draw.ellipse(target, color, (cx + w * 0.05, y - h * 0.3, w * 0.5, h * 0.9))

    if condition == Condition.CLEAR:
        pygame.draw.circle(target, palette.SUN, (cx, cy), round(r * 0.6))
    elif condition == Condition.PARTLY_CLOUDY:
        pygame.draw.circle(target, palette.SUN, (cx - r * 0.3, cy - r * 0.2), round(r * 0.45))
        cloud(palette.CLOUD_NEAR, y_offset=r * 0.25, scale=0.9)
    elif condition in (Condition.CLOUDY, Condition.OVERCAST):
        cloud(palette.CLOUD_NEAR)
    elif condition == Condition.FOG:
        for i, y in enumerate(range(-2, 3)):
            pygame.draw.line(
                target, palette.FOG,
                (cx - r * 0.9, cy + y * r * 0.3),
                (cx + r * 0.9, cy + y * r * 0.3), 2,
            )
    elif condition.is_snowing:
        cloud(palette.CLOUD_FAR, y_offset=-r * 0.3, scale=0.85)
        for dx in (-0.35, 0, 0.35):
            pygame.draw.circle(target, palette.SNOW_FLAKE, (round(cx + dx * r), round(cy + r * 0.5)), 2)
    elif condition.is_thunderstorm:
        cloud(palette.CLOUD_STORM, y_offset=-r * 0.3, scale=0.9)
        points = [
            (cx + r * 0.1, cy + r * 0.2),
            (cx - r * 0.15, cy + r * 0.55),
            (cx + r * 0.05, cy + r * 0.55),
            (cx - r * 0.2, cy + r * 0.95),
        ]
        pygame.draw.lines(target, palette.SUN, False, points, 2)
    elif condition.is_raining:
        cloud(palette.CLOUD_NEAR, y_offset=-r * 0.3, scale=0.9)
        for dx in (-0.35, 0, 0.35):
            x = cx + dx * r
            pygame.draw.line(
                target, palette.RAIN_STREAK,
                (x, cy + r * 0.35), (x - 2, cy + r * 0.7), 2,
            )
