# weathr-panel

A small graphical weather appliance for a 7" Linux display — what
[weathr](https://github.com/Veirt/weathr)'s terminal ASCII scene might have
become if it had been designed for a pixel-addressable display instead of a
terminal grid.

![rainy scene mockup](docs/preview-rain.png)

Python 3 + Pygame(-ce), rendering straight to DRM/KMS or a Linux framebuffer
— no X11, Wayland, Chromium, Electron, Qt, or GTK.

## Design principles carried over from weathr

Studied weathr's README and Rust source (`src/theme`, `src/scene/world`,
`src/weather`, `src/animation_manager.rs`, `src/app_state.rs`) before writing
any rendering code. What's worth preserving:

- **The scene *is* the UI.** weathr has no dashboard — a single HUD line
  sits over an ASCII illustration. We keep that ratio: one giant number, a
  short condition label, a handful of secondary stats, and otherwise let the
  animated scene carry the screen.
- **Conditions configure a shared set of layers, not separate renderers.**
  weathr's `AnimationManager` holds one rain/snow/fog/wind state that every
  condition maps into, with intensity tiers (drizzle → rain → heavy →
  storm) driving particle density. `Condition` in `app/weather/model.py`
  exposes the same shape (`cloud_coverage`, `rain_intensity`,
  `snow_intensity`, `fog_intensity`) and the scene layers just read it.
- **Day/night is real state, not a decoration.** weathr does a hard palette
  swap keyed on `sun.is_day`. We go one step further (gradual interpolation
  through dawn/dusk) because a graphical display can afford it, but the
  principle — sky state derived from real sun position, not a toggle — is
  the same one weathr already had.
- **Restraint.** weathr's HUD is a single plain line, fixed field order,
  attribution deliberately de-emphasized (dark grey, corner, out of the
  way). No boxes, no icons beyond text. We keep the "no boxes, no dashboard
  chrome" rule; hierarchy comes from type size, color, and spacing instead.
- **Assets separated from logic.** weathr's ASCII art lives in `.txt` files
  read via `include_str!`, kept out of the render/color code. We don't ship
  bitmap icons at all — the forecast glyphs (`app/ui/glyph.py`) are drawn
  procedurally from the same palette, so they can never fall out of sync
  with the current theme.
- **Graceful degradation, not error dialogs.** weathr keeps running on
  simulated/cached data when a request fails rather than showing an error
  screen. `WeatherSnapshot.stale` + a small unobtrusive "offline" label
  (bottom-left, dim) follow the same idea — see `App.draw_stale_indicator`.

Where we deliberately diverge: weathr draws a literal little ASCII house/
yard scene. We don't — the brief asks for the weather itself to be the
interface, so the scene is sky + clouds + precipitation + sun/moon/stars,
composed full-bleed, rather than a fixed illustration with weather painted
around it.

## Architecture

```
app/
  main.py            # the loop: events -> weather -> scene.update -> draw
  config.py           # TOML config -> dataclasses
  palette.py           # shared color vocabulary (sky phases, text, weather)

  weather/
    model.py           # Condition enum + intensity tiers, CurrentConditions,
                        # ForecastDay, Astronomy, WeatherSnapshot
    provider.py         # WeatherProvider protocol
    fake.py             # fake data for the Phase 1/2 mockup

  display/
    backend.py          # SDL init: window / kmsdrm / fbdev / auto-detect.
                         # Owns everything display-driver-specific; scene
                         # and ui code never touch SDL_VIDEODRIVER etc.

  scene/
    scene.py            # composes the layers below, owns draw order
    sky.py               # gradient, interpolated across night/dawn/day/dusk
    celestial.py          # sun/moon arc position, twinkling stars
    clouds.py             # parallax cloud clusters, wind-driven drift
    precipitation.py      # rain / snow / fog, intensity-driven
    effects.py            # lightning flash (more flourishes go here later)

  ui/
    typography.py        # font loading + cached text rendering
    format.py             # unit-aware temp/wind/precip formatting
    glyph.py               # procedural condition icons (forecast strip)
    current.py             # header, big temp, secondary stats
    forecast.py            # 5-day strip
    scrim.py                # soft top/bottom darkening for text legibility

assets/fonts/            # Space Mono (OFL) + VT323 (OFL)
scripts/                  # headless preview renderers (dev-only, no live window needed)
```

No DI container, no event bus, no plugin system — plain objects, a
`Scene.configure()`/`update()`/`draw()` triad, and one `WeatherSnapshot`
passed down from `main.py`. `WeatherProvider` is the only seam: swapping the
fake data for Open-Meteo later touches `main.py`'s `refresh_weather()` and
nothing in `scene/` or `ui/`.

## Status

**Phase 1–2 (this commit):** static/animated mockup on fake data, scaled
logical-resolution rendering, day/night sky interpolation, cloud parallax,
rain/snow/fog, sun/moon/stars, 5-day forecast, unit-aware formatting. Not
yet done: Open-Meteo integration (Phase 3), wind-shaped rain angle is
wired but untested against real wind data, thunderstorm flash timing needs
tuning, systemd deploy is a template only.

## Running it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config.example.toml config.toml   # edit location/units as needed
python -m app.main
```

Controls: `q`/`Esc` quit, `r` force refresh, `d` toggle debug overlay.

On the Pi (no desktop session), `backend = "auto"` in `config.toml` tries
DRM/KMS first, then legacy `fbdev`. Force one explicitly with `backend =
"kmsdrm"` or `"fbdev"` if auto-detection picks wrong. See
`weathr-panel.service.example` for the systemd unit.

`scripts/preview.py` and `scripts/preview_grid.py` render frames to PNG
without opening a window (`SDL_VIDEODRIVER=dummy`) — useful for checking
composition changes over SSH or in CI.

## Credits

Weather data (once Phase 3 lands): [Open-Meteo](https://open-meteo.com/),
CC BY 4.0. Fonts: [Space Mono](https://github.com/googlefonts/spacemono)
and [VT323](https://github.com/peterhull90/VT323), both SIL Open Font
License. Design lineage: [Veirt/weathr](https://github.com/Veirt/weathr).
