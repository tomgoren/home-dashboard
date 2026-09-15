"""Persists the last successful WeatherSnapshot to disk so the appliance has
something real to show immediately on boot, and something to fall back to
if the network is down.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from app.weather.model import (
    Astronomy,
    Condition,
    CurrentConditions,
    ForecastDay,
    WeatherSnapshot,
)


def save(path: Path, snapshot: WeatherSnapshot) -> None:
    data = asdict(snapshot)
    data["current"]["condition"] = snapshot.current.condition.value
    data["current"]["observed_at"] = snapshot.current.observed_at.isoformat()
    for day, raw in zip(snapshot.forecast, data["forecast"]):
        raw["condition"] = day.condition.value
        raw["date"] = day.date.isoformat()
    data["astronomy"]["sunrise"] = snapshot.astronomy.sunrise.isoformat()
    data["astronomy"]["sunset"] = snapshot.astronomy.sunset.isoformat()
    data["fetched_at"] = snapshot.fetched_at.isoformat()

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data))
    tmp.replace(path)


def load(path: Path) -> WeatherSnapshot | None:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None

    try:
        current = CurrentConditions(
            **{**data["current"],
               "condition": Condition(data["current"]["condition"]),
               "observed_at": datetime.fromisoformat(data["current"]["observed_at"])}
        )
        forecast = [
            ForecastDay(
                **{**day,
                   "condition": Condition(day["condition"]),
                   "date": datetime.fromisoformat(day["date"])}
            )
            for day in data["forecast"]
        ]
        astronomy = Astronomy(
            sunrise=datetime.fromisoformat(data["astronomy"]["sunrise"]),
            sunset=datetime.fromisoformat(data["astronomy"]["sunset"]),
            moon_phase=data["astronomy"].get("moon_phase", 0.0),
        )
        return WeatherSnapshot(
            current=current,
            forecast=forecast,
            astronomy=astronomy,
            location_name=data["location_name"],
            fetched_at=datetime.fromisoformat(data["fetched_at"]),
            stale=True,  # anything loaded from disk is stale until a live fetch succeeds
        )
    except (KeyError, ValueError):
        return None
