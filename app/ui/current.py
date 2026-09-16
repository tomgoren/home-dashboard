"""Header (date/time/location) and primary/secondary current-conditions
text. Positions are proportional to canvas size so the layout holds up if
the logical design resolution changes.
"""

from __future__ import annotations

from datetime import datetime

import pygame

from app import palette
from app.config import Config
from app.ui import format as fmt
from app.ui import typography as ty
from app.weather.model import WeatherSnapshot

MARGIN = 0.04  # fraction of width


def draw_header(target: pygame.Surface, snapshot: WeatherSnapshot, now: datetime) -> None:
    w, h = target.get_size()
    margin = round(w * MARGIN)

    date_font = ty.terminal_font(round(h * 0.052))
    time_font = ty.terminal_font(round(h * 0.09))
    loc_font = ty.body_font(round(h * 0.026))

    date_str = now.strftime("%a, %b %-d").upper()
    date_surf = ty.render(date_font, date_str, palette.TEXT_SECONDARY)
    target.blit(date_surf, (margin, round(h * 0.02)))

    time_str = now.strftime("%H:%M")
    time_surf = ty.render(time_font, time_str, palette.TEXT_PRIMARY)
    target.blit(time_surf, (w - margin - time_surf.get_width(), round(h * 0.005)))

    if snapshot.location_name:
        loc_surf = ty.render(loc_font, snapshot.location_name.upper(), palette.TEXT_DIM)
        target.blit(loc_surf, (w - margin - loc_surf.get_width(), round(h * 0.085)))


def draw_primary(target: pygame.Surface, snapshot: WeatherSnapshot, config: Config) -> pygame.Rect:
    """Draw the primary temperature and return its bounds."""
    w, h = target.get_size()
    margin = round(w * MARGIN)
    current = snapshot.current

    temp_font = ty.display_font(round(h * 0.34))
    temp_str = fmt.temperature(current.temperature, config.units, with_unit=False)
    temp_surf = ty.render(temp_font, temp_str, palette.TEXT_PRIMARY)
    temp_y = round(h * 0.24)
    target.blit(temp_surf, (margin, temp_y))

    # Just the letter, not another "°" — temp_str above already has one
    # baked in (with_unit=False still yields a bare degree glyph), so a
    # second "°F"/"°C" here would double up right next to it.
    unit_font = ty.body_font(round(h * 0.065))
    unit_str = "F" if config.units.temperature == "fahrenheit" else "C"
    unit_surf = ty.render(unit_font, unit_str, palette.TEXT_SECONDARY)
    # Space Mono's monospace advance bakes in trailing side-bearing after
    # the last digit, so pull the unit in rather than butting it flush.
    unit_x = margin + temp_surf.get_width() - round(h * 0.05)
    target.blit(unit_surf, (unit_x, temp_y + round(h * 0.03)))

    return pygame.Rect(
        margin,
        temp_y,
        temp_surf.get_width() + unit_surf.get_width(),
        temp_surf.get_height(),
    )


def draw_secondary(target: pygame.Surface, snapshot: WeatherSnapshot, config: Config, anchor: pygame.Rect) -> None:
    w, h = target.get_size()
    margin = round(w * MARGIN)
    current = snapshot.current

    label_font = ty.body_font(round(h * 0.024))
    value_font = ty.body_font(round(h * 0.036))

    rows = [
        ("CONDITIONS", current.condition.label),
        ("FEELS LIKE", fmt.temperature(current.feels_like, config.units)),
        ("WIND", f"{fmt.wind_compass(current.wind_direction_deg)} {fmt.wind(current.wind_speed, config.units)}"),
        ("HUMIDITY", f"{round(current.humidity)}%"),
    ]
    if current.precipitation_probability > 0:
        rows.append((
            "PRECIP",
            f"{round(current.precipitation_probability)}% · {fmt.precipitation(current.precipitation, config.units)}",
        ))

    row_h = round(h * 0.1)
    x = w - margin
    y = anchor.top
    for label, value in rows:
        label_surf = ty.render(label_font, label, palette.TEXT_DIM)
        value_surf = ty.render(value_font, value, palette.TEXT_PRIMARY)
        target.blit(label_surf, (x - label_surf.get_width(), y))
        target.blit(value_surf, (x - value_surf.get_width(), y + label_surf.get_height() + 2))
        y += row_h
