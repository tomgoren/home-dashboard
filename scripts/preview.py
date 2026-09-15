"""Dev-only: run a few simulated seconds of the loop and dump a PNG, so the
composition can be checked without staring at a live window."""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # override if you have a real display

import pygame

from app.config import load_config
from app.display.backend import Display
from app.scene.scene import Scene
from app.ui import current as ui_current
from app.ui import forecast as ui_forecast
from app.ui import scrim as ui_scrim
from app.weather.fake import fake_snapshot

config = load_config()
pygame.init()
pygame.display.init()
pygame.font.init()
screen = pygame.display.set_mode((config.display.width, config.display.height))
canvas = pygame.Surface((config.display.width, config.display.height)).convert()
display = Display(
    canvas=canvas,
    physical_screen=screen,
    logical_size=(config.display.width, config.display.height),
    backend_name="dummy",
)
scene = Scene(display.logical_size)

now = datetime(2026, 9, 15, 19, 5)  # evening, matches astronomy in fake data
snapshot = fake_snapshot(now)

scene.configure(snapshot, now)
for _ in range(90):  # ~3s at 30fps
    scene.update(1 / 30)

canvas = display.canvas
scene.draw(canvas)
ui_scrim.draw(canvas)
anchor = ui_current.draw_primary(canvas, snapshot, config)
ui_current.draw_header(canvas, snapshot, now)
ui_current.draw_secondary(canvas, snapshot, config, anchor)
ui_forecast.draw(canvas, snapshot, config)

pygame.image.save(canvas, "preview.png")
print("saved preview.png")
pygame.quit()
