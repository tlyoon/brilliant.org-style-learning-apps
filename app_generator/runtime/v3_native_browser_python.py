"""BSA246: select the authorized local browser Python before stateful V1-V19.

Never trigger model calls, fetch packages, or repair global site-packages.
Use Bosla's pinned Windows venv when the invoking Python lacks Selenium.
"""
from pathlib import Path


def select_source_free_browser_interpreter(
    *, repo: Path, current: Path, windows: bool,
    source_free: bool, selenium_available: bool,
) -> tuple[str, Path | None]:
    """Pure decision. No web, installs, provider calls, writes or relaunch."""
    if not windows or not source_free or selenium_available:
        return "USE_CURRENT_PYTHON", None
    candidate = repo / ".venv" / "Scripts" / "python.exe"
    if (candidate.is_symlink() or not candidate.is_file()
            or repo.is_symlink() or not repo.is_dir()):
        return "STOP_PINNED_BROWSER_RUNTIME_MISSING", None
    if candidate.resolve() == current.resolve():
        return "STOP_PINNED_BROWSER_RUNTIME_MISSING", None
    return "REEXEC_PINNED_BROWSER_PYTHON", candidate
