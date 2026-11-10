#!/usr/bin/env python3
"""Build one local preview or academic-gated minimal public learning bundle."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.domains import resolve_package_domain
from app_generator.runtime.academic_release import enforce_academic_release_gate
from app_generator.validation.final_acceptance_closure import assert_campaign_admissible


def _resolve_package(package_path: Path, source_root: Path = ROOT) -> Path:
    source = package_path if package_path.is_absolute() else source_root / package_path
    source = source.resolve()
    content_root = (source_root / "content").resolve()
    try:
        source.relative_to(content_root)
    except ValueError as exc:
        raise ValueError("Selected package must be under repository content") from exc
    if source.name != "package.json" or not source.is_file():
        raise ValueError("Selected package is not an existing package.json")
    return source


def build(
    output: Path, package_path: Path, *, source_root: Path = ROOT,
    local_preview: bool = False, validation_dir: Path | None = None,
) -> None:
    """Build with explicit preview intent or independent academic release proof.

    A standalone build is an alternate publication entry point. It must obey
    the same exact-package academic/visual gate as the automated publisher.
    A preview is marked unapproved and must not be deployed.
    """
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory must be empty")
    source_root = source_root.resolve()
    source_package = _resolve_package(package_path, source_root)
    original = source_package.read_bytes()
    package = json.loads(original.decode("utf-8"))
    if not isinstance(package, dict):
        raise ValueError("Selected package must contain a JSON object")

    if not local_preview:
        # This is an alternate public bundle entrypoint. Enforce the frozen
        # owner closure BEFORE any external/academic proof or output writes.
        # The shared academic gate separately protects automated publishing.
        assert_campaign_admissible(source_package, "publication")

    if local_preview:
        if validation_dir is not None:
            raise ValueError("Preview and release-validation modes are mutually exclusive")
    else:
        if not isinstance(validation_dir, Path):
            raise ValueError("Public bundle needs a separate private academic validation directory")
        target = validation_dir.resolve()
        output_root = output.resolve()
        if (target.is_relative_to(source_root)
                or target == output_root or target.is_relative_to(output_root)):
            raise ValueError("Private academic receipts must not be inside source or public bundle")
        report = enforce_academic_release_gate(source_root, source_package, target)
        # The gate reads the package again. Never bundle different bytes from
        # those independently checked, even if the source changes mid-build.
        if report.get("artifactSha256") != sha256(original).hexdigest():
            raise ValueError("Approved academic evidence does not match bundled package bytes")

    domain = resolve_package_domain(source_root, package)
    source_index = (source_root / "app" / "index.html").read_text(encoding="utf-8")
    index = source_index.replace('href="styles.css"', 'href="app/styles.css"').replace(
        'href="domain-styles.css"', 'href="app/domain-styles.css"'
    ).replace(
        'src="domain-renderers.js"', 'src="app/domain-renderers.js"'
    ).replace(
        'src="visual-renderers.js"', 'src="app/visual-renderers.js"'
    ).replace(
        'src="app.js"', 'src="app/app.js"'
    ).replace(
        'data-package-url=""',
        'data-package-url="./content/package.json"',
    )
    if local_preview:
        index = index.replace(
            "</head>",
            '    <meta name="robots" content="noindex, nofollow">\n  </head>',
        ).replace(
            '<main class="shell">',
            '<main class="shell">\n'
            '      <p class="prototype-notice" role="note">'
            'LOCAL DRAFT PREVIEW — NOT APPROVED FOR PUBLICATION'
            '</p>',
        )

    output.mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_text(index, encoding="utf-8")
    (output / ".nojekyll").touch()
    for source, relative in (
        (source_root / "app" / "app.js", Path("app/app.js")),
        (domain.path("visuals", "rendererScript"), Path("app/domain-renderers.js")),
        (source_root / "app" / "visual-renderers.js", Path("app/visual-renderers.js")),
        (source_root / "app" / "styles.css", Path("app/styles.css")),
        (domain.path("visuals", "stylesheet"), Path("app/domain-styles.css")),
    ):
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    content = output / "content" / "package.json"
    content.parent.mkdir(parents=True, exist_ok=True)
    content.write_bytes(original)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="Explicit repository content/.../package.json")
    parser.add_argument("output", type=Path, help="New or empty output directory")
    parser.add_argument(
        "--local-preview", action="store_true",
        help="Unapproved loopback-only draft preview; must not be deployed",
    )
    parser.add_argument(
        "--academic-validation-dir", type=Path,
        help="Private off-repository evidence directory for academic-gated public bundle",
    )
    args = parser.parse_args()
    if args.local_preview == (args.academic_validation_dir is not None):
        parser.error("Choose exactly one of --local-preview or --academic-validation-dir")
    try:
        build(
            args.output.resolve(), args.package, local_preview=args.local_preview,
            validation_dir=args.academic_validation_dir,
        )
    except (ValueError, OSError, json.JSONDecodeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
