"""Source-bound private cart/spring physics diagram check without AI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app_generator.validation.bounded_diagram_physics import (
    audit_source_bound_diagram_physics,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("package", "pdf", "packets", "out"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    try:
        output = args.out.resolve()
        if output.is_relative_to(ROOT) or output.exists() or not output.parent.is_dir():
            raise ValueError("unique private output outside Git required")
        result = audit_source_bound_diagram_physics(
            package_file=args.package,source_pdf=args.pdf,packets_file=args.packets,
        )
        with output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, sort_keys=True, ensure_ascii=True, indent=2)
            stream.write("\n")
        keys = ("status", "sourceActivitiesReverified",
                "boundedDiagramActivitiesChecked", "cartInitialConfigurationsChecked",
                "exactSpringEnergyLedgerChecked", "academicQA", "formalAcademicPASS",
                "publicationAuthorized")
        print(json.dumps({k: result[k] for k in keys}))
        return 0
    except (KeyError, ValueError, TypeError, OSError) as exc:
        print(json.dumps({"status":"DIAGRAM_PHYSICS_AUDIT_BLOCKED",
                          "errorType":type(exc).__name__,
                          "academicQA":"REVIEW_REQUIRED",
                          "publicationAuthorized":False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
