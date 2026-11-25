"""Fail-closed, source-bound Malay mechanics terminology repairs.

Private v5 content stays unchanged. The patch is constrained to 17 specific
Malay field paths and 20 replacements of mistranslated conservative /
nonconservative terminology. No private passages are embedded in Git.
It does NOT independently accept academic translation quality or release.
"""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster

V5_SHA = "27fc89bdf306400e1aef328b8df9d9cd5702912e00f8759b934de1b6fb1b5f0d"
ORIGINAL_PDF_SHA = "08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578"

# A narrowly curated 17-field scientific terminology correction. Values are
# short terminology snippets, not full copyrighted/protected passages.
RULES = (
    ("/prerequisites/2/description/ms", "daya abadi", "daya konservatif"),
    ("/prerequisites/2/recovery/ms", "pelesapan bukan abadi",
     "pelesapan akibat daya bukan konservatif"),
    ("/activities/6/feedback/ms", "ayunan abadi",
     "ayunan yang mengekalkan tenaga mekanikal"),
    ("/activities/6/answerLogic/ms", "daya ubah bentuk dalaman bukan abadi",
     "daya ubah bentuk dalaman bukan konservatif"),
    ("/activities/6/explanation/ms", "daya graviti abadi",
     "daya graviti konservatif"),
    ("/activities/6/prerequisiteRecovery/prompt/ms", "daya bukan abadi",
     "daya bukan konservatif"),
    ("/activities/8/answerLogic/ms", "Daya spring adalah abadi",
     "Daya spring bersifat konservatif"),
    ("/activities/8/prerequisiteRecovery/prompt/ms", "sistem abadi",
     "sistem konservatif"),
    ("/activities/13/hints/0/ms", "tenaga kinetik kekal abadi",
     "tenaga kinetik sentiasa terpelihara"),
    ("/activities/13/answerLogic/ms", "bampar spring abadi",
     "bampar spring ideal tanpa pelesapan"),
    ("/activities/13/interaction/items/0/label/ms", "bampar spring abadi",
     "bampar spring ideal tanpa pelesapan"),
    ("/activities/14/answerLogic/ms", "tenaga kinetik sentiasa abadi",
     "tenaga kinetik sentiasa terpelihara"),
    ("/activities/15/answerLogic/ms", "daya ubah bentuk bukan abadi",
     "daya ubah bentuk bukan konservatif"),
    ("/activities/15/answerLogic/ms", "daya sentuhan bukan abadi",
     "daya sentuhan bukan konservatif"),
    ("/activities/15/prerequisiteRecovery/prompt/ms",
     "daya lesapan bukan abadi", "daya lesapan bukan konservatif"),
    ("/activities/15/prerequisiteRecovery/prompt/ms",
     "daya ubah bentuk bukan abadi", "daya ubah bentuk bukan konservatif"),
    ("/activities/17/prompt/ms", "spring abadi ideal",
     "spring ideal tanpa pelesapan"),
    ("/activities/17/explanation/ms", "daya interaksi abadi",
     "daya interaksi konservatif"),
    ("/activities/17/explanation/ms", "perlanggaran bukan abadi",
     "perlanggaran tak kenyal"),
    ("/activities/17/prerequisiteRecovery/prompt/ms",
     "interaksi abadi", "interaksi konservatif"),
)


def _node(doc: dict, pointer: str):
    value = doc
    parts = pointer.strip("/").split("/")
    for segment in parts[:-1]:
        value = value[int(segment)] if isinstance(value,list) else value[segment]
    return value,parts[-1]


def _malay_misconceptions(node, key=""):
    if isinstance(node,dict):
        return sum(_malay_misconceptions(v,k) for k,v in node.items())
    if isinstance(node,list):
        return sum(_malay_misconceptions(v,key) for v in node)
    return len(re.findall(r"\babadi\b",node,flags=re.I)) if key=="ms" and isinstance(node,str) else 0


