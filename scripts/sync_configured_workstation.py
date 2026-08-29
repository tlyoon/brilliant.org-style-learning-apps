#!/usr/bin/env python3
"""Run workstation synchronization using config/configure_project.toml as project authority."""

from __future__ import annotations

from pathlib import Path

from scripts import sync_workstation as core


CONFIGURE_PROJECT_RELATIVE_PATH = Path("config") / "configure_project.toml"


def configure_core() -> None:
    """Point the hardened synchronizer at the dedicated project configuration authority."""

    core.PROJECT_CONFIG_RELATIVE_PATH = CONFIGURE_PROJECT_RELATIVE_PATH
    core.MANAGED_CONFIG_HEADER = (
        "# Managed by scripts/sync_workstation.py; edit config/configure_project.toml through Git.\n"
    )
    core.ALLOWED_PROJECT_KEYS = {
        **core.ALLOWED_PROJECT_KEYS,
        "compatibility": {"legacy_environment_prefix"},
    }


def main(argv: list[str] | None = None) -> int:
    # Keep the mature synchronization implementation in one place while making
    # the user-facing entrypoint read the dedicated project-specific authority.
    configure_core()
    return core.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
