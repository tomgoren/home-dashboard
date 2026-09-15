import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from app import palette
from app.scene.celestial import _build_moon_disc

pygame.init()
pygame.display.set_mode((1, 1))

phases = [0.0, 0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9]
radius = 30
canvas = pygame.Surface((radius * 2 * len(phases), radius * 2 + 20)).convert()
canvas.fill((10, 12, 22))

for i, phase in enumerate(phases):
    disc = _build_moon_disc(radius, round(phase * 100) % 100)
    canvas.blit(disc, (i * radius * 2, 10))

pygame.image.save(canvas, "preview_moon.png")
print("saved", phases)
pygame.quit()
