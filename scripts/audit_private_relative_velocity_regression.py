"""Private v7/v8 source-bound relative-speed academic QA comparison."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.full_source_packet_roster import verify_full_source_packet_roster
from app_generator.validation.relative_velocity_derivation import incorrect_derivation_premise_defects,ACTIVITY,V7_SHA,PDF_SHA
def main():
 p=argparse.ArgumentParser()
 for k in ("before","after","pdf","before-packets","after-packets","out"):
  p.add_argument("--"+k,required=True,type=Path)
 a=p.parse_args()
 x=verify_full_source_packet_roster(package_file=a.before,source_pdf=a.pdf,packets_file=a.before_packets,expected_count=18)
 y=verify_full_source_packet_roster(package_file=a.after,source_pdf=a.pdf,packets_file=a.after_packets,expected_count=18)
 if x["packageSha256"]!=V7_SHA or x["sourceSha256"]!=y["sourceSha256"] or y["sourceSha256"]!=PDF_SHA:
  raise ValueError("source hash drift")
 old=json.loads(a.before.read_text("utf-8"))
 new=json.loads(a.after.read_text("utf-8"))
 assert len(old["activities"])==len(new["activities"])==18
 diffs=[]
 for aa,bb in zip(old["activities"],new["activities"]):
  assert aa["id"]==bb["id"]
  if aa==bb:continue
  assert aa["id"]==ACTIVITY
  ca,cb=aa.copy(),bb.copy()
  va,vb=ca.pop("answerLogic"),cb.pop("answerLogic")
  assert ca==cb and set(va)==set(vb)=={"en","ms","zh"}
  diffs.append(aa["id"])
 assert diffs==[ACTIVITY]
 original=incorrect_derivation_premise_defects(next(x for x in old["activities"] if x["id"]==ACTIVITY))
 corrected=incorrect_derivation_premise_defects(next(x for x in new["activities"] if x["id"]==ACTIVITY))
 assert len(original)==3 and corrected==[]
 result={"status":"SOURCE_BOUND_RELATIVE_DERIVATION_QA_REPAIRED",
    "sourceSha256":PDF_SHA,"oldV7Sha256":x["packageSha256"],
    "newV8Sha256":y["packageSha256"],"sourceActivitiesReverifiedEach":18,
    "originalTrilingualDefectFlags":3,"correctedDefectFlags":0,
    "otherActivitiesModified":0,"answersChanged":False,
    "academicQA":"REVIEW_REQUIRED","formalAcademicPASS":0,"publicationAuthorized":False}
 if a.out.exists() or a.out.resolve().is_relative_to(ROOT):
  raise ValueError("new private report destination required")
 with a.out.open("x",encoding="utf-8") as f:json.dump(result,f,indent=2)
 print(json.dumps(result))
if __name__=="__main__":main()
