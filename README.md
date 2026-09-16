# home-dashboard

A graphical appliance for a small Linux display, currently showing
weather. Renders directly to DRM/KMS (or a legacy framebuffer) — no X11,
Wayland, Chromium, Electron, Qt, or GTK.

![rainy scene mockup](docs/preview-rain.png)

## What it does

- Full-screen animated scene: a sky that shifts continuously through
  night/dawn/day/dusk from real sunrise/sunset times, parallax clouds,
  wind-driven rain/snow/fog, a phase-shaded moon, twinkling stars, bird
  flocks during calm daylight, and a stylized mountain/river/treeline
  horizon.
- Large current temperature and condition, secondary stats (feels like,
  wind, humidity, precipitation), and a 5-day forecast strip.
- Real weather from [Open-Meteo](https://open-meteo.com/) (no API key),
  fetched on a background thread so the render loop never blocks on the
  network. Falls back to the last cached reading (flagged as stale) if
  the network is down.
- Local time is derived from the configured location's own UTC offset,
  not the device's system clock/timezone.
- Runs as a systemd service with no desktop session.

## Design

- The scene is the interface — no dashboard chrome, boxes, or gauges.
  Hierarchy comes from type size, color, and negative space.
- Conditions configure a shared set of layers (sky, clouds,
  precipitation, horizon, effects) instead of each condition having its
  own renderer. Intensity tiers (light/medium/heavy) drive animation
  density.
- Modeled after [weathr](https://github.com/Veirt/weathr), a terminal
  ASCII weather app — same restraint and condition-driven animation,
  translated to a pixel-addressable display instead of a terminal grid.

## Architecture

```
app/
  main.py                # event loop: read weather -> configure scene -> update -> draw
  config.py               # TOML config -> dataclasses
  palette.py               # shared color vocabulary

  weather/
    model.py               # Condition enum + intensity tiers, CurrentConditions,
                            # ForecastDay, Astronomy, WeatherSnapshot
    provider.py             # WeatherProvider protocol
    open_meteo.py            # real provider: WMO code normalization, no API key
    cache.py                  # persist/load last good snapshot to disk
    refresher.py               # background-thread polling
    fake.py                 # fake data, used only until the first live fetch lands

  display/
    backend.py              # SDL init: window / kmsdrm / fbdev / auto-detect;
                             # the only module that touches SDL_VIDEODRIVER etc.

  scene/
    scene.py                # composes the layers below, owns draw order
    sky.py                   # gradient, interpolated across night/dawn/day/dusk
    celestial.py              # sun/moon arc position, twinkling stars
    clouds.py                 # parallax cloud clusters, wind-driven drift
    horizon.py                 # mountain/treeline/river silhouette, tinted from the sky color
    precipitation.py          # rain / snow / fog, intensity-driven
    effects.py                 # lightning flashes, bird flocks

  ui/
    typography.py            # font loading + cached text rendering
    format.py                 # unit-aware temp/wind/precip formatting
    glyph.py                   # procedural condition icons (forecast strip)
    current.py                 # header, big temp, secondary stats
    forecast.py                # 5-day strip
    scrim.py                    # soft top/bottom darkening for text legibility

assets/fonts/                # Space Mono (OFL) + VT323 (OFL)
scripts/                      # setup/deploy automation + headless preview renderers
.mise.toml                    # pins Python, auto-creates/activates .venv, task shortcuts
```

Plain objects throughout — no DI container, event bus, or plugin system.
`WeatherProvider` is the only seam between network data and rendering.

## Setup

Python is managed by [mise](https://mise.jdx.dev): `.mise.toml` pins the
interpreter and auto-creates/activates a `.venv`, so there's no manual
`venv`/`activate` step.

There are two ways to get it running, depending on where you're starting
from.

### On the device itself

Run this while logged into the target machine (or on your own machine,
to develop against a window instead of a real display).

```bash
git clone https://github.com/tomgoren/home-dashboard.git
cd home-dashboard
mise run device:setup
```

`device:setup` installs the SDL2/DRM system packages, adds your user to
the `video`/`render`/`input` groups, installs `mise` if needed, and
installs the Python dependencies. Then:

```bash
$EDITOR config.toml     # set your location
```

Reboot once for the group membership to take effect, then run it (from
the device's local console — SDL needs the real display, not a headless
SSH session with no monitor attached):

```bash
mise run run
```

`backend = "auto"` in `config.toml` tries DRM/KMS first, then legacy
`fbdev`. `mise run check-display` shows what's actually available if you
need to force one explicitly (`backend = "kmsdrm"` or `"fbdev"`).

Once it looks right, install it as a service so it survives reboots:

```bash
mise run device:install-service
```

### Provisioning a headless device remotely, over SSH

For a device you don't want to log into and clone onto by hand — from
your own machine:

```bash
cp .remote.env.example .remote.env
$EDITOR .remote.env      # set REMOTE_HOST=user@host
mise run remote:provision
```

This clones the repo on the remote device and runs `device:setup` there
for you. If you already have a local `config.toml`, it's copied over
automatically; otherwise you'll be prompted to set the location on the
device directly.

```bash
mise run remote:run              # run it on the device's display, for testing
mise run remote:install-service    # install it as a service once it looks right
mise run remote:deploy               # later: pull + reinstall deps + restart
mise run remote:logs                   # tail the service log
```

Every `remote:*` task runs from your machine over SSH; `device:*` and the
plain tasks (`setup`, `run`, `config`, ...) run on whatever machine you
invoke them from.

## Testing without a monitor

Two different situations, two different tools:

**No display hardware attached yet.** `mise run preview`,
`preview-grid`, and `preview-live` render to PNG using SDL's `dummy`
driver — no display device required. This bypasses `display/backend.py`
entirely, so it verifies composition and data flow, not whether the
physical panel lights up.

```bash
mise run remote:run   # or, over a plain SSH session on the device:
mise run preview-live
scp user@host:~/home-dashboard/preview_live.png .
```

**A screen is attached and the app is running on it, but you can't look
at it right now.** `app/main.py` installs a `SIGUSR1` handler that dumps
exactly what's currently on the physical display to a timestamped PNG:

```bash
kill -USR1 $(pgrep -f "app.main")
scp user@host:~/home-dashboard/debug_screenshot_*.png .
```

This only works against the process directly or under systemd —
`mise run run` wraps the process and doesn't forward the signal. Use
`.venv/bin/python -m app.main &` if you want to test this without
installing the service first.

Either way, check the `[display] backend=...` line in the startup log
(`journalctl -u home-dashboard`, or plain stdout) to confirm which
backend actually got picked — `auto` can silently fall back further than
expected if `kmsdrm` init fails.

## Credits

Weather: [Open-Meteo](https://open-meteo.com/), CC BY 4.0. Fonts:
[Space Mono](https://github.com/googlefonts/spacemono) and
[VT323](https://github.com/peterhull90/VT323), both SIL Open Font
License. Design lineage: [Veirt/weathr](https://github.com/Veirt/weathr).
