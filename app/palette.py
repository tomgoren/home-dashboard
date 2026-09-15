"""A restrained, shared color vocabulary. One place to tune the whole
appliance's mood rather than scattering RGB literals through scene/ui code.

Sky colors are defined as gradient (top, horizon) pairs per phase; scene/sky.py
interpolates between adjacent phases as the day progresses.
"""

from __future__ import annotations

Color = tuple[int, int, int]

# -- sky phases: (zenith, horizon) --------------------------------------
SKY_NIGHT: tuple[Color, Color] = ((8, 11, 26), (18, 22, 45))
SKY_DAWN: tuple[Color, Color] = ((30, 32, 66), (196, 118, 92))
SKY_DAY: tuple[Color, Color] = ((74, 98, 128), (140, 158, 176))
SKY_DAY_OVERCAST: tuple[Color, Color] = ((58, 66, 82), (94, 102, 116))
SKY_DUSK: tuple[Color, Color] = ((36, 30, 62), (210, 122, 74))

# -- atmosphere / weather elements ---------------------------------------
CLOUD_FAR: Color = (58, 66, 86)
CLOUD_NEAR: Color = (84, 95, 120)
CLOUD_STORM: Color = (40, 42, 54)
RAIN_STREAK: Color = (174, 198, 216)
SNOW_FLAKE: Color = (235, 240, 245)
FOG: Color = (150, 160, 170)
LIGHTNING_FLASH: Color = (232, 236, 255)
SUN: Color = (247, 205, 111)
SUN_GLOW: Color = (247, 205, 111)
MOON: Color = (222, 226, 235)
STAR: Color = (230, 233, 245)
GROUND_NIGHT: Color = (10, 12, 22)
GROUND_DAY: Color = (24, 28, 36)

# -- typography ------------------------------------------------------------
TEXT_PRIMARY: Color = (242, 239, 233)
TEXT_SECONDARY: Color = (198, 204, 214)
TEXT_ACCENT: Color = (232, 168, 87)
TEXT_DIM: Color = (168, 174, 186)

BACKDROP: Color = (14, 16, 28)


def lerp_color(a: Color, b: Color, t: float) -> Color:
    t = max(0.0, min(1.0, t))
    return (
        round(a[0] + (b[0] - a[0]) * t),
        round(a[1] + (b[1] - a[1]) * t),
        round(a[2] + (b[2] - a[2]) * t),
    )
