"""Background lease heartbeat with a fail-closed ownership check."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from app_generator.coordinator.client import CoordinatorClient, JobLease
from app_generator.errors import LeaseLostError


@dataclass
class LeaseGuard:
    client: CoordinatorClient
    lease: JobLease
    heartbeat_seconds: int
    lease_seconds: int
    _stop: threading.Event = field(default_factory=threading.Event, init=False)
    _thread: threading.Thread | None = field(default=None, init=False)
    _last_success: float = field(default_factory=time.monotonic, init=False)
    _failure: BaseException | None = field(default=None, init=False)

    def __enter__(self) -> "LeaseGuard":
        self._thread = threading.Thread(target=self._run, name="generator-lease-heartbeat", daemon=True)
        self._thread.start()
        return self

    def _run(self) -> None:
        while not self._stop.wait(self.heartbeat_seconds):
            try:
                self.lease = self.client.heartbeat(self.lease)
                self._last_success = time.monotonic()
                self._failure = None
            except LeaseLostError as exc:
                self._failure = exc
                return
            except BaseException as exc:
                self._failure = exc
                if time.monotonic() - self._last_success >= self.lease_seconds:
                    return

    def ensure_owned(self) -> None:
        if isinstance(self._failure, LeaseLostError):
            raise self._failure
        if time.monotonic() - self._last_success >= self.lease_seconds:
            raise LeaseLostError(f"Lease heartbeat expired after coordinator failure: {self._failure}")

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=min(5, self.heartbeat_seconds))
