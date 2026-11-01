"""Conservative multilingual QA triage, not a translation-quality oracle."""
from __future__ import annotations
import unicodedata
import re
from collections.abc import Mapping
from app_generator.validation.academic_qa import Finding

def scientific_malay_eternal_terms(document: Mapping) -> list[str]:
    """Locate science usage where Malay 'eternal' likely mistranslates 'conservative'.

    Returns metadata paths, never the protected localized sentences.
    'diabadikan' (conserved) is deliberately NOT the exact word 'abadi'.
    This negative test does not claim translation meaning is correct when empty.
    """
    suspects=[]
    physical=re.compile(
        r"(?i)\b(?:daya|spring|ayunan|perlanggaran|tenaga|sistem|"
        r"interaksi|pelesapan|graviti|kinetik|bampar)\b")
    exact=re.compile(r"(?i)\babadi\b")
    def visit(obj,route):
        if isinstance(obj,Mapping):
            if isinstance(obj.get("ms"),str):
                malay=obj["ms"]
                if exact.search(malay) and physical.search(malay):
                    suspects.append(route+"/ms")
            for name,value in obj.items():
                if name=="ms" and isinstance(value,str):
                    continue
                visit(value,route+"/"+str(name))
        elif isinstance(obj,list):
            for i,value in enumerate(obj):
                visit(value,route+"/"+str(i))
    visit(document,"")
    return suspects


def check_multilingual_surface(activity: Mapping) -> Finding:
    ref=f"activity:{activity.get('id', '?')}"
    texts=[]
    fields=["prompt","feedback"]
    fields.extend(["hints"] if activity.get("hints") else [])
    values=[activity.get("prompt"),activity.get("feedback")]
    values.extend(activity.get("hints",[]) if isinstance(activity.get("hints"),list) else [])
    if activity.get("type")=="mcq":
        values.extend(x.get("label") for x in activity.get("answerKey",{}).get("options",[]) if isinstance(x,dict))
    for index, value in enumerate(values):
        if not isinstance(value, Mapping) or any(not isinstance(value.get(lang),str) or not value[lang].strip()
                                               for lang in ("en","ms","zh")):
            return Finding("multilingual_meaning","FAIL","deterministic",ref,
                           f"missing or empty localized prose at field index {index}",True)
        norm={k:unicodedata.normalize("NFKC",value[k]).casefold().strip() for k in ("en","ms","zh")}
        if (len(norm["en"])>30 and norm["en"]==norm["zh"]):
            texts.append(f"English/Chinese identical long prose at field {index}")
        if (len(norm["en"])>30 and norm["en"]==norm["ms"]):
            texts.append(f"English/Malay identical long prose at field {index}")
    physics_terms=scientific_malay_eternal_terms(activity)
    if physics_terms:
        return Finding("multilingual_meaning","FAIL","deterministic",ref,
                       "Malay conservative-force terminology mistranslated as eternal at "
                       + ", ".join(physics_terms[:12]),True)
    if texts:
        return Finding("multilingual_meaning","REVIEW_REQUIRED","deterministic",ref,
                       "; ".join(texts),True)
    return Finding("multilingual_meaning","REVIEW_REQUIRED","deterministic",ref,
                   "EN-MS-ZH surface is populated; semantic translation equivalence not independently verified",True)
