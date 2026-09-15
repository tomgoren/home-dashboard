"""A soft, continuous darkening gradient at the top and bottom edges so
header/forecast text stays legible against whatever the sky is doing,
without resorting to boxes or panels."""

from __future__ import annotations

from functools import lru_cache

import pygame


@lru_cache(maxsize=4)
def _build(size: tuple[int, int]) -> pygame.Surface:
    w, h = size
    surf = pygame.Surface(size, pygame.SRCALPHA)

    top_h = round(h * 0.16)
    for y in range(top_h):
        t = 1 - (y / top_h)
        alpha = round(95 * t * t)
        pygame.draw.line(surf, (0, 0, 0, alpha), (0, y), (w, y))

    bottom_h = round(h * 0.24)
    start_y = h - bottom_h
    for y in range(bottom_h):
        t = y / bottom_h
        alpha = round(120 * t * t)
        pygame.draw.line(surf, (0, 0, 0, alpha), (0, start_y + y), (w, start_y + y))

    return surf


def draw(target: pygame.Surface) -> None:
    target.blit(_build(target.get_size()), (0, 0))
