"""Unit-aware formatting. The weather model always stores metric SI-ish
values; this is the only place unit conversion happens."""

from __future__ import annotations

from app.config import UnitsConfig

_WIND_LABEL = {"kmh": "km/h", "ms": "m/s", "mph": "mph", "kn": "kn"}
_WIND_FACTOR = {"kmh": 1.0, "ms": 1 / 3.6, "mph": 0.621371, "kn": 0.539957}


def temperature(celsius: float, units: UnitsConfig, *, with_unit: bool = True) -> str:
    if units.temperature == "fahrenheit":
        value = celsius * 9 / 5 + 32
        suffix = "°F" if with_unit else "°"
    else:
        value = celsius
        suffix = "°C" if with_unit else "°"
    return f"{round(value)}{suffix}"


def wind(speed_kmh: float, units: UnitsConfig) -> str:
    factor = _WIND_FACTOR.get(units.wind_speed, 1.0)
    label = _WIND_LABEL.get(units.wind_speed, "km/h")
    return f"{round(speed_kmh * factor)} {label}"


def precipitation(mm: float, units: UnitsConfig) -> str:
    if units.precipitation == "inch":
        return f"{mm / 25.4:.2f} in"
    return f"{mm:.1f} mm"


def wind_compass(degrees: float) -> str:
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = round(degrees / 22.5) % 16
    return dirs[idx]
