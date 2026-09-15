import os
import sys
from dataclasses import replace
from datetime import datetime, timedelta
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
from app.weather.fake import fake_snapshot
from app.weather.model import Condition

config = load_config()
pygame.init()
pygame.display.init()
pygame.font.init()
screen = pygame.display.set_mode((config.display.width, config.display.height))

scenarios = [
    ("clear_night", Condition.CLEAR, 23, 10),
    ("clear_day", Condition.CLEAR, 13, 0),
    ("snow", Condition.SNOW, 8, 0),
    ("thunderstorm", Condition.THUNDERSTORM_HAIL, 16, 30),
    ("fog_dawn", Condition.FOG, 6, 50),
]

tiles = []
for name, cond, hh, mm in scenarios:
    canvas = pygame.Surface((config.display.width, config.display.height)).convert()
    display = Display(canvas=canvas, physical_screen=screen, logical_size=canvas.get_size(), backend_name="dummy")
    scene = Scene(display.logical_size)

    today = datetime(2026, 9, 15, hh, mm)
    snapshot = fake_snapshot(today)
    snapshot.current = replace(snapshot.current, condition=cond)

    scene.configure(snapshot, today)
    for _ in range(60):
        scene.update(1 / 30)

    scene.draw(canvas)
    ui_scrim.draw(canvas)
    anchor = ui_current.draw_primary(canvas, snapshot, config)
    ui_current.draw_header(canvas, snapshot, today)
    ui_current.draw_secondary(canvas, snapshot, config, anchor)
    ui_forecast.draw(canvas, snapshot, config)

    path = f"preview_{name}.png"
    pygame.image.save(canvas, path)
    tiles.append(path)
    print("saved", path)

pygame.quit()
