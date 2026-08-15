#!/usr/bin/env python3
"""Run lightweight repository lint checks without third-party packages."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".css", ".html", ".js", ".json", ".md", ".py", ".yml", ".yaml"}
IGNORED_PARTS = {".git", ".venv", "node_modules"}


def main() -> int:
    errors: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES or IGNORED_PARTS.intersection(path.parts):
            continue
        relative = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{relative}: is not valid UTF-8")
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if line.rstrip() != line:
                errors.append(f"{relative}:{number}: trailing whitespace")
            if "\t" in line:
                errors.append(f"{relative}:{number}: tab character")
        try:
            if path.suffix == ".json":
                json.loads(text)
            elif path.suffix == ".py":
                ast.parse(text, filename=str(relative))
        except (json.JSONDecodeError, SyntaxError) as exc:
            errors.append(f"{relative}: {exc}")

    if errors:
        print("Lint failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Lint passed (UTF-8, whitespace, JSON, and Python syntax).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
