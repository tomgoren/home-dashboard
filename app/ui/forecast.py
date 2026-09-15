"""Compact multi-day forecast strip along the bottom edge. No boxes/dividers
— columns are separated by spacing and alignment only."""

from __future__ import annotations

import pygame

from app import palette
from app.config import Config
from app.ui import format as fmt
from app.ui import glyph
from app.ui import typography as ty
from app.weather.model import WeatherSnapshot

MARGIN = 0.04
DAYS_SHOWN = 5


def draw(target: pygame.Surface, snapshot: WeatherSnapshot, config: Config) -> None:
    w, h = target.get_size()
    margin = round(w * MARGIN)
    strip_top = round(h * 0.80)
    strip_h = h - strip_top - round(h * 0.02)

    days = snapshot.forecast[:DAYS_SHOWN]
    if not days:
        return

    col_w = (w - margin * 2) / len(days)

    day_font = ty.body_font(round(h * 0.028))
    hi_font = ty.body_font(round(h * 0.034))
    lo_font = ty.body_font(round(h * 0.028))
    glyph_size = round(strip_h * 0.42)

    for i, day in enumerate(days):
        cx = margin + col_w * (i + 0.5)

        day_str = day.date.strftime("%a").upper()
        day_surf = ty.render(day_font, day_str, palette.TEXT_DIM)
        target.blit(day_surf, (round(cx - day_surf.get_width() / 2), strip_top))

        glyph_rect = pygame.Rect(0, 0, glyph_size, glyph_size)
        glyph_rect.center = (round(cx), strip_top + round(strip_h * 0.42))
        glyph.draw(target, glyph_rect, day.condition)

        hi_str = fmt.temperature(day.high, config.units, with_unit=False)
        lo_str = fmt.temperature(day.low, config.units, with_unit=False)
        hi_surf = ty.render(hi_font, hi_str, palette.TEXT_PRIMARY)
        lo_surf = ty.render(lo_font, lo_str, palette.TEXT_DIM)

        line_y = strip_top + round(strip_h * 0.72)
        gap = 6
        total_w = hi_surf.get_width() + gap + lo_surf.get_width()
        start_x = round(cx - total_w / 2)
        target.blit(hi_surf, (start_x, line_y))
        target.blit(lo_surf, (start_x + hi_surf.get_width() + gap, line_y + (hi_surf.get_height() - lo_surf.get_height())))
