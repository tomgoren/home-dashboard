"""Font loading and cached text rendering.

Two typefaces carry the whole app:
  - Space Mono (Bold for the giant temperature + key numbers, Regular for
    body/forecast text) — a clean monospace with a "digital readout" feel
    that stays legible at both huge and small sizes.
  - VT323 — a terminal/pixel-adjacent face, used sparingly for the
    date/time header as a nod to weathr's ASCII-terminal heritage. Never
    used where legibility of a critical number matters.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pygame

FONTS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "fonts"

_SPACE_MONO_BOLD = FONTS_DIR / "SpaceMono-Bold.ttf"
_SPACE_MONO_REGULAR = FONTS_DIR / "SpaceMono-Regular.ttf"
_VT323 = FONTS_DIR / "VT323-Regular.ttf"


@lru_cache(maxsize=None)
def _load(path: str, size: int) -> pygame.font.Font:
    return pygame.font.Font(path, size)


def display_font(size: int) -> pygame.font.Font:
    """Bold monospace — current temperature, primary numbers."""
    return _load(str(_SPACE_MONO_BOLD), size)


def body_font(size: int) -> pygame.font.Font:
    """Regular monospace — secondary metrics, forecast, condition labels."""
    return _load(str(_SPACE_MONO_REGULAR), size)


def terminal_font(size: int) -> pygame.font.Font:
    """VT323 — date/time header only."""
    return _load(str(_VT323), size)


_text_cache: dict[tuple[int, str, tuple[int, int, int]], pygame.Surface] = {}


def render(font: pygame.font.Font, text: str, color: tuple[int, int, int]) -> pygame.Surface:
    """Cached antialiased text render, keyed by font identity + text + color."""
    key = (id(font), text, color)
    cached = _text_cache.get(key)
    if cached is not None:
        return cached
    surface = font.render(text, True, color)
    _text_cache[key] = surface
    return surface
