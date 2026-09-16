"""Internal weather model. Providers normalize into this; nothing downstream
of here (scene, ui) ever sees a provider's raw response shape.

Mirrors weathr's condition taxonomy (clear-skies / precipitation / snow /
storms, each with intensity tiers that drive animation density) but as plain
dataclasses + an enum rather than a Rust-style closed type hierarchy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum


class Condition(Enum):
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly-cloudy"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    FOG = "fog"
    DRIZZLE = "drizzle"
    RAIN = "rain"
    FREEZING_RAIN = "freezing-rain"
    RAIN_SHOWERS = "rain-showers"
    SNOW = "snow"
    SNOW_GRAINS = "snow-grains"
    SNOW_SHOWERS = "snow-showers"
    THUNDERSTORM = "thunderstorm"
    THUNDERSTORM_HAIL = "thunderstorm-hail"

    @property
    def is_raining(self) -> bool:
        return self in {
            Condition.DRIZZLE,
            Condition.RAIN,
            Condition.FREEZING_RAIN,
            Condition.RAIN_SHOWERS,
        }

    @property
    def is_snowing(self) -> bool:
        return self in {Condition.SNOW, Condition.SNOW_GRAINS, Condition.SNOW_SHOWERS}

    @property
    def is_foggy(self) -> bool:
        return self == Condition.FOG

    @property
    def is_thunderstorm(self) -> bool:
        return self in {Condition.THUNDERSTORM, Condition.THUNDERSTORM_HAIL}

    @property
    def is_cloudy(self) -> bool:
        return self in {
            Condition.PARTLY_CLOUDY,
            Condition.CLOUDY,
            Condition.OVERCAST,
            Condition.THUNDERSTORM,
            Condition.THUNDERSTORM_HAIL,
        }

    @property
    def cloud_coverage(self) -> float:
        """0..1, how much of the sky clouds occupy. Drives cloud layer density."""
        return {
            Condition.CLEAR: 0.0,
            Condition.PARTLY_CLOUDY: 0.35,
            Condition.CLOUDY: 0.65,
            Condition.OVERCAST: 0.9,
            Condition.FOG: 0.5,
            Condition.DRIZZLE: 0.75,
            Condition.RAIN: 0.85,
            Condition.FREEZING_RAIN: 0.85,
            Condition.RAIN_SHOWERS: 0.6,
            Condition.SNOW: 0.85,
            Condition.SNOW_GRAINS: 0.7,
            Condition.SNOW_SHOWERS: 0.6,
            Condition.THUNDERSTORM: 0.95,
            Condition.THUNDERSTORM_HAIL: 0.95,
        }[self]

    @property
    def rain_intensity(self) -> float:
        """0..1 particle density for the rain layer."""
        return {
            Condition.DRIZZLE: 0.25,
            Condition.RAIN: 0.6,
            Condition.RAIN_SHOWERS: 0.6,
            Condition.FREEZING_RAIN: 0.8,
            Condition.THUNDERSTORM: 0.85,
            Condition.THUNDERSTORM_HAIL: 1.0,
        }.get(self, 0.0)

    @property
    def snow_intensity(self) -> float:
        return {
            Condition.SNOW_GRAINS: 0.3,
            Condition.SNOW_SHOWERS: 0.55,
            Condition.SNOW: 0.85,
        }.get(self, 0.0)

    @property
    def fog_intensity(self) -> float:
        return 0.6 if self == Condition.FOG else 0.0

    @property
    def label(self) -> str:
        return {
            Condition.CLEAR: "Clear",
            Condition.PARTLY_CLOUDY: "Partly Cloudy",
            Condition.CLOUDY: "Cloudy",
            Condition.OVERCAST: "Overcast",
            Condition.FOG: "Fog",
            Condition.DRIZZLE: "Drizzle",
            Condition.RAIN: "Rain",
            Condition.FREEZING_RAIN: "Freezing Rain",
            Condition.RAIN_SHOWERS: "Rain Showers",
            Condition.SNOW: "Snow",
            Condition.SNOW_GRAINS: "Snow Grains",
            Condition.SNOW_SHOWERS: "Snow Showers",
            Condition.THUNDERSTORM: "Thunderstorm",
            Condition.THUNDERSTORM_HAIL: "Thunderstorm & Hail",
        }[self]


@dataclass
class Astronomy:
    sunrise: datetime
    sunset: datetime
    moon_phase: float = 0.0  # 0 = new moon, 0.5 = full, 1 = new again

    def is_day(self, at: datetime) -> bool:
        return self.sunrise <= at <= self.sunset


@dataclass
class CurrentConditions:
    temperature: float
    feels_like: float
    condition: Condition
    humidity: float  # 0..100
    wind_speed: float
    wind_direction_deg: float
    precipitation: float
    precipitation_probability: float  # 0..100
    observed_at: datetime


@dataclass
class ForecastDay:
    date: datetime
    condition: Condition
    high: float
    low: float
    precipitation_probability: float = 0.0


@dataclass
class WeatherSnapshot:
    current: CurrentConditions
    forecast: list[ForecastDay]
    astronomy: Astronomy
    location_name: str
    fetched_at: datetime
    stale: bool = False
    utc_offset_seconds: int = 0

    def local_now(self) -> datetime:
        """The configured location's current wall-clock time — deliberately
        independent of the device's own system timezone, since this
        appliance is driven entirely by lat/lon, not wherever it boots up
        with its clock set to (a fresh Pi image often defaults to UTC)."""
        return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=self.utc_offset_seconds)
