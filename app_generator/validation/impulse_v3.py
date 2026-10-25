"""Private review-only v3 correction of the impulse approximation question.

The v2 immutable source package is a required input. No original installed
package may be altered. Bounded tests never certify multilingual semantics.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.impulse_qualifier_repair import ACTIVITY_ID, SOURCE_SHA256
from app_generator.validation.impulse_semantics import (
    IDS, SELECTED, EXPECTED_V2_SHA256, physics_counterexamples,
)

ITEM_ID = "item-large-internal-forces"

V3_LABEL = {
    "en": (
        "During the brief collision, the net external impulse on the two-body "
        "system is negligible compared with the magnitude of the collision "
        "impulse on either body. This does not require each external force "
        "individually to be small."
    ),
    "ms": (
        "Semasa perlanggaran singkat, impuls luar bersih ke atas sistem dua "
        "jasad boleh diabaikan berbanding magnitud impuls perlanggaran pada "
        "mana-mana satu jasad. Ini tidak mensyaratkan setiap daya luar "
        "secara individu adalah kecil."
    ),
    "zh": (
        "\u5728\u77ed\u6682\u78b0\u649e\u671f\u95f4\uff0c\u4e24\u7269\u4f53\u7cfb\u7edf\u6240\u53d7\u7684\u51c0\u5916\u529b\u51b2\u91cf"
        "\u76f8\u5bf9\u4e8e\u4efb\u4e00\u7269\u4f53\u6240\u53d7\u7684\u78b0\u649e\u76f8\u4e92\u4f5c\u7528\u51b2\u91cf\u53ef\u5ffd\u7565\u3002"
        "\u8fd9\u5e76\u4e0d\u8981\u6c42\u6bcf\u4e00\u4e2a\u5916\u529b\u90fd\u5f88\u5c0f\u3002"
    ),
}

V3_ANSWER_LOGIC = {
    "en": (
        "Items 1, 2 and 3 are correct under the stated impulse approximation. "
        "Item 1 compares the small net external impulse over the impact "
        "interval with an individual collision interaction impulse; large "
        "external forces can cancel, so there is no requirement that each "
        "external force is small. Item 2 uses Newton's third-law cancellation "
        "of internal forces. Item 3 distinguishes approximately conserved "
        "momentum for negligible net external impulse from exactly conserved "
        "momentum when the net external impulse is zero, independently of "
        "collision type. Item 4 is false because kinetic-energy dissipation "
        "alone does not reduce total momentum. Item 5 is false because "
        "external forces need not vanish before and after the impact."
    ),
    "ms": (
        "Item 1, 2 dan 3 adalah betul di bawah penghampiran impuls yang "
        "dinyatakan. Item 1 membandingkan impuls luar bersih yang boleh "
        "diabaikan sepanjang hentaman dengan impuls perlanggaran yang dialami "
        "oleh satu jasad; daya luar yang besar boleh saling membatalkan, "
        "maka bukan setiap daya luar perlu kecil. Item 2 menggunakan "
        "pembatalan daya dalaman menurut hukum ketiga Newton. Item 3 "
        "membezakan keabadian momentum secara anggaran bagi impuls luar "
        "bersih yang boleh diabaikan daripada keabadian tepat apabila impuls "
        "luar bersih sifar, tanpa bergantung pada jenis perlanggaran. Item "
        "4 salah kerana pelesapan tenaga kinetik sahaja tidak mengurangkan "
        "jumlah momentum. Item 5 salah kerana daya luar tidak semestinya "
        "sifar sebelum dan selepas hentaman."
    ),
    "zh": (
        "\u5728\u6240\u8ff0\u51b2\u91cf\u8fd1\u4f3c\u4e0b\uff0c\u7b2c1\u30012\u548c3\u9879\u6b63\u786e\u3002"
        "\u7b2c1\u9879\u6bd4\u8f83\u78b0\u649e\u671f\u95f4\u53ef\u5ffd\u7565\u7684\u51c0\u5916\u529b\u51b2\u91cf"
        "\u4e0e\u5355\u4e2a\u7269\u4f53\u6240\u53d7\u7684\u78b0\u649e\u51b2\u91cf\uff1b"
        "\u5373\u4f7f\u4e2a\u522b\u5916\u529b\u5f88\u5927\uff0c\u4e5f\u53ef\u80fd\u76f8\u4e92\u62b5\u6d88\uff0c"
        "\u56e0\u6b64\u4e0d\u8981\u6c42\u6bcf\u4e2a\u5916\u529b\u90fd\u5f88\u5c0f\u3002"
        "\u7b2c2\u9879\u6839\u636e\u725b\u987f\u7b2c\u4e09\u5b9a\u5f8b\u8bf4\u660e\u5185\u529b\u76f8\u4e92\u62b5\u6d88\u3002"
        "\u7b2c3\u9879\u533a\u5206\u51c0\u5916\u529b\u51b2\u91cf\u53ef\u5ffd\u7565\u65f6\u7684\u52a8\u91cf\u8fd1\u4f3c\u5b88\u6052"
        "\u548c\u51c0\u5916\u529b\u51b2\u91cf\u4e3a\u96f6\u65f6\u7684\u52a8\u91cf\u7cbe\u786e\u5b88\u6052\uff0c"
        "\u4e0e\u78b0\u649e\u7c7b\u578b\u65e0\u5173\u3002"
        "\u7b2c4\u9879\u9519\u8bef\uff0c\u56e0\u4e3a\u52a8\u80fd\u8017\u6563\u672c\u8eab\u4e0d\u4f1a\u51cf\u5c11\u603b\u52a8\u91cf\u3002"
        "\u7b2c5\u9879\u9519\u8bef\uff0c\u56e0\u4e3a\u78b0\u649e\u524d\u540e\u7684\u5916\u529b\u4e0d\u5fc5\u59cb\u7ec8\u4e3a\u96f6\u3002"
    ),
}


def canonical_digest(package: dict[str, Any]) -> str:
    return sha256(json.dumps(package, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8")).hexdigest()


def review_candidate_v3(v2_file: Path, v2_receipt: Path,
                        source_pdf: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return new candidate and evidence; never write or approve anything."""
    v2_bytes = v2_file.read_bytes()
    v2_file_sha = sha256(v2_bytes).hexdigest()
    if v2_file_sha != EXPECTED_V2_SHA256:
        raise ValueError("v2 immutable package checksum mismatch")
    v2_review = json.loads(v2_receipt.read_text(encoding="utf-8"))
    if (v2_review.get("candidatePackageFileSha256") != v2_file_sha
        or v2_review.get("controlledSourceSha256") != SOURCE_SHA256
        or v2_review.get("reviewOnly") is not True
        or v2_review.get("publicationAuthorized") is not False):
        raise ValueError("v2 private receipt mismatched or approval flag unsafe")
    if sha256(source_pdf.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("controlled original PDF checksum mismatch")
    v2 = json.loads(v2_bytes.decode("utf-8"))
    activities = v2.get("activities")
    if not isinstance(activities, list) or len(activities) != 18:
        raise ValueError("expected 18-activity controlled pilot package")
    targets = [a for a in activities if a.get("id") == ACTIVITY_ID]
    if len(targets) != 1:
        raise ValueError("missing or duplicate target activity")
    previous = targets[0]
    interaction = previous.get("interaction")
    if (previous.get("type") != "interactive"
        or previous.get("interactionMode") != "selection"
        or not isinstance(interaction, dict)
        or interaction.get("correctSelections") != list(SELECTED)):
        raise ValueError("protected interaction answer structure differs")
    choices = interaction.get("items")
    if (not isinstance(choices, list) or len(choices) != len(IDS)
        or {x.get("id") for x in choices} != set(IDS)):
        raise ValueError("protected five choice identifiers differ")
    selected = [x for x in choices if x.get("id") == ITEM_ID]
    if len(selected) != 1 or selected[0].get("label") is None:
        raise ValueError("selected option missing or duplicated")
    if previous.get("answerLogic") is None:
        raise ValueError("missing protected answer explanation")
    # This real counterexample falsifies "any external force must be small":
    # +1000 and -1000 external forces yield exactly zero net external impulse.
    witness = physics_counterexamples()
    if (Fraction(witness["balancedExternalForceA"]) +
        Fraction(witness["balancedExternalForceB"]) != 0 or
        abs(Fraction(witness["balancedExternalForceA"])) <=
        abs(Fraction(witness["exampleInternalForce"]))):
        raise ValueError("independent balanced-external-forces witness fails")
    updated = deepcopy(v2)
    target = next(a for a in updated["activities"] if a["id"] == ACTIVITY_ID)
    item = next(x for x in target["interaction"]["items"] if x["id"] == ITEM_ID)
    item["label"] = deepcopy(V3_LABEL)
    target["answerLogic"] = deepcopy(V3_ANSWER_LOGIC)
    for old, new in zip(v2["activities"], updated["activities"]):
        if old.get("id") != new.get("id") or (old["id"] != ACTIVITY_ID and old != new):
            raise ValueError("unrelated learning activity modified")
    for field in ("objective", "visualPlan", "prompt", "feedback",
                  "explanation", "hints", "prerequisiteRecovery"):
        if target.get(field) != previous.get(field):
            raise ValueError("non-targeted protected activity field modified")
    if target["interaction"]["correctSelections"] != list(SELECTED):
        raise ValueError("answer key changed")
    if target["interaction"]["items"][1:] != previous["interaction"]["items"][1:]:
        raise ValueError("unrelated distractor or option modified")
    if canonical_digest(updated) == canonical_digest(v2):
        raise ValueError("no meaningful correction")
    return updated, {
        "version": "v3",
        "parentV2FileSha256": v2_file_sha,
        "parentV2CanonicalSha256": canonical_digest(v2),
        "candidateCanonicalSha256": canonical_digest(updated),
        "sourcePdfSha256": SOURCE_SHA256,
        "activityId": ACTIVITY_ID,
        "changedPaths": ["interaction.items[id=item-large-internal-forces].label",
                         "answerLogic"],
        "answerKeyUnchanged": True,
        "untouchedActivities": 17,
        "locales": ["en", "ms", "zh"],
        "physicsCounterexample": witness,
        "academicQA": "REVIEW_REQUIRED",
        "reviewOnly": True,
        "humanReviewed": False,
        "publicationAuthorized": False,
    }
