"""Conservative multilingual QA triage, not a translation-quality oracle."""
from __future__ import annotations
import unicodedata
from collections.abc import Mapping
from app_generator.validation.academic_qa import Finding

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
    if texts:
        return Finding("multilingual_meaning","REVIEW_REQUIRED","deterministic",ref,
                       "; ".join(texts),True)
    return Finding("multilingual_meaning","REVIEW_REQUIRED","deterministic",ref,
                   "EN-MS-ZH surface is populated; semantic translation equivalence not independently verified",True)
