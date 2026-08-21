"""Cross-platform, per-Gem worker lock."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import IO

from app_generator.errors import WorkerLockError


class WorkerLock:
    def __init__(self, lock_root: Path, gem_url: str) -> None:
        digest = hashlib.sha256(gem_url.encode("utf-8")).hexdigest()[:20]
        self.path = lock_root / "locks" / f"gem-{digest}.lock"
        self._handle: IO[str] | None = None

    def __enter__(self) -> "WorkerLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+", encoding="utf-8")
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                if handle.read(1) == "":
                    handle.write("0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            handle.close()
            raise WorkerLockError(f"Another process is already using this Gem: {self.path}") from exc
        handle.seek(0)
        handle.truncate()
        handle.write(str(os.getpid()))
        handle.flush()
        self._handle = handle
        return self

    def __exit__(self, *_: object) -> None:
        if not self._handle:
            return
        if os.name == "nt":
            import msvcrt
            self._handle.seek(0)
            msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        self._handle.close()
        self._handle = None
