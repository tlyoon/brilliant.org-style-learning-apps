"""Source-free adversarial join tests for academic action ordering."""
import unittest
from app_generator.validation.academic_review_priorities import prioritize_academic_review

A="a"*64
B="b"*64


class AcademicQueueTests(unittest.TestCase):
    def setUp(self):
        self.coverage={
            "status":"EXACT_ORIGINAL_SOURCE_ACADEMIC_CLAIM_COVERAGE",
            "sourceSha256":A,"packageSha256":B,"activityCount":3,
            "sourceActivitiesReverified":3,"activities":[
                {"activityId":"a","claimStates":{"AMBIGUOUS":3,"COMPLETE":5,"SKIPPED_UNSENT":2},
                 "originalSourcePassageReverified":True,"publicationAuthorized":False},
                {"activityId":"b","claimStates":{"NOT_SUBMITTED":10},
                 "originalSourcePassageReverified":True,"publicationAuthorized":False},
                {"activityId":"c","claimStates":{"NOT_SUBMITTED":10},
                 "originalSourcePassageReverified":True,"publicationAuthorized":False},
            ]}
        self.triage={
            "status":"SOURCE_BOUND_NUMERIC_TOKEN_TRIAGE","sourceSha256":A,
            "packageSha256":B,"sourceVerifiedActivities":3,"numericDriftFlagCount":1,
            "activities":[
                {"activityId":"a","numericTokenDriftFlags":[]},
                {"activityId":"b","numericTokenDriftFlags":[{
                    "reasonCode":"CROSS_LOCALE_NUMERIC_TOKEN_DIFFERENCE",
                    "confirmedSemanticEquivalence":False,
                    "candidateReason":"POSSIBLE_ONE_DIMENSION_NOTATION"}]},
                {"activityId":"c","numericTokenDriftFlags":[]},
            ]}

    def test_blocked_nonreplayable_claims_priority_before_multilingual(self):
        result=prioritize_academic_review(self.coverage,self.triage)
        self.assertEqual(["a","b","c"],[r["activityId"] for r in result["activities"]])
        self.assertEqual("RECONCILE_EXISTING_NONREPLAYABLE_CLAIMS",result["activities"][0]["priority"])
        self.assertEqual("INDEPENDENT_MULTILINGUAL_SEMANTIC_REVIEW",result["activities"][1]["priority"])
        self.assertEqual(1,result["activities"][1]["possibleNotationEquivalentFlags"])
        self.assertFalse(result["numericParityEstablishesTranslation"])
        self.assertFalse(result["publicationAuthorized"])

    def test_changed_original_pdf_or_corrected_package_rejected(self):
        with self.assertRaisesRegex(ValueError,"provenance"):
            prioritize_academic_review(self.coverage,{**self.triage,"sourceSha256":"c"*64})
        with self.assertRaisesRegex(ValueError,"provenance"):
            prioritize_academic_review(self.coverage,{**self.triage,"packageSha256":"c"*64})

    def test_falsely_approved_translation_flag_rejected(self):
        self.triage["activities"][1]["numericTokenDriftFlags"][0]["confirmedSemanticEquivalence"]=True
        with self.assertRaisesRegex(ValueError,"unproven"):
            prioritize_academic_review(self.coverage,self.triage)

    def test_missing_source_activity_roster_or_forged_flag_total_rejected(self):
        with self.assertRaisesRegex(ValueError,"identities"):
            prioritize_academic_review(self.coverage,{**self.triage,
                "activities":self.triage["activities"][:2]+[{"activityId":"not-c","numericTokenDriftFlags":[]}]})
        with self.assertRaisesRegex(ValueError,"totals"):
            prioritize_academic_review(self.coverage,{**self.triage,"numericDriftFlagCount":100})

    def test_falsely_approved_academic_coverage_rejected(self):
        self.coverage["activities"][0]["publicationAuthorized"]=True
        with self.assertRaisesRegex(ValueError,"falsely approved"):
            prioritize_academic_review(self.coverage,self.triage)


if __name__=="__main__":
    unittest.main()
