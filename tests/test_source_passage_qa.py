import hashlib
import unittest
from pathlib import Path
from unittest.mock import patch

from app_generator.validation.source_passages import check_anchor, audit_source_anchors

class SourcePassageQATests(unittest.TestCase):
    page_1 = "The isolated system conserves momentum during the brief collision between the two carts."
    page_2 = "The total kinetic energy stays constant only for perfectly elastic collisions involving two particles."
    quote = "The isolated system conserves momentum during the brief collision between the two carts."

    def test_page_and_exact_quote_require_context_without_academic_claim(self):
        pages = (self.page_1, self.page_2)
        good = check_anchor(pages, {"activityId":"a","pageIndex":1,"quotedText":self.quote})
        self.assertEqual("VERIFIED_TEXT_ONLY",good["status"])
        self.assertEqual(64,len(good["quoteSha256"]))
        self.assertIn("unverified",good["reason"])
        bad = check_anchor(pages,{"activityId":"a","pageIndex":2,"quotedText":self.quote})
        self.assertEqual("FAIL",bad["status"])
        self.assertEqual("REVIEW_REQUIRED",check_anchor(pages, {
            "activityId":"a","pageIndex":1,"quotedText":"momentum"
        })["status"])

    def test_repeated_or_corrupt_excerpts_fail_closed(self):
        pages=(self.page_1,self.page_1)
        record={"activityId":"a","pageIndex":1,"quotedText":self.quote}
        self.assertEqual("REVIEW_REQUIRED",check_anchor(pages,record)["status"])
        record["quotedText"]="This claim is not in either of the source PDF pages at all."
        self.assertEqual("REVIEW_REQUIRED",check_anchor(pages,record)["status"])
        record["pageIndex"]=False
        self.assertEqual("REVIEW_REQUIRED",check_anchor(pages,record)["status"])

    def test_exact_pdf_hash_and_missing_activity_anchors(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"source.pdf"
            path.write_bytes(b"%PDF-1.4 fake fixture")
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            pkg={"activities":[{"id":"a"},{"id":"b"}]}
            with patch("app_generator.validation.source_passages.extract_pages",
                       return_value=(self.page_1,self.page_2)):
                result=audit_source_anchors(pkg,path,digest,[{
                    "activityId":"a","pageIndex":1,"quotedText":self.quote
                }])
                self.assertEqual(1,result["passageLocationVerified"])
                self.assertEqual(1,result["pending"])
                self.assertFalse(result["academicQAPass"])
                self.assertFalse(result["publicationAuthorized"])
                with self.assertRaisesRegex(ValueError,"SHA"):
                    audit_source_anchors(pkg,path,"0"*64,[])
                with self.assertRaisesRegex(ValueError,"duplicate anchor"):
                    audit_source_anchors(pkg,path,digest,[{"activityId":"a"},{"activityId":"a"}])
                with self.assertRaisesRegex(ValueError,"unknown"):
                    audit_source_anchors(pkg,path,digest,[{"activityId":"wrong"}])

if __name__=="__main__":
    unittest.main()
