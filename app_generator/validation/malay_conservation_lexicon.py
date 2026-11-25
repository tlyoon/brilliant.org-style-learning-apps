"""Bounded, private source-bound repair of Malay physics-conservation vocabulary.

The non-physics Malay roots for "eternity/immortalize" are not appropriate for
momentum or energy conservation. Fail closed on source identity, expected token
roster, immutable target, and all unexpected non-Malay modifications.
No private textbook or learning passages are stored in Git.
"""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster

V8_SHA = "3fc1da4f60bd0550857ac8bc5bb4f16d17d2a5e54ee44e87ebe474246e2e0c9e"
PDF_SHA = "08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578"
ROOTS = (
    ("keabadian","pemuliharaan",59),
    ("mengabadikan","mengekalkan",18),
    ("diabadikan","dikekalkan",69),
)
EXPECTED_FIELDS = 101
EXPECTED_TOTAL = 146


def _replace_in_malay(node, path, changed_paths, counts):
    if isinstance(node,dict):
        out={}
        for key,value in node.items():
            if key=="ms" and isinstance(value,str):
                text=value
                for source,target,_expected in ROOTS:
                    pattern=r"\b"+source+r"\b"
                    def sub(match):
                        counts[source]+=1
                        term=match.group(0)
                        if term.isupper(): return target.upper()
                        if term[0].isupper():return target[0].upper()+target[1:]
                        return target
                    text=re.sub(pattern,sub,text,flags=re.IGNORECASE)
                if text!=value:changed_paths.append(path+"/ms")
                out[key]=text
            else:
                out[key]=_replace_in_malay(value,path+"/"+str(key),changed_paths,counts)
        return out
    if isinstance(node,list):
        return [_replace_in_malay(v,path+"/"+str(i),changed_paths,counts) for i,v in enumerate(node)]
    return node


def conservation_lexicon_flags(node)->list[str]:
    """Only metadata paths; source text never leaves private container."""
    flags=[]
    def visit(x,path):
        if isinstance(x,dict):
            for k,v in x.items():
                if k=="ms" and isinstance(v,str):
                    if any(re.search(r"\b"+src+r"\b",v,re.I) for src,_,_ in ROOTS):
                        flags.append(path+"/ms")
                else:visit(v,path+"/"+str(k))
        elif isinstance(x,list):
            for i,v in enumerate(x):visit(v,path+"/"+str(i))
    visit(node,"")
    return flags


def repair_private_malay_v9(package):
    if len(package.get("activities",[]))!=18:
        raise ValueError("controlled activity roster invalid")
    original=deepcopy(package)
    counts={src:0 for src,_,_ in ROOTS}
    paths=[]
    result=_replace_in_malay(package,"",paths,counts)
    if package!=original:
        raise ValueError("copy-on-write source mutation")
    if (counts!={src:num for src,_,num in ROOTS} or
        sum(counts.values())!=EXPECTED_TOTAL or
        len(paths)!=EXPECTED_FIELDS or len(set(paths))!=EXPECTED_FIELDS or
        conservation_lexicon_flags(result)):
        raise ValueError("Malay conservation terminology changed outside original roster")
    return result,{"status":"SCOPED_MALAY_PHYSICS_CONSERVATION_VOCABULARY_REPAIRED",
        "localizedScientificTermReplacements":sum(counts.values()),
        "changedMalayFields":len(paths),
        "originalTermCounts":counts,
        "otherLocalesChanged":False,
        "academicQA":"REVIEW_REQUIRED","formalAcademicPASS":0,
        "publicationAuthorized":False,
        "changedFieldPaths":paths}


def create_private_v9(*,package_file,source_pdf,packets_file,output_dir):
    if output_dir.exists() or output_dir.resolve().is_relative_to(
        Path(__file__).resolve().parents[2]):
        raise ValueError("new private directory outside repository required")
    proof=verify_full_source_packet_roster(
        package_file=package_file,source_pdf=source_pdf,
        packets_file=packets_file,expected_count=18)
    if (proof["packageSha256"]!=V8_SHA or proof["sourceSha256"]!=PDF_SHA or
        proof["newlyReverifiedSourceActivities"]!=18 or
        proof["publicationAuthorized"] is not False):
        raise ValueError("original source/private v8 identity mismatch")
    old=json.loads(package_file.read_text("utf-8"))
    new,report=repair_private_malay_v9(old)
    manifest=json.loads(packets_file.read_text("utf-8"))
    data=(json.dumps(new,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    digest=sha256(data).hexdigest()
    manifest["packageSha256"]=digest
    output_dir.mkdir(parents=True,exist_ok=False)
    (output_dir/"package.json").write_bytes(data)
    (output_dir/"source-packets-full18.json").write_text(
        json.dumps(manifest,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    after=verify_full_source_packet_roster(
        package_file=output_dir/"package.json",source_pdf=source_pdf,
        packets_file=output_dir/"source-packets-full18.json",expected_count=18)
    if (after["newlyReverifiedSourceActivities"]!=18 or
        after["sourceSha256"]!=PDF_SHA or after["packageSha256"]!=digest):
        raise ValueError("repaired private source roster could not be verified")
    report.update({"originalPdfSha256":PDF_SHA,"oldV8PackageSha256":V8_SHA,
        "newV9PackageSha256":digest,"originalSourceActivitiesReverified":18,
        "privateRevision":"v9-malay-conservation-draft"})
    (output_dir/"private-repair-receipt.json").write_text(
        json.dumps(report,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    return report
