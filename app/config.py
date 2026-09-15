"""Loads config.toml (falling back to config.example.toml) into a plain dataclass tree."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class LocationConfig:
    latitude: float = 52.5200
    longitude: float = 13.4050
    name: str = "Berlin"


@dataclass
class UnitsConfig:
    temperature: str = "celsius"
    wind_speed: str = "kmh"
    precipitation: str = "mm"


@dataclass
class DisplayConfig:
    backend: str = "auto"
    fullscreen: bool = True
    width: int = 800
    height: int = 480
    fps: int = 30


@dataclass
class WeatherConfig:
    refresh_interval_seconds: int = 600
    cache_path: str = "~/.cache/weathr-panel/last_weather.json"


@dataclass
class DebugConfig:
    enabled: bool = False


@dataclass
class Config:
    location: LocationConfig = field(default_factory=LocationConfig)
    units: UnitsConfig = field(default_factory=UnitsConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    debug: DebugConfig = field(default_factory=DebugConfig)

    @property
    def cache_path(self) -> Path:
        return Path(self.weather.cache_path).expanduser()


def load_config(path: Path | None = None) -> Config:
    if path is None:
        candidate = PROJECT_ROOT / "config.toml"
        path = candidate if candidate.exists() else PROJECT_ROOT / "config.example.toml"

    with open(path, "rb") as f:
        raw = tomllib.load(f)

    return Config(
        location=LocationConfig(**raw.get("location", {})),
        units=UnitsConfig(**raw.get("units", {})),
        display=DisplayConfig(**raw.get("display", {})),
        weather=WeatherConfig(**raw.get("weather", {})),
        debug=DebugConfig(**raw.get("debug", {})),
    )
