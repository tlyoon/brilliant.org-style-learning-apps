"""Private exact-source audit of Chinese 1D/2D/zero numeric notation, no AI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_generator.validation.narrow_numeric_notation import (
    audit_private_narrow_numeric_notation,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("package", "pdf", "packets", "out"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    try:
        target = args.out.resolve()
        if (target.is_relative_to(ROOT) or target.exists() or
                not target.parent.is_dir()):
            raise ValueError("unique private-only report path outside Git required")
        report = audit_private_narrow_numeric_notation(
            package_file=args.package, source_pdf=args.pdf,
            source_packets_file=args.packets,
        )
        with target.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=True, indent=2, sort_keys=True)
            stream.write("\n")
        keys = ("status", "sourceVerifiedActivities", "originalNumericDriftFlags",
                "narrowNumericNotationMatches", "remainingUnresolvedNumericFlags",
                "academicQA", "academicPASS", "publicationAuthorized")
        print(json.dumps({k: report[k] for k in keys}))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({
            "status": "NARROW_NUMERIC_AUDIT_BLOCKED",
            "errorType": type(exc).__name__,
            "academicQA": "REVIEW_REQUIRED", "publicationAuthorized": False,
        }))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
