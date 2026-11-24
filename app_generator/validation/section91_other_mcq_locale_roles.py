"""BSA260: bounded source-bound per-choice multilingual polarity cues, all nine MCQs.

Historical rational formal models rechecked against original single textbook PDF.
Cues independently locate key proposition roles in each localized candidate;
NOT a full translation-equivalence, scientific, or visual acceptance.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app_generator.validation.section91_formal_physics import (
    _SOURCE_SHA,_CANDIDATE_SHA,_CASES,_mcq_cases,_source_axioms,
)
from app_generator.validation.source_passages import extract_pages

# Curated from the ACTUAL frozen candidate: option-specific direction/polarity
# anchors, not generic "momentum" words that could accidentally pass negations.
_CUES={
"act-mcq-02-si-units":{
 "en":("SI unit, dimensions","kg · m/s",{
   "opt-a":("ML/T","direction"),
   "opt-b":("magnitude alone","scalar"),
   "opt-c":("ML^2/T^2","energy"),
   "opt-d":("MT/L","perpendicular"),
 }),
 "ms":("unit SI, dimensi","kg · m/s",{
   "opt-a":("ML/T","arah"),
   "opt-b":("magnitud sahaja","skalar"),
   "opt-c":("ML^2/T^2","tenaga"),
   "opt-d":("MT/L","berserenjang"),
 }),
 "zh":("单位、量纲及方向","kg · m/s",{
   "opt-a":("ML/T","方向"),
   "opt-b":("仅凭大小","标量"),
   "opt-c":("ML^2/T^2","能量"),
   "opt-d":("MT/L","垂直"),
 }),
},
"act-mcq-03-net-force-definition":{
 "en":("nonzero net force","dp/dt",{
   "opt-a":("rate","increases"),
   "opt-b":("momentum itself","remains constant"),
   "opt-c":("mass only","no effect"),
   "opt-d":("must be zero","already possesses"),
 }),
 "ms":("daya padu bukan sifar","dp/dt",{
   "opt-a":("kadar perubahan","meningkat"),
   "opt-b":("momentum linear kuar itu sendiri","kekal malar"),
   "opt-c":("jisim terhadap masa sahaja","tanpa memberi kesan"),
   "opt-d":("mestilah sifar","sudah memiliki"),
 }),
 "zh":("恒定非零合外力","dp/dt",{
   "opt-a":("变化率","持续增加"),
   "opt-b":("本身的线动量","保持不变"),
   "opt-c":("仅等于质量","没有任何影响"),
   "opt-d":("就必须为零","已经具有"),
 }),
},
"act-mcq-04-two-particle-opposite-momentum":{
 "en":("same constant speed","zero total linear momentum",{
   "opt-a":("momentum is zero","energy is positive"),
   "opt-b":("both","positive and non-zero"),
   "opt-c":("both","are zero"),
   "opt-d":("momentum is positive","energy is zero"),
 }),
 "ms":("laju malar yang sama","momentum linear sifar",{
   "opt-a":("momentum linear adalah sifar","tenaga kinetik adalah positif"),
   "opt-b":("kedua-dua","positif dan bukan sifar"),
   "opt-c":("kedua-dua","adalah sifar"),
   "opt-d":("momentum linear adalah positif","tenaga kinetik adalah sifar"),
 }),
 "zh":("相同的恒定速率","总线动量也可能为零",{
   "opt-a":("总线动量为零","总动能为正"),
   "opt-b":("总线动量和总动能","均为正"),
   "opt-c":("总线动量和总动能","均为零"),
   "opt-d":("总线动量为正","总动能为零"),
 }),
},
"act-mcq-05-third-law-connection":{
 "en":("isolated system","third law",{
   "opt-a":("equal and opposite","sum of the time rates"),
   "opt-b":("each individual particle","strictly constant"),
   "opt-c":("acceleration of each","zero"),
   "opt-d":("same mass and velocity","guarantees"),
 }),
 "ms":("sistem terpencil","hukum ketiga",{
   "opt-a":("sama magnitud","bertentangan arah"),
   "opt-b":("setiap zarah individu","kekal malar"),
   "opt-c":("Pecutan setiap zarah","sifar"),
   "opt-d":("jisim dan halaju yang sama","menjamin"),
 }),
 "zh":("孤立系统","牛顿第三",{
   "opt-a":("大小相等","方向相反"),
   "opt-b":("每个粒子的线动量","严格保持恒定"),
   "opt-c":("每个粒子的加速度","都为零"),
   "opt-d":("质量和速度","必须完全相同"),
 }),
},
"act-mcq-06-equal-speed-comparison":{
 "en":("due North","vector",{
   "opt-a":("greater magnitude","perpendicular directions"),
   "opt-b":("scalar magnitude","direction is irrelevant"),
   "opt-c":("identical linear momenta","depends only on speed"),
   "opt-d":("car has a greater","less mass"),
 }),
 "ms":("Utara","vektor",{
   "opt-a":("lebih besar","arah serenjang"),
   "opt-b":("magnitud skalar","arah perjalanan tidak relevan"),
   "opt-c":("serupa","hanya bergantung pada laju"),
   "opt-d":("Kereta mempunyai","jisim yang lebih kecil"),
 }),
 "zh":("正向北","矢量",{
   "opt-a":("更大的线动量大小","正交垂直"),
   "opt-b":("标量大小","行驶方向与动量无关"),
   "opt-c":("完全相同的线动量","仅取决于速率"),
   "opt-d":("轿车具有更大的","质量较小"),
 }),
},
"act-mcq-07-equal-ke-momentum-relation":{
 "en":("identical kinetic energies","same kinetic energy",{
   "opt-transport-greater":("cargo transport","greater momentum magnitude"),
   "opt-equal-momentum":("identical momentum","equal kinetic energies"),
   "opt-scout-greater":("scout rover","greater momentum magnitude"),
   "opt-cannot-determine":("cannot be determined","actual speed"),
 }),
 "ms":("tenaga kinetik yang serupa","tenaga kinetik",{
   "opt-transport-greater":("pengangkut kargo","lebih besar"),
   "opt-equal-momentum":("magnitud momentum yang sama","tenaga kinetik yang serupa"),
   "opt-scout-greater":("perayau peninjau","lebih besar"),
   "opt-cannot-determine":("tidak dapat ditentukan","laju sebenar"),
 }),
 "zh":("动能完全相同","动能相等",{
   "opt-transport-greater":("货物运输车","大小大于"),
   "opt-equal-momentum":("动量大小完全相同","动能相等"),
   "opt-scout-greater":("侦察巡逻车","动量大小更大"),
   "opt-cannot-determine":("无法确定","实际速率"),
 }),
},
"act-mcq-08-isolated-subsystem-fallacy":{
 "en":("Nadia","Newton's third law",{
   "opt-nadia-momentum-changes":("momentum changes","rate of change"),
   "opt-single-particle-conserved":("remains zero","overall"),
   "opt-force-equals-momentum":("directly equal","rather than its time rate"),
   "opt-forces-cancel-on-body":("cannot change","cancel out entirely"),
 }),
 "ms":("Nadia","hukum ketiga",{
   "opt-nadia-momentum-changes":("Momentum Nadia berubah","kadar perubahan"),
   "opt-single-particle-conserved":("kekal sifar","keseluruhan sistem"),
   "opt-force-equals-momentum":("sama secara langsung","bukannya kadar perubahan"),
   "opt-forces-cancel-on-body":("tidak boleh berubah","membatalkan sepenuhnya"),
 }),
 "zh":("纳迪娅","牛顿第三",{
   "opt-nadia-momentum-changes":("动量发生改变","变化率"),
   "opt-single-particle-conserved":("始终保持为零","整体系统"),
   "opt-force-equals-momentum":("直接等于","而不是动量"),
   "opt-forces-cancel-on-body":("不可能改变","完全抵消"),
 }),
},
"act-mcq-09-no-momentum-conversion":{
 "en":("spring buffer","potential",{
   "opt-ke-transforms-momentum-transfers":("elastic potential energy","transferred"),
   "opt-potential-momentum-stored":("potential momentum","stored"),
   "opt-both-turn-to-heat":("both","thermal energy"),
   "opt-momentum-conserved-internally":("pod alone","completely destroyed"),
 }),
 "ms":("spring","tenaga keupayaan",{
   "opt-ke-transforms-momentum-transfers":("tenaga keupayaan kenyal","dipindahkan"),
   "opt-potential-momentum-stored":("momentum keupayaan kenyal","tersimpan"),
   "opt-both-turn-to-heat":("kedua-dua","tenaga terma dalaman"),
   "opt-momentum-conserved-internally":("pod itu sendiri","musnah sepenuhnya"),
 }),
 "zh":("弹簧缓冲器","势能",{
   "opt-ke-transforms-momentum-transfers":("弹性势能","转移"),
   "opt-potential-momentum-stored":("弹性势动量","储存"),
   "opt-both-turn-to-heat":("动能和线动量","热能"),
   "opt-momentum-conserved-internally":("内部守恒","完全消失"),
 }),
},
}


def bound_all_other_mcq_locale_option_roles(
    *,source_pdf:Path,package_file:Path,
)->dict[str,Any]:
    if (source_pdf.is_symlink() or not source_pdf.is_file()
            or sha256(source_pdf.read_bytes()).hexdigest()!=_SOURCE_SHA
            or package_file.is_symlink() or not package_file.is_file()
            or sha256(package_file.read_bytes()).hexdigest()!=_CANDIDATE_SHA):
        raise ValueError("BSA260_EXACT_SELECTED_SERWAY_OR_CANDIDATE_DRIFT")
    axioms=_source_axioms(source_pdf,_SOURCE_SHA)
    if len(extract_pages(source_pdf))!=3 or len(axioms)!=9:
        raise ValueError("BSA260_SELECTED_SINGLE_TEXTBOOK_PHYSICS_MISSING")
    pkg=json.loads(package_file.read_text(encoding="utf8"))
    activities=pkg.get("activities")
    if not isinstance(activities,list) or len(activities)!=18:
        raise ValueError("BSA260_EXPECTED_SOURCE_ACTIVITY_ROSTER_CHANGED")
    formal=_mcq_cases()
    if (len(formal)!=9 or set(formal)!={x["id"] for x in activities[:9]}
            or set(_CUES)!={x["id"] for x in activities[1:9]}):
        raise ValueError("BSA260_SOURCE_PROOF_SCOPE_CHANGED")
    result=[]
    for activity in activities[1:9]:
        ident=activity["id"]
        key=activity["answerKey"]["correct"]
        opts=activity["answerKey"]["options"]
        labels={o["id"]:o["label"] for o in opts}
        truth=formal[ident]
        if (len(labels)!=4 or set(labels)!=set(truth) or
                set(labels)!={o["id"] for o in opts} or
                truth.get(key) is not True or
                sum(v is True for v in truth.values())!=1 or
                sum(v is False for v in truth.values())!=3):
            raise ValueError("BSA260_WRONG_FORMAL_ANSWER_OR_FALSE_CHOICE_"+ident)
        localized=[]
        for locale in ("en","ms","zh"):
            promptcue,explaincue,opcue=_CUES[ident][locale]
            if (set(opcue)!=set(labels) or
                    not isinstance(activity.get("prompt",{}).get(locale),str) or
                    promptcue.casefold() not in activity["prompt"][locale].casefold() or
                    not isinstance(activity.get("explanation",{}).get(locale),str) or
                    explaincue.casefold() not in activity["explanation"][locale].casefold()):
                raise ValueError("BSA260_SOURCE_LOCALE_PROMPT_OR_REASONING_CUE_MISSING_"+
                                 ident+"_"+locale)
            roles=[]
            for oid,tokens in opcue.items():
                text=labels[oid].get(locale)
                if (not isinstance(text,str) or
                        not all(cue.casefold() in text.casefold() for cue in tokens)):
                    raise ValueError("BSA260_OPTION_DIRECTION_OR_POLARITY_CUE_MISSING_"+
                                     ident+"_"+locale+"_"+oid)
                roles.append({"option":oid,"textSha256":sha256(text.encode("utf8")).hexdigest(),
                              "cueCount":len(tokens),"modelTruth":truth[oid]})
            localized.append({"locale":locale,"answerOptionRoles":roles,
                              "promptSha256":sha256(activity["prompt"][locale].encode("utf8")).hexdigest(),
                              "explanationSha256":sha256(activity["explanation"][locale].encode("utf8")).hexdigest()})
        result.append({"activityId":ident,"correctAnswerModel":key,
                       "falseOptionsModelled":sorted(o for o,v in truth.items() if not v),
                       "localeWitnesses":localized})
    return {
        "status":"BSA260_OTHER_EIGHT_SOURCE_BOUND_MCQ_LOCALIZED_CUE_WITNESSES",
        "sourceSha256":_SOURCE_SHA,
        "candidateSha256":_CANDIDATE_SHA,
        "actualOriginalSourceAxiomsRechecked":9,
        "otherMcqActivitiesChecked":8,
        "otherMcqLocalizedOptionRolesChecked":96,
        "otherMcqPromptExplanationRoleChecks":48,
        "otherMcqFormalTrueChoiceWitnesses":8,
        "otherMcqFormalFalseChoiceCounterexamples":24,
        "sourceBoundActivityWitnesses":result,
        "fullTrilingualMeaningEquivalenceProven":False,
        "fullNaturalLanguageScientificTruthCertified":False,
        "fullAcademicPASS":0,"newProviderCalls":0,
        "publicationAuthorized":False,
    }
