"""Review-only, original-source-bound repair for a Section 9.4 impulse qualifier.

This intentionally does not install, publish, merge, or grant academic PASS.
Revising question wording invalidates the previous frozen semantic QA fingerprint.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from app_generator.validation.interactive_physics import EXPECTED_TEXT_SHA256, semantic_digest

SOURCE_SHA256 = "08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578"
INSTALLED_CANONICAL_SHA256 = "2ffe799784c5492b5b8cf2062f7ffaa40264e3933820349b506c39fb651a01f7"
ACTIVITY_ID = "int-select-isolated-conditions"
SELECTED_ITEM = "item-momentum-conserved-regardless-type"
EXPECTED_ANSWERS = (
    "item-large-internal-forces",
    "item-action-reaction-internal",
    SELECTED_ITEM,
)

REVISION = {
    "prompt": {
        "en": "During a brief one-dimensional collision under the impulse approximation, which statements about the forces and total momentum of the two-body system are correct? Distinguish negligible external impulse (approximate momentum conservation) from exactly zero net external impulse (exact conservation). Select all that apply.",
        "ms": "Semasa perlanggaran satu dimensi yang singkat di bawah penghampiran impuls, pernyataan manakah tentang daya dan jumlah momentum sistem dua jasad yang betul? Bezakan impuls luar yang boleh diabaikan (keabadian momentum secara anggaran) daripada impuls luar bersih yang tepat sifar (keabadian tepat). Pilih semua yang berkenaan.",
        "zh": '在冲量近似下的短暂一维碰撞中，关于双物体系统所受的力和总动量，哪些陈述正确？请区分净外力冲量可忽略时的动量近似守恒，以及净外力冲量严格为零时的动量精确守恒。请选择所有适用项。',
    },
    "feedback": {
        "en": "The collision forces are internal action-reaction pairs, so they cancel in the system's net force. The total momentum change is exactly the net external impulse, Δp = J_ext. When that impulse is negligible during a brief impact, momentum is approximately conserved; it is exactly conserved only when the net external impulse is zero. This distinction applies to elastic, inelastic, and perfectly inelastic collisions, regardless of the kinetic-energy loss.",
        "ms": "Daya perlanggaran ialah pasangan tindakan-tindak balas dalaman, maka sumbangannya kepada daya bersih sistem saling membatalkan. Perubahan jumlah momentum adalah tepat sama dengan impuls luar bersih, Δp = J_ext. Jika impuls itu boleh diabaikan semasa hentaman singkat, momentum diabadikan secara anggaran; keabadian tepat hanya berlaku apabila impuls luar bersih sifar. Perbezaan ini terpakai bagi perlanggaran kenyal, tak kenyal dan tak kenyal sempurna, tanpa mengira kehilangan tenaga kinetik.",
        "zh": '碰撞力是系统内部的作用力与反作用力，其对系统合力的贡献相互抵消。总动量的变化严格等于净外力冲量，即 Δp = J_ext。若短暂碰撞期间的净外力冲量可忽略，则动量近似守恒；只有当净外力冲量严格为零时，动量才精确守恒。无论弹性、非弹性或完全非弹性碰撞，也无论动能损失多少，都必须区分这两种情况。',
    },
    "answerLogic": {
        "en": "Items 1, 2 and 3 are correct in the stated approximation: internal collision forces dominate the external impulse, Newton's third-law pairs cancel internally, and the momentum-conservation rule does not depend on collision type. Item 3 distinguishes approximate conservation for negligible net external impulse from exact conservation if that impulse is zero. Item 4 is false because kinetic-energy dissipation alone does not change total momentum. Item 5 is false because external forces need not vanish at all times before or after impact; only the net external impulse over the impact interval determines its momentum change.",
        "ms": "Item 1, 2 dan 3 adalah betul dalam penghampiran yang dinyatakan: daya perlanggaran dalaman mendominasi impuls luar, pasangan daya hukum ketiga Newton saling membatalkan secara dalaman, dan prinsip keabadian momentum tidak bergantung pada jenis perlanggaran. Item 3 membezakan keabadian secara anggaran apabila impuls luar bersih boleh diabaikan dengan keabadian tepat apabila impuls itu sifar. Item 4 salah kerana pelesapan tenaga kinetik sahaja tidak mengubah jumlah momentum. Item 5 salah kerana daya luar tidak semestinya sifar pada setiap masa sebelum atau selepas hentaman; perubahan momentum ditentukan oleh impuls luar bersih sepanjang selang hentaman.",
        "zh": '在给定近似条件下，第1、2和3项正确：碰撞内力的冲量远大于外力冲量，牛顿第三定律的内力对相互抵消，而动量守恒的条件不取决于碰撞类型。第3项区分净外力冲量可忽略时的近似守恒与净外力冲量为零时的精确守恒。第4项错误，因为动能耗散本身不会使系统总动量改变。第5项错误，因为外力不必在碰撞前后的所有时刻都为零；碰撞期间的净外力冲量才决定动量的变化。',
    },
    "explanation": {
        "en": "For the two-body system, Newton's third-law interaction forces cancel, so Δp_total = ∫F_ext,net dt = J_ext across the impact interval. The impulse approximation treats the external impulse as small compared with the internal collision impulse: Δp_total is then approximately zero, not necessarily exactly zero. Exact momentum conservation requires J_ext = 0 over that interval. This rule is independent of whether the collision conserves kinetic energy; deformation can dissipate kinetic energy without violating the system's momentum balance.",
        "ms": "Bagi sistem dua jasad, daya interaksi yang mematuhi hukum ketiga Newton saling membatalkan, maka Δp_total = ∫F_ext,net dt = J_ext sepanjang selang hentaman. Penghampiran impuls menganggap impuls luar kecil berbanding impuls perlanggaran dalaman: oleh itu Δp_total hampir sifar, tetapi tidak semestinya tepat sifar. Keabadian momentum yang tepat memerlukan J_ext = 0 sepanjang selang tersebut. Prinsip ini tidak bergantung pada sama ada tenaga kinetik diabadikan; ubah bentuk boleh melesapkan tenaga kinetik tanpa melanggar imbangan momentum sistem.",
        "zh": '对双物体系统而言，遵守牛顿第三定律的相互作用内力相互抵消，因此在碰撞时间间隔内，Δp_total = ∫F_ext,net dt = J_ext。冲量近似认为外力冲量相对于碰撞内力冲量很小，所以 Δp_total 近似为零，但未必严格等于零。精确的动量守恒要求该时间间隔内 J_ext = 0。这与碰撞是否保持动能无关；形变可以耗散动能，而系统仍须遵守动量变化等于净外力冲量的关系。',
    },
    "selectedItem": {
        "en": "For any collision type (elastic, inelastic or perfectly inelastic), total momentum is approximately conserved when net external impulse is negligible, and is exactly conserved when net external impulse over the collision is zero.",
        "ms": "Bagi sebarang jenis perlanggaran (kenyal, tak kenyal atau tak kenyal sempurna), jumlah momentum diabadikan secara anggaran apabila impuls luar bersih boleh diabaikan, dan diabadikan dengan tepat apabila impuls luar bersih sepanjang perlanggaran adalah sifar.",
        "zh": '对于任何碰撞类型（弹性、非弹性或完全非弹性），如果净外力冲量可忽略，则总动量近似守恒；如果碰撞期间净外力冲量严格为零，则总动量精确守恒。',
    },
    "secondHint": {
        "en": "Newton's third law cancels internal forces, but the system's change in momentum equals the net external impulse. Ask whether that impulse is negligible (approximate conservation) or exactly zero (exact conservation).",
        "ms": "Hukum ketiga Newton menyebabkan daya dalaman saling membatalkan, tetapi perubahan momentum sistem sama dengan impuls luar bersih. Tentukan sama ada impuls itu boleh diabaikan (keabadian secara anggaran) atau tepat sifar (keabadian tepat).",
        "zh": '牛顿第三定律使内力相互抵消，但系统动量变化仍等于净外力冲量。请判断该冲量只是可忽略（动量近似守恒），还是严格为零（动量精确守恒）。',
    },
    "prerequisite": {
        "en": "Review the momentum-impulse theorem: Δp_total = J_ext. A negligible external impulse gives approximately conserved total momentum; exact conservation requires zero net external impulse during the interval.",
        "ms": "Ulang kaji teorem momentum-impuls: Δp_total = J_ext. Impuls luar bersih yang boleh diabaikan memberikan keabadian momentum secara anggaran; keabadian tepat memerlukan impuls luar bersih sifar sepanjang selang masa itu.",
        "zh": '复习动量—冲量定理：Δp_total = J_ext。净外力冲量可忽略时，总动量近似守恒；只有当该时间间隔内净外力冲量为零时，总动量才精确守恒。',
    },
}


def canonical_hash(data: dict) -> str:
    return sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,
                             separators=(",",":")).encode("utf-8")).hexdigest()


def check_physics_rule() -> None:
    """Exact nonzero external impulse is a counterexample to blanket 'strictly'."""
    momentum_initial=Fraction(2)
    external_impulse=Fraction(1,100000)
    final_momentum=momentum_initial+external_impulse
    if final_momentum-momentum_initial!=external_impulse or final_momentum==momentum_initial:
        raise ValueError("nonzero net external impulse must change system momentum")
    if momentum_initial+Fraction(0)!=momentum_initial:
        raise ValueError("zero net external impulse must conserve system momentum")


def build_review_candidate(
    original: dict, source_pdf: Path, source_sha256: str=SOURCE_SHA256,
    *, original_package_hash: str=INSTALLED_CANONICAL_SHA256,
    original_semantic_sha: str | None=None,
) -> tuple[dict,dict]:
    if sha256(source_pdf.read_bytes()).hexdigest()!=source_sha256 or source_sha256!=SOURCE_SHA256:
        raise ValueError("source PDF does not match controlled Section 9.4 edition")
    if canonical_hash(original)!=original_package_hash:
        raise ValueError("installed candidate input differs from protected baseline")
    activities=original.get("activities",[])
    matches=[a for a in activities if a.get("id")==ACTIVITY_ID]
    if len(matches)!=1 or matches[0].get("type")!="interactive":
        raise ValueError("expected unique installed impulse selection activity")
    old=matches[0]
    semantic=original_semantic_sha or EXPECTED_TEXT_SHA256[ACTIVITY_ID]
    if semantic_digest(old)!=semantic:
        raise ValueError("protected original localized question differs from reviewed baseline")
    if old.get("interactionMode")!="selection":
        raise ValueError("impulse repair applies to selection mode only")
    ix=old["interaction"]
    if tuple(ix.get("correctSelections",[]))!=EXPECTED_ANSWERS:
        raise ValueError("original selection answer structure changed")
    items=[x for x in ix.get("items",[]) if x.get("id")==SELECTED_ITEM]
    if len(items)!=1 or len(old.get("hints",[]))<2:
        raise ValueError("missing expected targeted item or second hint")
    check_physics_rule()
    candidate=deepcopy(original)
    changed=next(a for a in candidate["activities"] if a["id"]==ACTIVITY_ID)
    for field in ("prompt","feedback","answerLogic","explanation"):
        changed[field]=deepcopy(REVISION[field])
    changed["hints"][1]=deepcopy(REVISION["secondHint"])
    changed["prerequisiteRecovery"]["prompt"]=deepcopy(REVISION["prerequisite"])
    next(x for x in changed["interaction"]["items"] if x["id"]==SELECTED_ITEM)["label"]=deepcopy(REVISION["selectedItem"])
    if changed["interaction"]["correctSelections"]!=list(EXPECTED_ANSWERS):
        raise ValueError("candidate changed correct answer key")
    if semantic_digest(changed)==semantic_digest(old):
        raise ValueError("repaired text did not change academic semantic fingerprint")
    return candidate,{
        "activityId":ACTIVITY_ID,
        "originalPackageCanonicalSha256":canonical_hash(original),
        "candidatePackageCanonicalSha256":canonical_hash(candidate),
        "originalNarrativeSha256":semantic,
        "candidateNarrativeSha256":semantic_digest(changed),
        "controlledSourceSha256":source_sha256,
        "changedFields":[
            "prompt","feedback","answerLogic","explanation",
            "hints[1]","prerequisiteRecovery.prompt",
            "interaction.items[id=item-momentum-conserved-regardless-type].label",
        ],
        "answerKeyUnchanged":True,
        "locales":["en","ms","zh"],
        "reviewOnly":True,
        "academicQA":"REVIEW_REQUIRED",
        "humanReviewed":False,
        "publicationAuthorized":False,
    }
