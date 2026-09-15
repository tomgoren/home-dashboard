"""Runs a WeatherProvider on a background thread so a slow/failed network
request never stalls the render loop. The main loop only ever reads
`.snapshot`, which is always the latest data available (live, or the last
good one with `.stale` set).
"""

from __future__ import annotations

import sys
import threading
from dataclasses import replace
from pathlib import Path

from app.weather import cache
from app.weather.model import WeatherSnapshot
from app.weather.provider import WeatherProvider


class BackgroundRefresher:
    def __init__(
        self,
        provider: WeatherProvider,
        cache_path: Path,
        interval_seconds: int,
        initial_snapshot: WeatherSnapshot,
    ):
        self._provider = provider
        self._cache_path = cache_path
        self._interval = interval_seconds
        self._lock = threading.Lock()
        self._snapshot = initial_snapshot
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()

    @property
    def snapshot(self) -> WeatherSnapshot:
        with self._lock:
            return self._snapshot

    def force_refresh(self) -> None:
        self._wake.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            self._fetch_once()
            self._wake.wait(self._interval)
            self._wake.clear()

    def _fetch_once(self) -> None:
        try:
            snapshot = self._provider.fetch()
        except Exception as exc:  # noqa: BLE001 - never let a network hiccup kill the appliance
            print(f"[weather] refresh failed: {exc}", file=sys.stderr)
            with self._lock:
                self._snapshot = replace(self._snapshot, stale=True)
            return

        with self._lock:
            self._snapshot = snapshot
        try:
            cache.save(self._cache_path, snapshot)
        except OSError as exc:
            print(f"[weather] cache write failed: {exc}", file=sys.stderr)
