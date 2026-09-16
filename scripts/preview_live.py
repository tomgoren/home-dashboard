"""Dev-only: render one frame using real Open-Meteo data, headlessly."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from app.config import load_config
from app.display.backend import Display
from app.scene.scene import Scene
from app.ui import current as ui_current
from app.ui import forecast as ui_forecast
from app.ui import scrim as ui_scrim
from app.weather.open_meteo import OpenMeteoProvider

config = load_config()
pygame.init()
pygame.display.init()
pygame.font.init()
screen = pygame.display.set_mode((config.display.width, config.display.height))
canvas = pygame.Surface((config.display.width, config.display.height)).convert()
display = Display(canvas=canvas, physical_screen=screen, logical_size=canvas.get_size(), backend_name="dummy")
scene = Scene(display.logical_size)

snapshot = OpenMeteoProvider(config.location).fetch()
now = snapshot.local_now()  # the location's time, not this machine's

scene.configure(snapshot, now)
for _ in range(90):
    scene.update(1 / 30)

scene.draw(canvas)
ui_scrim.draw(canvas)
anchor = ui_current.draw_primary(canvas, snapshot, config)
ui_current.draw_header(canvas, snapshot, now)
ui_current.draw_secondary(canvas, snapshot, config, anchor)
ui_forecast.draw(canvas, snapshot, config)

pygame.image.save(canvas, "preview_live.png")
print("saved preview_live.png —", snapshot.current.condition, snapshot.current.temperature)
pygame.quit()
