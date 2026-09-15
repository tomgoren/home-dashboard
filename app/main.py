"""Entry point. Keeps the loop obvious:

    while running:
        process_events()
        update_weather_if_needed()
        scene.configure(weather)   # cheap; only rebuilds on change
        scene.update(dt)
        draw()
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame

from app import palette
from app.config import Config, load_config
from app.display.backend import init_display
from app.scene.scene import Scene
from app.ui import current as ui_current
from app.ui import forecast as ui_forecast
from app.ui import scrim as ui_scrim
from app.ui import typography as ty
from app.weather import cache as weather_cache
from app.weather.fake import fake_snapshot
from app.weather.model import WeatherSnapshot
from app.weather.open_meteo import OpenMeteoProvider
from app.weather.refresher import BackgroundRefresher


class App:
    def __init__(self, config: Config):
        self.config = config
        pygame.init()
        self.display = init_display(config.display)
        self.scene = Scene(self.display.logical_size)
        self.clock = pygame.time.Clock()
        self.debug = config.debug.enabled
        self.running = True
        self._last_condition = None

        bootstrap = weather_cache.load(config.cache_path)
        if bootstrap is None:
            bootstrap = fake_snapshot()
            bootstrap.stale = True

        self.refresher = BackgroundRefresher(
            provider=OpenMeteoProvider(config.location),
            cache_path=config.cache_path,
            interval_seconds=config.weather.refresh_interval_seconds,
            initial_snapshot=bootstrap,
        )
        self.refresher.start()

    @property
    def snapshot(self) -> WeatherSnapshot:
        return self.refresher.snapshot

    def process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    self.running = False
                elif event.key == pygame.K_r:
                    self.refresher.force_refresh()
                elif event.key == pygame.K_d:
                    self.debug = not self.debug

    def draw_debug(self) -> None:
        font = ty.body_font(14)
        text = f"{self.clock.get_fps():4.1f} fps  backend={self.display.backend_name}"
        surf = ty.render(font, text, palette.TEXT_DIM)
        self.display.canvas.blit(surf, (8, self.display.logical_size[1] - surf.get_height() - 6))

    def draw_stale_indicator(self, snapshot: WeatherSnapshot, now: datetime) -> None:
        if not snapshot.stale:
            return
        age_min = round((now - snapshot.fetched_at).total_seconds() / 60)
        font = ty.body_font(14)
        surf = ty.render(font, f"OFFLINE · DATA {age_min}m OLD", palette.TEXT_DIM)
        target = self.display.canvas
        target.blit(surf, (8, target.get_height() - surf.get_height() - 6))

    def run(self) -> None:
        fps = max(5, self.config.display.fps)
        while self.running:
            dt = self.clock.tick(fps) / 1000.0
            now = datetime.now()
            snapshot = self.snapshot  # one consistent read for the whole frame

            self.process_events()

            if snapshot.current.condition != self._last_condition:
                self.scene.configure(snapshot, now)
                self._last_condition = snapshot.current.condition
            else:
                # keep sky/celestial time-driven state fresh even when the
                # condition hasn't changed
                self.scene.sky.configure(now, snapshot.astronomy, snapshot.current.condition)
                self.scene.celestial.configure(now, snapshot.astronomy, snapshot.current.condition.cloud_coverage)

            self.scene.update(dt)

            canvas = self.display.canvas
            self.scene.draw(canvas)
            ui_scrim.draw(canvas)
            ui_current.draw_header(canvas, snapshot, now)
            anchor = ui_current.draw_primary(canvas, snapshot, self.config)
            ui_current.draw_secondary(canvas, snapshot, self.config, anchor)
            ui_forecast.draw(canvas, snapshot, self.config)
            self.draw_stale_indicator(snapshot, now)
            if self.debug:
                self.draw_debug()

            self.display.present()

        self.refresher.stop()
        pygame.quit()


def main() -> None:
    config = load_config()
    App(config).run()


if __name__ == "__main__":
    main()
