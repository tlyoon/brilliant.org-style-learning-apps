"""Per-run directories and resumable structured stage storage."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app_generator.filesystem.outputs import write_json_atomic, write_text_atomic
from app_generator.runtime.state import StateStore

SAFE_STAGE = re.compile(r"^[a-z0-9-]+$")


@dataclass(frozen=True)
class RunContext:
    run_id: str
    root: Path
    logs: Path
    state_dir: Path
    candidate: Path
    batches: Path
    validation: Path
    diagnostics: Path
    sources: Path
    store: StateStore

    @classmethod
    def create(cls, state_root: Path, run_id: str | None = None) -> "RunContext":
        identifier = run_id or f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{uuid4().hex[:10]}"
        root = state_root / identifier
        directories = {
            name: root / name
            for name in ("logs", "state", "candidate", "batches", "validation", "diagnostics", "sources")
        }
        for directory in directories.values():
            directory.mkdir(parents=True, exist_ok=True)
        store = StateStore(directories["state"] / "run-state.json", identifier)
        return cls(
            identifier,
            root,
            directories["logs"],
            directories["state"],
            directories["candidate"],
            directories["batches"],
            directories["validation"],
            directories["diagnostics"],
            directories["sources"],
            store,
        )

    def save_stage(self, name: str, document: object, raw_response: str | None = None) -> None:
        if not SAFE_STAGE.fullmatch(name):
            raise ValueError(f"Unsafe stage name: {name}")
        write_json_atomic(self.batches / f"{name}.json", document)
        if raw_response is not None:
            write_text_atomic(self.batches / f"{name}.response.txt", raw_response)

    def save_raw_response(self, name: str, raw_response: str) -> None:
        if not SAFE_STAGE.fullmatch(name):
            raise ValueError(f"Unsafe stage name: {name}")
        write_text_atomic(self.batches / f"{name}.response.txt", raw_response)

    def load_stage(self, name: str) -> object | None:
        path = self.batches / f"{name}.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None

    def discard_stage(self, name: str) -> None:
        """Remove only a parsed generated-stage cache after contract rejection."""

        if not SAFE_STAGE.fullmatch(name):
            raise ValueError(f"Unsafe stage name: {name}")
        try:
            (self.batches / f"{name}.json").unlink()
        except FileNotFoundError:
            pass

    def discard_parsed_stages(self) -> None:
        """Remove generated parsed caches while retaining raw responses."""

        for path in self.batches.glob("*.json"):
            path.unlink()
