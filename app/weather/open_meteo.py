"""Open-Meteo provider. No API key required. This is the only module that
knows Open-Meteo's JSON shape — everything else sees a WeatherSnapshot.
"""

from __future__ import annotations

import math
from datetime import datetime

import requests

from app.config import LocationConfig
from app.weather.model import (
    Astronomy,
    Condition,
    CurrentConditions,
    ForecastDay,
    WeatherSnapshot,
)

API_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_S = 10

_CURRENT_FIELDS = "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m,precipitation,cloud_cover"
_DAILY_FIELDS = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset"
_HOURLY_FIELDS = "precipitation_probability"

# A known new moon (2000-01-06 18:14 UTC) plus the synodic month length is
# enough for an approximate phase — no ephemeris needed.
_REFERENCE_NEW_MOON = datetime(2000, 1, 6, 18, 14)
_SYNODIC_MONTH_DAYS = 29.53058867


def _moon_phase(now: datetime) -> float:
    days = (now - _REFERENCE_NEW_MOON).total_seconds() / 86400
    phase = (days % _SYNODIC_MONTH_DAYS) / _SYNODIC_MONTH_DAYS
    return phase


def _normalize_condition(code: int, cloud_cover: float | None = None) -> Condition:
    if code in (0, 1):
        return Condition.CLEAR
    if code == 2:
        return Condition.PARTLY_CLOUDY
    if code == 3:
        if cloud_cover is not None and cloud_cover < 85:
            return Condition.CLOUDY
        return Condition.OVERCAST
    if code in (45, 48):
        return Condition.FOG
    if code in (51, 53, 55):
        return Condition.DRIZZLE
    if code in (56, 57, 66, 67):
        return Condition.FREEZING_RAIN
    if code in (61, 63, 65, 82):
        return Condition.RAIN
    if code in (80, 81):
        return Condition.RAIN_SHOWERS
    if code in (71, 77):
        return Condition.SNOW_GRAINS
    if code == 73:
        return Condition.SNOW_SHOWERS
    if code == 75:
        return Condition.SNOW
    if code == 85:
        return Condition.SNOW_SHOWERS
    if code == 86:
        return Condition.SNOW
    if code == 95:
        return Condition.THUNDERSTORM
    if code in (96, 99):
        return Condition.THUNDERSTORM_HAIL
    return Condition.CLOUDY  # unknown code: safest restrained default


def _nearest_hour_index(times: list[str], now_iso: str) -> int | None:
    try:
        return times.index(now_iso)
    except ValueError:
        return None


class OpenMeteoProvider:
    def __init__(self, location: LocationConfig):
        self.location = location

    def fetch(self) -> WeatherSnapshot:
        params = {
            "latitude": self.location.latitude,
            "longitude": self.location.longitude,
            "current": _CURRENT_FIELDS,
            "daily": _DAILY_FIELDS,
            "hourly": _HOURLY_FIELDS,
            "forecast_days": 7,
            "timezone": "auto",
        }
        resp = requests.get(API_URL, params=params, timeout=TIMEOUT_S)
        resp.raise_for_status()
        data = resp.json()

        now = datetime.now()
        cur = data["current"]
        condition = _normalize_condition(cur["weather_code"], cur.get("cloud_cover"))

        precip_probability = 0.0
        hourly = data.get("hourly", {})
        idx = _nearest_hour_index(hourly.get("time", []), cur["time"])
        if idx is not None:
            probs = hourly.get("precipitation_probability", [])
            if idx < len(probs) and probs[idx] is not None:
                precip_probability = float(probs[idx])

        current = CurrentConditions(
            temperature=cur["temperature_2m"],
            feels_like=cur["apparent_temperature"],
            condition=condition,
            humidity=cur["relative_humidity_2m"],
            wind_speed=cur["wind_speed_10m"],
            wind_direction_deg=cur["wind_direction_10m"],
            precipitation=cur["precipitation"],
            precipitation_probability=precip_probability,
            observed_at=now,
        )

        daily = data["daily"]
        forecast = []
        for i in range(1, len(daily["time"])):  # skip today; "current" covers it
            forecast.append(
                ForecastDay(
                    date=datetime.fromisoformat(daily["time"][i]),
                    condition=_normalize_condition(daily["weather_code"][i]),
                    high=daily["temperature_2m_max"][i],
                    low=daily["temperature_2m_min"][i],
                    precipitation_probability=daily.get("precipitation_probability_max", [0] * len(daily["time"]))[i] or 0,
                )
            )

        astronomy = Astronomy(
            sunrise=datetime.fromisoformat(daily["sunrise"][0]),
            sunset=datetime.fromisoformat(daily["sunset"][0]),
            moon_phase=_moon_phase(now),
        )

        return WeatherSnapshot(
            current=current,
            forecast=forecast,
            astronomy=astronomy,
            location_name=self.location.name,
            fetched_at=now,
            stale=False,
        )
