"""Fake data for the Phase 1 mockup: a dark, rainy, overcast evening.
Exercises most of the visual language (clouds, rain, low light) before any
network code exists.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.weather.model import (
    Astronomy,
    Condition,
    CurrentConditions,
    ForecastDay,
    WeatherSnapshot,
)


def fake_snapshot(now: datetime | None = None) -> WeatherSnapshot:
    now = now or datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    current = CurrentConditions(
        temperature=12.4,
        feels_like=10.8,
        condition=Condition.RAIN,
        humidity=88,
        wind_speed=23,
        wind_direction_deg=245,
        precipitation=3.2,
        precipitation_probability=92,
        observed_at=now,
    )

    forecast_conditions = [
        Condition.RAIN,
        Condition.RAIN_SHOWERS,
        Condition.CLOUDY,
        Condition.PARTLY_CLOUDY,
        Condition.CLEAR,
    ]
    forecast = [
        ForecastDay(
            date=today + timedelta(days=i + 1),
            condition=cond,
            high=15 - i * 0.6,
            low=9 - i * 0.3,
            precipitation_probability=max(10, 90 - i * 18),
        )
        for i, cond in enumerate(forecast_conditions)
    ]

    astronomy = Astronomy(
        sunrise=today + timedelta(hours=6, minutes=42),
        sunset=today + timedelta(hours=19, minutes=18),
        moon_phase=0.62,
    )

    return WeatherSnapshot(
        current=current,
        forecast=forecast,
        astronomy=astronomy,
        location_name="Berlin",
        fetched_at=now,
        stale=False,
    )
