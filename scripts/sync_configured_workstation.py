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


def _configured_subprocess_run(original_run):
    """Keep the post-sync subprocess on this configured wrapper."""

    def run(arguments, *args, **kwargs):
        rewritten = arguments
        if (
            isinstance(arguments, list)
            and len(arguments) >= 2
            and Path(str(arguments[1])).name == "sync_workstation.py"
            and "--post-sync" in arguments
        ):
            rewritten = [
                arguments[0],
                "-m",
                "scripts.sync_configured_workstation",
                *arguments[2:],
            ]
        return original_run(rewritten, *args, **kwargs)

    return run


def main(argv: list[str] | None = None) -> int:
    # Keep the mature synchronization implementation in one place while making
    # both the initial and post-sync phases read the dedicated project authority.
    configure_core()
    original_run = core.subprocess.run
    core.subprocess.run = _configured_subprocess_run(original_run)
    try:
        return core.main(argv)
    finally:
        core.subprocess.run = original_run


if __name__ == "__main__":
    raise SystemExit(main())
