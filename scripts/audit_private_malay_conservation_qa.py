"""Metadata-only original-PDF-bound v8->v9 Malay science QA regression."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster
from app_generator.validation.malay_conservation_lexicon import (
    V8_SHA,PDF_SHA,repair_private_malay_v9,conservation_lexicon_flags,
)
from app_generator.validation.mcq_statement_physics import APPROVED_MALAY_LEXICON_V9_SHA
from app_generator.validation.language_qa import check_multilingual_surface

def audit(before,after,pdf,pre_packets,post_packets):
    x=verify_full_source_packet_roster(package_file=before,source_pdf=pdf,
                                      packets_file=pre_packets,expected_count=18)
    y=verify_full_source_packet_roster(package_file=after,source_pdf=pdf,
                                      packets_file=post_packets,expected_count=18)
    if (x["packageSha256"]!=V8_SHA or
        y["packageSha256"]!=APPROVED_MALAY_LEXICON_V9_SHA or
        x["sourceSha256"]!=y["sourceSha256"] or y["sourceSha256"]!=PDF_SHA):
        raise ValueError("original source and versioned package hashes changed")
    old=json.loads(before.read_text("utf-8"))
    new=json.loads(after.read_text("utf-8"))
    reconstructed,repaired=repair_private_malay_v9(old)
    if reconstructed!=new:
        raise ValueError("v9 modifies fields outside approved lexicon repair")
    count=lambda data:sum(check_multilingual_surface(a).result=="FAIL"
                          for a in data["activities"])
    if (len(conservation_lexicon_flags(old))!=101 or
        conservation_lexicon_flags(new) or
        count(old)!=18 or count(new)!=0):
        raise ValueError("automatic language QA did not capture all problems")
    if x["publicationAuthorized"] or y["publicationAuthorized"]:
        raise ValueError("publication gate changed")
    return {
       "status":"SOURCE_BOUND_MALAY_CONSERVATION_GENERATOR_QA",
       "originalPdfSha256":PDF_SHA,
       "sourceActivitiesReverifiedPerCandidate":18,
       "oldV8Sha256":V8_SHA,
       "correctedV9Sha256":APPROVED_MALAY_LEXICON_V9_SHA,
       "previousMistranslatedFields":101,
       "previousMistranslatedOccurrences":146,
       "previousFailedLanguageGates":18,
       "correctedMistranslatedFields":0,
       "correctedFailedLanguageGates":0,
       "otherChangesBeyondPermittedLexicon":False,
       "fullTranslationSemanticsProven":False,
       "formalAcademicPASS":0,"academicQA":"REVIEW_REQUIRED",
       "publicationAuthorized":False,
    }

def main():
    p=argparse.ArgumentParser()
    for k in ("before","after","pdf","before-packets","after-packets","out"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    dest=a.out.resolve()
    if dest.exists() or dest.is_relative_to(ROOT):
        raise ValueError("new private audit outside Git required")
    result=audit(a.before,a.after,a.pdf,a.before_packets,a.after_packets)
    with dest.open("x",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=True,indent=2)
        f.write("\n")
    print(json.dumps(result))
if __name__=="__main__":main()
