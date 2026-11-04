"""Source-bound before/after Malay science-term gate: metadata-only receipt."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster
from app_generator.validation.language_qa import (
    check_multilingual_surface,scientific_malay_eternal_terms,
)


def audit(before_pkg:Path,after_pkg:Path,pdf:Path,
          before_packets:Path,after_packets:Path)->dict:
    first=verify_full_source_packet_roster(
        package_file=before_pkg,source_pdf=pdf,
        packets_file=before_packets,expected_count=18)
    second=verify_full_source_packet_roster(
        package_file=after_pkg,source_pdf=pdf,
        packets_file=after_packets,expected_count=18)
    a=json.loads(before_pkg.read_text("utf-8"))
    b=json.loads(after_pkg.read_text("utf-8"))
    former=scientific_malay_eternal_terms(a)
    newer=scientific_malay_eternal_terms(b)
    original_failed=sum(check_multilingual_surface(x).result=="FAIL"
                        for x in a["activities"])
    updated_failed=sum(check_multilingual_surface(x).result=="FAIL"
                       for x in b["activities"])
    if (len(former)!=17 or newer or original_failed!=6 or updated_failed or
            first["sourceSha256"]!=second["sourceSha256"] or
            first["packageSha256"]==second["packageSha256"] or
            first["publicationAuthorized"] is not False or
            second["publicationAuthorized"] is not False):
        raise ValueError("original scientific mistranslation detector regression failed")
    return {
      "status":"SOURCE_BOUND_MALAY_SCIENCE_GENERATION_QA_REGRESSION",
      "originalPdfSha256":first["sourceSha256"],
      "originalV5Sha256":first["packageSha256"],
      "correctedV6Sha256":second["packageSha256"],
      "originalSourceActivitiesReverifiedInEachCandidate":18,
      "oldSuspectScientificLocalizedFields":len(former),
      "oldFailedActivityMultilingualGates":original_failed,
      "newSuspectScientificLocalizedFields":len(newer),
      "newFailedActivityMultilingualGates":updated_failed,
      "newTranslationSemanticsFullyApproved":False,
      "academicQA":"REVIEW_REQUIRED",
      "formalAcademicPASS":0,"publicationAuthorized":False,
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("before","after","pdf","before-packets","after-packets","out"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    try:
        dest=a.out.resolve()
        if dest.exists() or dest.is_relative_to(ROOT) or not dest.parent.is_dir():
            raise ValueError("private immutable receipt destination required")
        report=audit(a.before,a.after,a.pdf,a.before_packets,a.after_packets)
        with dest.open("x",encoding="utf-8") as f:
            json.dump(report,f,indent=2,sort_keys=True)
            f.write("\n")
        print(json.dumps(report,sort_keys=True))
        return 0
    except (ValueError,TypeError,KeyError,OSError) as exc:
        print(json.dumps({"status":"MALAY_SCIENCE_GENERATION_QA_BLOCKED",
                          "errorType":type(exc).__name__,
                          "publicationAuthorized":False}))
        return 2
if __name__=="__main__":
    raise SystemExit(main())
