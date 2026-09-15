"""WeatherProvider is the seam between the outside world and the internal
model. The renderer never imports a provider directly — only WeatherSnapshot.
"""

from __future__ import annotations

from typing import Protocol

from app.weather.model import WeatherSnapshot


class WeatherProvider(Protocol):
    def fetch(self) -> WeatherSnapshot: ...
