"""Fail-closed incident-to-regression guard for the development contract.

No network, credentials, source PDFs, student data or real browser required.
The historical ledger has duplicate legacy IDs; new IDs after the cutover
must be unique and represented in the machine-readable registry.
"""
from __future__ import annotations

import ast
from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"^BSA-(\d{8})-(\d{3})$")
LEDGER_RE = re.compile(r"\|\s*(BSA-\d{8}-\d{3})\s*\|")
CUTOVER = "BSA-20261102-096"
REQUIRED_BASELINE = frozenset({
    "BSA-20261023-003",
    "BSA-20261024-001",
    "BSA-20261024-004",
    "BSA-20261030-048",
    "BSA-20261030-049",
    "BSA-20261030-051",
    "BSA-20261030-052",
    "BSA-20261031-055",
    "BSA-20261031-057",
    "BSA-20261031-058",
    "BSA-20261031-059",
    "BSA-20261031-060",
    "BSA-20261031-061",
    "BSA-20261031-062",
    "BSA-20261031-063",
    "BSA-20261031-066",
    "BSA-20261031-067",
    "BSA-20261031-070",
    "BSA-20261101-074",
    "BSA-20261101-077",
    "BSA-20261102-090",
    "BSA-20261102-091",
    "BSA-20261102-094",
    "BSA-20261102-096",
    "BSA-20261102-097",
})
STANDARD_PYTHON_CI = "python -m unittest discover -s tests -v"
GUARD_CI = "python scripts/check_regression_contract.py"


def _repo_file(root: Path, name: object) -> Path | None:
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        return None
    if (name.startswith("/") or any(part in ("", ".", "..") for part in name.split("/"))
            or ":" in name):
        return None
    target = (root / name).resolve()
    return target if target.is_relative_to(root.resolve()) and target.is_file() else None


