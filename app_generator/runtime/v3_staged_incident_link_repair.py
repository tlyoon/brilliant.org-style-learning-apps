"""BSA306: narrowly scoped automatic repair of two known historical links.

The stored candidate from 28 Nov referenced nonexistent 20261128 incidents,
although original incidents were correctly registered on 20261127. Only
replace those two exact references when their predecessors are present.
Never relax the recurrence contract or rewrite scientific evidence.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess

_FIXES=(
 ("BSA-20261128-300","BSA-20261128-294","BSA-20261127-294"),
 ("BSA-20261128-302","BSA-20261128-289","BSA-20261127-289"),
)

def repair_staged_known_incident_links(repo:Path)->dict:
    repo=repo.resolve()
    path=repo/"docs"/"recurrence_registry.json"
    if (path.is_symlink() or not path.is_file()
        or not path.resolve().is_relative_to(repo)
        or path.stat().st_size>1_500_000):
        raise ValueError("BSA306_UNTRUSTED_REGISTRY_PATH")
    staged=subprocess.run(["git","diff","--cached","--name-only"],
        cwd=repo,capture_output=True,text=True,check=False,timeout=40)
    if staged.returncode:
        raise ValueError("BSA306_STAGED_FILES_UNAVAILABLE")
    if "docs/recurrence_registry.json" not in staged.stdout.splitlines():
        return {"status":"BSA306_NO_STAGED_REGISTRY","fixed":[]}
    raw=path.read_text(encoding="utf8")
    before=json.loads(raw)
    incidents=before.get("incidents",[])
    if not isinstance(incidents,list):
        raise ValueError("BSA306_REGISTRY_SCHEMA_CHANGED")
    entries={row.get("id"):row for row in incidents if isinstance(row,dict)}
    if len(entries)!=len(incidents):
        raise ValueError("BSA306_DUPLICATE_OR_MALFORMED_INCIDENT")
    replacements=[]
    for incident,wrong,right in _FIXES:
        current=entries.get(incident)
        if current is None:
            continue
        refs=current.get("relatedIncidentIds")
        if (not isinstance(refs,list)
            or right not in entries
            or wrong not in refs and right not in refs):
            raise ValueError("BSA306_UNKNOWN_HISTORICAL_LINK_PATTERN")
        if wrong in refs:
            if (right in refs or raw.count('"'+wrong+'"')!=1):
                raise ValueError("BSA306_AMBIGUOUS_REPAIR_TARGET")
            replacements.append((incident,wrong,right))
    if not replacements:
        return {"status":"BSA306_ALREADY_VALID","fixed":[]}
    proposed=raw
    for _,wrong,right in replacements:
        proposed=proposed.replace('"'+wrong+'"','"'+right+'"')
    after=json.loads(proposed)
    # Ensure only the exact approved incident refs changed.
    expected=json.loads(raw)
    lookup={r["id"]:r for r in expected["incidents"]}
    for incident,wrong,right in replacements:
        refs=lookup[incident]["relatedIncidentIds"]
        refs[refs.index(wrong)]=right
    if after!=expected:
        raise ValueError("BSA306_UNEXPECTED_REGISTRY_MUTATION")
    path.write_text(proposed,encoding="utf8")
    restage=subprocess.run(["git","add","--","docs/recurrence_registry.json"],
        cwd=repo,capture_output=True,check=False,timeout=40)
    if restage.returncode:
        raise ValueError("BSA306_RESTAGE_FAILED")
    return {"status":"BSA306_EXACT_HISTORICAL_LINKS_REPAIRED",
            "fixed":[x[0] for x in replacements],
            "beforeSha256":sha256(raw.encode("utf8")).hexdigest(),
            "afterSha256":sha256(proposed.encode("utf8")).hexdigest(),
            "publicationAuthorized":False,"academicPASS":False}
