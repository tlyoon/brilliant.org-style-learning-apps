#!/usr/bin/env python3
"""Build a minimal static review bundle for an explicitly selected package."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _resolve_package(package_path: Path) -> Path:
    source = package_path if package_path.is_absolute() else ROOT / package_path
    source = source.resolve()
    content_root = (ROOT / "content").resolve()
    try:
        source.relative_to(content_root)
    except ValueError as exc:
        raise ValueError("Public package must be selected from the repository content directory") from exc
    if source.name != "package.json" or not source.is_file():
        raise ValueError(f"Selected public package does not exist or is not package.json: {source}")
    return source


def build(output: Path, package_path: Path) -> None:
    """Create an empty-directory release bundle from one explicitly selected package."""
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Output directory must be empty: {output}")
    source_package = _resolve_package(package_path)
    output.mkdir(parents=True, exist_ok=True)

    source_index = (ROOT / "app" / "index.html").read_text(encoding="utf-8")
    public_index = source_index.replace('href="styles.css"', 'href="app/styles.css"').replace(
        'src="app.js"', 'src="app/app.js"'
    ).replace(
        'data-package-url=""',
        'data-package-url="./content/package.json"',
    )
    (output / "index.html").write_text(public_index, encoding="utf-8")
    (output / ".nojekyll").touch()

    for source, relative_target in (
        (ROOT / "app" / "app.js", Path("app/app.js")),
        (ROOT / "app" / "styles.css", Path("app/styles.css")),
        (source_package, Path("content/package.json")),
    ):
        target = output / relative_target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="Repository content/.../package.json to publish as a review bundle")
    parser.add_argument("output", type=Path, help="Empty directory for the public release bundle")
    args = parser.parse_args()
    try:
        build(args.output.resolve(), args.package)
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