def _python_has_test(source: str, marker: str) -> bool:
    """Accept only an active unittest.TestCase method in normal discovery.

    A bare test-named function, an inert nested helper or an explicitly
    skipped method must not satisfy a supposedly permanent regression.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    if not marker.startswith("test_") or not marker.isidentifier():
        return False
    for cls in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        is_test_case = any(
            (isinstance(base, ast.Name) and base.id == "TestCase")
            or (isinstance(base, ast.Attribute) and base.attr == "TestCase")
            for base in cls.bases
        )
        if not is_test_case:
            continue
        if any(
            isinstance(decorator, (ast.Name, ast.Attribute))
            and (
                (isinstance(decorator, ast.Name) and decorator.id == "skip")
                or (isinstance(decorator, ast.Attribute) and decorator.attr == "skip")
            )
            for decorator in cls.decorator_list
        ):
            continue
        for method in cls.body:
            if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) or method.name != marker:
                continue
            decorators = [
                dec.func if isinstance(dec, ast.Call) else dec
                for dec in method.decorator_list
            ]
            if any(
                (isinstance(dec, ast.Name) and dec.id == "skip")
                or (isinstance(dec, ast.Attribute) and dec.attr == "skip")
                for dec in decorators
            ):
                continue
            return True
    return False


def _js_has_assertion(source: str, marker: str) -> bool:
    # Require the marker on a line that is actually an assertion, rather
    # than an inert comment or an explanatory contract paragraph.
    if not marker or len(marker) < 12 or "\n" in marker:
        return False
    return any(marker in line and re.search(r"\bassert(?:\.|\()", line)
               and not line.lstrip().startswith(("//", "*", "/*"))
               for line in source.splitlines())


def verify(root: Path = ROOT) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    registry_path = _repo_file(root, "docs/recurrence_registry.json")
    ledger_path = _repo_file(root, "docs/FAILURE_TO_FIX_LEDGER.md")
    workflow_path = _repo_file(root, ".github/workflows/validate.yml")
    if not all((registry_path, ledger_path, workflow_path)):
        return ["registry, ledger and validation workflow must exist"]
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (ValueError, OSError, UnicodeError):
        return ["recurrence registry is not valid UTF-8 JSON"]
    if not isinstance(registry, dict):
        return ["recurrence registry must be a JSON object"]
    if type(registry.get("schemaVersion")) is not int or registry["schemaVersion"] != 1:
        errors.append("unsupported recurrence registry schema version")
    if registry.get("cutoverIncident") != CUTOVER:
        errors.append("recurrence cutover cannot be silently weakened")
    if registry.get("policyDecision") != "docs/decisions/0027-regression-immunity-and-recovery.md":
        errors.append("regression contract decision path mismatch")
    elif _repo_file(root, registry["policyDecision"]) is None:
        errors.append("approved contract decision is missing")

    workflow = workflow_path.read_text(encoding="utf-8")
    if STANDARD_PYTHON_CI not in workflow or GUARD_CI not in workflow:
        errors.append("full Python discovery and recurrence contract guard must run in CI")

    entries = registry.get("incidents")
    if not isinstance(entries, list):
        return errors + ["incidents must be a JSON list"]
    ledger = ledger_path.read_text(encoding="utf-8")
    ledger_counts = Counter(LEDGER_RE.findall(ledger))
    registered: set[str] = set()

    for position, entry in enumerate(entries):
        prefix = f"incident[{position}]"
        if not isinstance(entry, dict):
            errors.append(prefix + " must be an object")
            continue
        ident = entry.get("id")
        if not isinstance(ident, str) or not ID_RE.fullmatch(ident):
            errors.append(prefix + " has invalid incident ID")
            continue
        if ident in registered:
            errors.append(ident + " duplicates registry incident ID")
            continue
        registered.add(ident)
        if ledger_counts[ident] == 0:
            errors.append(ident + " missing from failure-to-fix ledger")
        if ident >= CUTOVER and ledger_counts[ident] != 1:
            errors.append(ident + " must occur exactly once in new ledger entries")
        if not isinstance(entry.get("class"), str) or len(entry["class"]) < 3:
            errors.append(ident + " has no failure class")
        status = entry.get("status")
        if status not in ("resolved", "active"):
            errors.append(ident + " has unknown status")
            continue
        if status == "active":
            if not isinstance(entry.get("nextAction"), str) or len(entry["nextAction"].strip()) < 12:
                errors.append(ident + " active issue lacks actionable next step")
            continue
        cases = entry.get("regressions")
        if not isinstance(cases, list) or not cases:
            errors.append(ident + " resolved incident lacks regression cases")
            continue
        for case in cases:
            if not isinstance(case, dict):
                errors.append(ident + " regression entry must be an object")
                continue
            name, kind, marker = case.get("path"), case.get("kind"), case.get("marker")
            test_file = _repo_file(root, name)
            if (not isinstance(name, str) or not name.startswith("tests/test_") or
                    test_file is None):
                errors.append(ident + " references missing or unsafe regression test")
                continue
            if not isinstance(marker, str):
                errors.append(ident + " regression marker missing")
                continue
            source = test_file.read_text(encoding="utf-8")
            if kind == "python" and name.endswith(".py"):
                if not _python_has_test(source, marker):
                    errors.append(ident + " Python test method is missing: " + marker)
            elif kind == "javascript" and name.endswith(".js"):
                if not _js_has_assertion(source, marker):
                    errors.append(ident + " JS assertion is missing: " + marker)
                if f"node {name}" not in workflow:
                    errors.append(ident + " JS regression must run directly in CI: " + name)
            else:
                errors.append(ident + " has unsupported regression kind")

    for ident in sorted(REQUIRED_BASELINE - registered):
        errors.append(ident + " protected baseline recurrence entry was deleted")
    for ident in sorted(ledger_counts):
        if ident >= CUTOVER and ident not in registered:
            errors.append(ident + " new incident absent from recurrence registry")
    return errors


def main() -> int:
    problems = verify()
    if problems:
        for problem in problems[:50]:
            print("RECURRENCE CONTRACT FAIL:", problem)
        return 1
    print("Recurrence contract passed: registered incidents, executable tests and CI coverage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
