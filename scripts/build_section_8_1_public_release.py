#!/usr/bin/env python3
"""Build the minimal dual-version Section 8.1 public review site."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_PATH = Path("content/chapter-8/section-8-1/package.json")
VERSION_ONE_COMMIT = "38b6b59d4d5c0fc408406721c445baf78c00980d"
EXPECTED_PACKAGE_ID = "chapter-8-section-8-1"


def _validate_public_package(payload: bytes, label: str) -> None:
    try:
        package = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not valid UTF-8 JSON: {exc}") from exc
    if package.get("packageId") != EXPECTED_PACKAGE_ID:
        raise ValueError(f"{label} has an unexpected packageId")
    if package.get("status") != "draft":
        raise ValueError(f"{label} must remain explicitly labelled as draft")
    if len(package.get("activities", [])) != 18:
        raise ValueError(f"{label} must contain exactly 18 activities")


def version_one_package() -> bytes:
    """Read the immutable initial Section 8.1 draft from its introducing commit."""

    result = subprocess.run(
        ["git", "show", f"{VERSION_ONE_COMMIT}:{PACKAGE_PATH.as_posix()}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    _validate_public_package(result.stdout, "Section 8.1 Version 1")
    return result.stdout


def version_two_package() -> bytes:
    """Read the current regenerated Section 8.1 draft."""

    payload = (ROOT / PACKAGE_PATH).read_bytes()
    _validate_public_package(payload, "Section 8.1 Version 2")
    return payload


def _version_page(version: str, label: str, package_url: str) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex, nofollow">
    <title>Section 8.1 {label} Review Prototype</title>
    <link rel="stylesheet" href="../app/styles.css">
  </head>
  <body>
    <main class="shell">
      <header class="topbar">
        <a class="brand" href="../">Section 8.1 — {label}</a>
        <label>Language
          <select id="locale" aria-label="Language">
            <option value="en">English</option>
            <option value="ms">Bahasa Melayu</option>
            <option value="zh">简体中文</option>
          </select>
        </label>
      </header>
      <p class="prototype-notice" role="note">Draft review prototype — {label}; not approved for publication.</p>
      <section id="app" aria-live="polite" data-package-url="{package_url}">
        <p>Loading Section 8.1 {version}…</p>
      </section>
    </main>
    <script type="module" src="../app/app.js"></script>
  </body>
</html>
"""


def _landing_page() -> str:
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex, nofollow">
    <title>Section 8.1 Dual-Version Review Prototype</title>
    <link rel="stylesheet" href="app/styles.css">
    <style>
      .version-grid { display: grid; gap: 1rem; margin: 1rem 0 3rem; }
      .version-link { display: block; margin-top: 1rem; text-decoration: none; }
      .privacy-note { color: #4b6659; }
    </style>
  </head>
  <body>
    <main class="shell">
      <header class="topbar"><span class="brand">Section 8.1 Learning</span></header>
      <p class="prototype-notice" role="note">Public draft review prototypes — neither version is approved for publication.</p>
      <h1>Choose a Section 8.1 version</h1>
      <div class="version-grid">
        <section class="card">
          <p class="eyebrow">Version 1</p>
          <h2>Initial generated draft</h2>
          <p>Open the earlier validated 18-activity package.</p>
          <a class="action version-link" href="v1/">Open Version 1</a>
        </section>
        <section class="card">
          <p class="eyebrow">Version 2</p>
          <h2>Regenerated draft</h2>
          <p>Open the later validated 18-activity package.</p>
          <a class="action version-link" href="v2/">Open Version 2</a>
        </section>
      </div>
      <p class="privacy-note">This static review site has no accounts, analytics, audio capture, or student-data storage.</p>
    </main>
  </body>
</html>
"""


def build(output: Path) -> None:
    """Create an empty-directory release bundle containing only public runtime files."""

    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Output directory must be empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    packages = {
        Path("content/v1/package.json"): version_one_package(),
        Path("content/v2/package.json"): version_two_package(),
    }
    files = {
        Path("index.html"): _landing_page().encode("utf-8"),
        Path("v1/index.html"): _version_page(
            "Version 1", "Version 1", "../content/v1/package.json"
        ).encode("utf-8"),
        Path("v2/index.html"): _version_page(
            "Version 2", "Version 2", "../content/v2/package.json"
        ).encode("utf-8"),
        **packages,
    }
    for relative, payload in files.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)

    for source, relative in (
        (ROOT / "app" / "app.js", Path("app/app.js")),
        (ROOT / "app" / "styles.css", Path("app/styles.css")),
    ):
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    (output / ".nojekyll").touch()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Empty directory for the public release bundle")
    args = parser.parse_args()
    try:
        build(args.output.resolve())
    except (subprocess.CalledProcessError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
