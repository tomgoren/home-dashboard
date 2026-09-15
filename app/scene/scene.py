"""Composes the sky/celestial/cloud/precipitation/effects layers. This is
the only place that knows the draw order; everything else just owns one
layer's worth of state.
"""

from __future__ import annotations

from datetime import datetime

import pygame

from app.scene.celestial import CelestialLayer
from app.scene.clouds import CloudLayer
from app.scene.effects import EffectsLayer
from app.scene.precipitation import PrecipitationLayer
from app.scene.sky import SkyLayer
from app.weather.model import WeatherSnapshot


class Scene:
    def __init__(self, size: tuple[int, int]):
        self.size = size
        self.sky = SkyLayer(size)
        self.celestial = CelestialLayer(size)
        self.clouds = CloudLayer(size)
        self.precipitation = PrecipitationLayer(size)
        self.effects = EffectsLayer(size)

    def configure(self, snapshot: WeatherSnapshot, now: datetime) -> None:
        condition = snapshot.current.condition
        self.sky.configure(now, snapshot.astronomy, condition)
        self.celestial.configure(now, snapshot.astronomy, condition.cloud_coverage)
        self.clouds.configure(
            condition, snapshot.current.wind_speed, snapshot.current.wind_direction_deg
        )
        self.precipitation.configure(
            condition, snapshot.current.wind_speed, snapshot.current.wind_direction_deg
        )
        self.effects.configure(condition)

    def update(self, dt: float) -> None:
        self.celestial.update(dt)
        self.clouds.update(dt)
        self.precipitation.update(dt)
        self.effects.update(dt)

    def draw(self, target: pygame.Surface) -> None:
        self.sky.draw(target)
        self.celestial.draw(target)
        self.clouds.draw(target)
        self.precipitation.draw(target)
        self.effects.draw(target)
