"""Conservative multilingual QA triage, not a translation-quality oracle."""
from __future__ import annotations
import unicodedata
import re
from collections.abc import Mapping
from app_generator.validation.academic_qa import Finding
from app_generator.validation.malay_conservation_lexicon import conservation_lexicon_flags

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


def _learner_visible_localized_fields(activity: Mapping) -> list[tuple[str, object]]:
    """Enumerate schema-defined prose fields, not arbitrary numeric visual data.

    Paths contain field names and array indices only, never private text.
    Optional fields are examined when present; absent optional fields are not
    evidence of translation errors. Schema validation checks full requiredness.
    """
    surfaces: list[tuple[str, object]] = [
        ("prompt", activity.get("prompt")),
        ("feedback", activity.get("feedback")),
    ]
    hints = activity.get("hints")
    if "hints" in activity:
        if not isinstance(hints, list) or not hints:
            surfaces.append(("hints", None))
        else:
            surfaces.extend((f"hints/{i}", value) for i, value in enumerate(hints))
    for key in ("answerLogic", "explanation", "accessibilityText"):
        if key in activity:
            surfaces.append((key, activity[key]))
    if "prerequisiteRecovery" in activity:
        recovery = activity["prerequisiteRecovery"]
        surfaces.append(("prerequisiteRecovery/prompt",
                         recovery.get("prompt") if isinstance(recovery, Mapping) else None))
    if activity.get("type") == "mcq":
        key = activity.get("answerKey")
        options = key.get("options") if isinstance(key, Mapping) else None
        if not isinstance(options, list) or not options:
            surfaces.append(("answerKey/options", None))
        else:
            for i, option in enumerate(options):
                surfaces.append((f"answerKey/options/{i}/label",
                                 option.get("label") if isinstance(option, Mapping) else None))
    elif activity.get("type") == "interactive":
        interaction = activity.get("interaction")
        if not isinstance(interaction, Mapping):
            surfaces.append(("interaction/items", None))
        else:
            for key in ("items", "targets"):
                if key == "targets" and key not in interaction:
                    continue
                records = interaction.get(key)
                if not isinstance(records, list) or not records:
                    surfaces.append((f"interaction/{key}", None))
                else:
                    for i, item in enumerate(records):
                        surfaces.append((f"interaction/{key}/{i}/label",
                                         item.get("label") if isinstance(item, Mapping) else None))
    visual = activity.get("visualSpec")
    if isinstance(visual, Mapping):
        entities = visual.get("entities", [])
        if isinstance(entities, list):
            for i, entity in enumerate(entities):
                if isinstance(entity, Mapping) and "label" in entity:
                    surfaces.append((f"visualSpec/entities/{i}/label", entity["label"]))
        accessibility = visual.get("accessibility")
        if isinstance(accessibility, Mapping) and "description" in accessibility:
            surfaces.append(("visualSpec/accessibility/description",
                             accessibility["description"]))
    return surfaces


def check_multilingual_surface(activity: Mapping) -> Finding:
    """Fail on missing translations in learner-visible fields; never grant PASS.

    This verifies presence and catches known language mistakes, not scientific
    semantic equivalence. Source-grounded independent EN/MS/ZH verification
    remains required for a formal academic PASS.
    """
    ref=f"activity:{activity.get('id', '?')}"
    texts = []
    for route, value in _learner_visible_localized_fields(activity):
        if (not isinstance(value, Mapping) or
                any(not isinstance(value.get(lang), str) or not value[lang].strip()
                    for lang in ("en", "ms", "zh"))):
            return Finding("multilingual_meaning", "FAIL", "deterministic", ref,
                           "missing or empty EN/MS/ZH at " + route, True)
        norm = {k: unicodedata.normalize("NFKC", value[k]).casefold().strip()
                for k in ("en", "ms", "zh")}
        if len(norm["en"]) > 30 and norm["en"] == norm["zh"]:
            texts.append("English/Chinese identical long prose at " + route)
        if len(norm["en"]) > 30 and norm["en"] == norm["ms"]:
            texts.append("English/Malay identical long prose at " + route)
    # This lexical failure is scoped to mechanics educational content;
    # "eternity" may be legitimate in unrelated history/literature topics.
    en_prompt = activity.get("prompt", {}).get("en", "")
    mechanics = bool(isinstance(en_prompt, str) and re.search(
        r"(?i)\b(?:collision|collide|momentum|kinetic|impulse|"
        r"glider|spring|ballistic|projectile|newton)\b", en_prompt))
    if mechanics:
        conservation_terms = conservation_lexicon_flags(activity)
        if conservation_terms:
            return Finding(
                "multilingual_meaning", "FAIL", "deterministic", ref,
                "Malay conservation expressed using eternity/immortalization "
                "terminology at " + ", ".join(conservation_terms[:12]), True)
    physics_terms = scientific_malay_eternal_terms(activity)
    if physics_terms:
        return Finding("multilingual_meaning", "FAIL", "deterministic", ref,
                       "Malay conservative-force terminology mistranslated as eternal at "
                       + ", ".join(physics_terms[:12]), True)
    if texts:
        return Finding("multilingual_meaning", "REVIEW_REQUIRED", "deterministic", ref,
                       "; ".join(texts), True)
    return Finding("multilingual_meaning", "REVIEW_REQUIRED", "deterministic", ref,
                   "EN-MS-ZH learner-visible fields are populated; scientific semantic "
                   "equivalence not independently verified", True)
