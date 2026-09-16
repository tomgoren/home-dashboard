"""Owns all SDL/display initialization so the rest of the app never has to
know whether it's drawing to a desktop window, DRM/KMS, or a Linux
framebuffer.

Rendering code always draws to a fixed-size logical ``canvas`` surface;
``Display.present()`` scales that once onto whatever the physical screen
turns out to be.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import pygame

from app.config import DisplayConfig


@dataclass
class Display:
    canvas: pygame.Surface
    physical_screen: pygame.Surface
    logical_size: tuple[int, int]
    backend_name: str

    def present(self) -> None:
        phys_w, phys_h = self.physical_screen.get_size()
        log_w, log_h = self.logical_size

        scale = min(phys_w / log_w, phys_h / log_h)
        out_w, out_h = round(log_w * scale), round(log_h * scale)

        if (out_w, out_h) == (phys_w, phys_h):
            scaled = pygame.transform.smoothscale(self.canvas, (out_w, out_h))
            self.physical_screen.blit(scaled, (0, 0))
        else:
            self.physical_screen.fill((0, 0, 0))
            scaled = pygame.transform.smoothscale(self.canvas, (out_w, out_h))
            offset = ((phys_w - out_w) // 2, (phys_h - out_h) // 2)
            self.physical_screen.blit(scaled, offset)

        pygame.display.flip()


def _linux_headless() -> bool:
    return sys.platform.startswith("linux") and not (
        os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    )


def _try_init(driver: str | None, fullscreen: bool, width: int, height: int) -> pygame.Surface | None:
    if driver:
        os.environ["SDL_VIDEODRIVER"] = driver
    else:
        os.environ.pop("SDL_VIDEODRIVER", None)

    try:
        pygame.display.quit()
        pygame.display.init()
        flags = pygame.FULLSCREEN | pygame.SCALED if fullscreen else 0
        size = (0, 0) if fullscreen else (width, height)
        screen = pygame.display.set_mode(size, flags)
        return screen
    except pygame.error:
        return None


def init_display(config: DisplayConfig) -> Display:
    """Create the physical display using the configured (or auto-detected) backend."""

    pygame.font.init()
    if not pygame.display.get_init():
        pygame.display.init()

    requested = config.backend
    screen: pygame.Surface | None = None
    backend_name = "window"

    if requested == "window":
        screen = _try_init(None, fullscreen=False, width=config.width, height=config.height)
        backend_name = "window"

    elif requested == "kmsdrm":
        screen = _try_init("kmsdrm", fullscreen=True, width=config.width, height=config.height)
        backend_name = "kmsdrm"

    elif requested == "fbdev":
        os.environ.setdefault("SDL_FBDEV", "/dev/fb0")
        screen = _try_init("fbcon", fullscreen=True, width=config.width, height=config.height)
        backend_name = "fbdev"

    else:  # "auto"
        if _linux_headless():
            screen = _try_init("kmsdrm", fullscreen=True, width=config.width, height=config.height)
            backend_name = "kmsdrm"
            if screen is None:
                os.environ.setdefault("SDL_FBDEV", "/dev/fb0")
                screen = _try_init("fbcon", fullscreen=True, width=config.width, height=config.height)
                backend_name = "fbdev"
        if screen is None:
            screen = _try_init(None, fullscreen=False, width=config.width, height=config.height)
            backend_name = "window"

    if screen is None:
        raise RuntimeError(
            f"Could not initialize any SDL video backend (requested={requested!r})"
        )

    pygame.mouse.set_visible(backend_name == "window")
    pygame.display.set_caption("home-dashboard")

    canvas = pygame.Surface((config.width, config.height)).convert()

    # Only visible feedback available over a headless SSH session — always
    # print it, don't gate behind debug config.
    print(
        f"[display] backend={backend_name} "
        f"physical={screen.get_size()} logical=({config.width}, {config.height})",
        flush=True,
    )

    return Display(
        canvas=canvas,
        physical_screen=screen,
        logical_size=(config.width, config.height),
        backend_name=backend_name,
    )
