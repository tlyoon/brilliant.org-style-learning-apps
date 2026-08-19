#!/usr/bin/env python3
"""Build the minimal static bundle for the public Section 1.1 review prototype."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = (
    (ROOT / "app" / "app.js", Path("app/app.js")),
    (ROOT / "app" / "styles.css", Path("app/styles.css")),
    (
        ROOT / "content" / "chapter-1" / "section-1-1" / "package.json",
        Path("content/chapter-1/section-1-1/package.json"),
    ),
)


def build(output: Path) -> None:
    """Create an empty-directory release bundle without internal repository material."""
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Output directory must be empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    source_index = (ROOT / "app" / "index.html").read_text(encoding="utf-8")
    public_index = source_index.replace('href="styles.css"', 'href="app/styles.css"').replace(
        'src="app.js"', 'src="app/app.js"'
    )
    (output / "index.html").write_text(public_index, encoding="utf-8")
    (output / ".nojekyll").touch()

    for source, relative_target in PUBLIC_FILES:
        target = output / relative_target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Empty directory for the public release bundle")
    args = parser.parse_args()
    try:
        build(args.output.resolve())
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