def patch_private_semantics(package: dict) -> tuple[dict,dict]:
    """Copy-on-write exact repair. All other fields are byte-semantically identical."""
    if len(package.get("activities",[]))!=18:
        raise ValueError("18-activity pilot roster changed")
    original_count=_malay_misconceptions(package)
    if original_count!=len(RULES):
        raise ValueError("new or missing Malay conservative terminology found")
    repaired=deepcopy(package)
    modified=[]
    for pointer,old,new in RULES:
        if pointer.count("/ms")!=1 or "abadi" not in old:
            raise ValueError("unsafe scope")
        parent,key=_node(repaired,pointer)
        text=parent.get(key) if isinstance(parent,dict) else None
        if not isinstance(text,str) or text.count(old)!=1 or old in new:
            raise ValueError("unexpected source text for scoped terminology")
        parent[key]=text.replace(old,new,1)
        modified.append(pointer)
    if _malay_misconceptions(repaired):
        raise ValueError("Malay conservative scientific terms remain mistranslated")
    if len(modified)!=20 or len(set(modified))!=17:
        raise ValueError("repair count or field roster drifted")
    report={
      "status":"BOUNDED_MALAY_CONSERVATIVE_TERMINOLOGY_REPAIRED",
      "changedTermOccurrences":len(modified),
      "changedLocalizedFields":len(set(modified)),
      "unchangedOriginalActivities":18,
      "otherLanguagesModified":False,
      "englishAndChineseUnchanged":True,
      "academicQA":"REVIEW_REQUIRED",
      "translationSemanticsAccepted":False,
      "formalAcademicPASS":0,
      "publicationAuthorized":False,
      "affectedPaths":sorted(set(modified)),
    }
    return repaired,report


def emit_versioned_private_candidate(
    *,package_file:Path,source_pdf:Path,packets_file:Path,out_directory:Path,
)->dict:
    if out_directory.exists() or out_directory.resolve().is_relative_to(Path(__file__).resolve().parents[2]):
        raise ValueError("new private version directory outside repository required")
    receipt=verify_full_source_packet_roster(
        package_file=package_file,source_pdf=source_pdf,
        packets_file=packets_file,expected_count=18)
    if (receipt["packageSha256"]!=V5_SHA or
            receipt["sourceSha256"]!=ORIGINAL_PDF_SHA or
            receipt["newlyReverifiedSourceActivities"]!=18):
        raise ValueError("original controlled source/package mismatch")
    raw=json.loads(package_file.read_text(encoding="utf-8"))
    changed,report=patch_private_semantics(raw)
    manifest=json.loads(packets_file.read_text(encoding="utf-8"))
    out_directory.mkdir(parents=True,exist_ok=False)
    changed_bytes=(json.dumps(changed,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    new_sha=sha256(changed_bytes).hexdigest()
    manifest["packageSha256"]=new_sha
    (out_directory/"package.json").write_bytes(changed_bytes)
    (out_directory/"source-packets-full18.json").write_text(
        json.dumps(manifest,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    new_receipt=verify_full_source_packet_roster(
        package_file=out_directory/"package.json",source_pdf=source_pdf,
        packets_file=out_directory/"source-packets-full18.json",expected_count=18)
    if (new_receipt["newlyReverifiedSourceActivities"]!=18 or
            new_receipt["sourceSha256"]!=ORIGINAL_PDF_SHA):
        raise ValueError("repaired source packets not verifiable")
    report.update({"oldPackageSha256":V5_SHA,"newPackageSha256":new_sha,
                   "originalPdfSha256":ORIGINAL_PDF_SHA,
                   "newSourcePacketActivitiesReverified":18,
                   "privateCandidateVersion":"v6-scientific-translation-draft",
                   "formalAcademicPASS":0,"publicationAuthorized":False})
    (out_directory/"private-repair-receipt.json").write_text(
        json.dumps(report,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    return report
