import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_generator.validation.interactive_physics import (
    SUPPORTED, assignments, actual_answer, audit_interaction_models,
    EXPECTED_TEXT_SHA256, semantic_digest,
)

ROOT=Path(__file__).resolve().parents[1]


class InteractivePhysicsModelsTests(unittest.TestCase):
    def setUp(self):
        # Synthetic source-free fixtures. The repository's checked-in
        # package is intentionally NOT the separately installed pilot,
        # and must never be substituted as real-generation evidence.
        examples=[]
        for id_,model in SUPPORTED.items():
            mode,key,_,_=assignments(model)
            if mode in ("classification","matching"):
                item_ids=list(key)
                targets=set(key.values())
                interaction={
                    "items":[{"id":i} for i in item_ids],
                    "targets":[{"id":t} for t in sorted(targets)],
                    "placements":[{"itemId":i,"targetId":t} for i,t in key.items()],
                }
            else:
                items=list(key)
                if mode=="selection":
                    options={
                        "equal_mass_outcomes":["opt-elastic-exchange","opt-inelastic-stick",
                                               "opt-inelastic-exchange","opt-kinetic-always-conserved"],
                        "impulse_conditions":["item-large-internal-forces",
                                              "item-action-reaction-internal",
                                              "item-momentum-conserved-regardless-type",
                                              "item-deformation-decreases-momentum",
                                              "item-requires-zero-external-forces-ever"],
                    }
                    items=options[model]
                interaction={"items":[{"id":i} for i in items]}
                if mode=="selection":
                    interaction["correctSelections"]=list(key)
                else:
                    interaction["correctOrder"]=list(key)
            examples.append({"id":id_,"type":"interactive",
                             "interactionMode":mode,"interaction":interaction})
        self.real_package={"activities":examples}
        self.interactive={a["id"]:a for a in examples}

    def test_independent_models_cover_exactly_all_nine_original_interactions(self):
        self.assertEqual(set(SUPPORTED),set(self.interactive))
        verified=0
        flagged=0
        for id_,model in SUPPORTED.items():
            with self.subTest(id=id_):
                mode,key,notes,proof=assignments(model)
                actual_mode,actual_key=actual_answer(self.interactive[id_])
                self.assertEqual(mode,actual_mode)
                if mode=="selection":
                    self.assertEqual(set(key),set(actual_key))
                else:
                    self.assertEqual(key,actual_key)
                self.assertTrue(proof)
                if notes:
                    flagged+=1
                    self.assertEqual("int-select-isolated-conditions",id_)
                    self.assertIn("strictly conserved",notes[0])
                else:
                    verified+=1
        self.assertEqual((verified,flagged),(8,1))

    def test_corrupted_order_key_or_classification_is_rejected(self):
        # A structurally valid but physically wrong mapping is caught by
        # independent model comparison and cannot become a QA PASS.
        for id_ in ("int-order-post-collision-speeds",
                    "int-classify-collision-regimes",
                    "int-select-valid-equal-mass-outcomes",
                    "int-match-extreme-mass-limits"):
            with self.subTest(id=id_):
                altered=copy.deepcopy(self.interactive[id_])
                x=altered["interaction"]
                if "correctOrder" in x:
                    x["correctOrder"]=list(reversed(x["correctOrder"]))
                elif "correctSelections" in x:
                    x["correctSelections"]=x["correctSelections"][1:]
                else:
                    x["placements"][0]["targetId"]=x["placements"][1]["targetId"]
                _,reference,_,_=assignments(SUPPORTED[id_])
                _,observed=actual_answer(altered)
                self.assertNotEqual(set(reference) if isinstance(reference,list) and
                                    altered["interactionMode"]=="selection" else reference,
                                    set(observed) if altered["interactionMode"]=="selection" else observed)

    def test_missing_duplicate_or_wrong_item_keys_are_invalid(self):
        x=copy.deepcopy(self.interactive["int-order-ballistic-pendulum-sequence"])
        x["interaction"]["correctOrder"]=["unknown"]*4
        with self.assertRaisesRegex(ValueError,"invalid ordering"):
            actual_answer(x)
        x=copy.deepcopy(self.interactive["int-select-valid-equal-mass-outcomes"])
        x["interaction"]["correctSelections"]=["opt-elastic-exchange"]*2
        with self.assertRaisesRegex(ValueError,"ambiguous selection"):
            actual_answer(x)
        x=copy.deepcopy(self.interactive["int-match-collision-properties"])
        x["interaction"]["placements"].append(copy.deepcopy(x["interaction"]["placements"][0]))
        with self.assertRaisesRegex(ValueError,"incomplete placements"):
            actual_answer(x)

    def test_private_source_bound_report_is_falsifiable_and_never_full_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            pdf=Path(temp)/"source.pdf"
            pdf.write_bytes(b"%PDF-1.4 test only")
            digest=hashlib.sha256(pdf.read_bytes()).hexdigest()
            package=copy.deepcopy(self.real_package)
            canonical=hashlib.sha256(json.dumps(package,sort_keys=True,ensure_ascii=False,
                    separators=(",",":")).encode("utf-8")).hexdigest()
            # One source anchor is sufficient for a bounded model; every
            # missing activity remains REVIEW_REQUIRED in this partial fixture.
            text="In this reference the isolated particles exchange energy while conserving total momentum during collision."
            receipt={
                "sourceSha256":digest,
                "packageCanonicalSha256":canonical,
                "proofs":[{
                    "activityId":"int-order-post-collision-speeds",
                    "model":"order_target_speeds",
                    "anchor":{
                        "activityId":"int-order-post-collision-speeds",
                        "pageIndex":1,
                        "quotedText":text,
                    },
                }],
            }
            fixture_digests={a["id"]:semantic_digest(a) for a in package["activities"]}
            with patch.dict(EXPECTED_TEXT_SHA256,fixture_digests):
              with patch("app_generator.validation.interactive_physics.extract_pages",
                         return_value=(text,)):
                  report=audit_interaction_models(package,pdf,digest,receipt)
                  self.assertEqual(1,report["boundedModelsVerified"])
                  self.assertEqual(8,report["unresolved"])
                  self.assertEqual(0,report["fullAcademicActivitiesPassed"])
                  self.assertFalse(report["publicationAuthorized"])
                  changed=copy.deepcopy(package)
                  next(a for a in changed["activities"] if a["id"]=="int-order-post-collision-speeds")["interaction"]["correctOrder"].reverse()
                  with self.assertRaisesRegex(ValueError,"package"):
                      audit_interaction_models(changed,pdf,digest,receipt)
                  with self.assertRaisesRegex(ValueError,"source PDF SHA"):
                      audit_interaction_models(package,pdf,"0"*64,receipt)
                  receipt["proofs"].append(copy.deepcopy(receipt["proofs"][0]))
                  with self.assertRaisesRegex(ValueError,"duplicate"):
                      audit_interaction_models(package,pdf,digest,receipt)

    def test_changed_multilingual_narrative_blocks_recertified_model(self):
        with tempfile.TemporaryDirectory() as temp:
            pdf=Path(temp)/"source.pdf"
            pdf.write_bytes(b"%PDF-1.4 controlled fixture")
            digest=hashlib.sha256(pdf.read_bytes()).hexdigest()
            package=copy.deepcopy(self.real_package)
            activity=next(x for x in package["activities"] if x["id"]=="int-order-post-collision-speeds")
            activity["prompt"]={"en":"Which target is fastest?","ms":"Mana sasaran?","zh":"????"}
            canonical=hashlib.sha256(json.dumps(package,sort_keys=True,ensure_ascii=False,
                      separators=(",",":")).encode("utf-8")).hexdigest()
            quote="The isolated particles may exchange kinetic energy while conserving their combined momentum."
            receipt={"sourceSha256":digest,"packageCanonicalSha256":canonical,
                     "proofs":[{"activityId":activity["id"],"model":"order_target_speeds",
                                "anchor":{"activityId":activity["id"],"pageIndex":1,
                                          "quotedText":quote}}]}
            fixtures={x["id"]:semantic_digest(x) for x in self.real_package["activities"]}
            with patch.dict(EXPECTED_TEXT_SHA256,fixtures):
              with patch("app_generator.validation.interactive_physics.extract_pages",
                         return_value=(quote,)):
                  r=audit_interaction_models(package,pdf,digest,receipt)
            changed=next(x for x in r["results"] if x["activityId"]==activity["id"])
            self.assertEqual("REVIEW_REQUIRED",changed["status"])
            self.assertIn("wording differs",changed["reason"])
            self.assertEqual(0,r["boundedModelsVerified"])
            self.assertEqual(0,r["fullAcademicActivitiesPassed"])

    def test_qualifier_is_a_review_gate_not_an_unjustified_physics_pass(self):
        _,_,caveats,proof=assignments("impulse_conditions")
        self.assertEqual(len(caveats),1)
        self.assertEqual(proof["externalImpulse"],"1/100000")
        self.assertNotEqual(proof["externalImpulse"],"0")


if __name__=="__main__":
    unittest.main()
