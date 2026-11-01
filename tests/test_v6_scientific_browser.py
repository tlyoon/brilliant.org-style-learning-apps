"""Source-free adversarial checks for controlled multilingual learner surfaces."""
import unittest
from scripts.audit_private_v6_scientific_browser import normalize_visible,check_science_surface


class ScientificLocaleSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.mcq={
            "type":"mcq",
            "prompt":{"en":"Conservative swing?","ms":"Ayunan konservatif?",
                      "zh":"\u4fdd\u5b88\u529b\u6446\u52a8\uff1f"},
        }
        self.interactive={
            "type":"interactive",
            "prompt":{"en":"Classify forces","ms":"Kelaskan daya","zh":"\u529b\u7684\u5206\u7c7b"},
            "interaction":{"items":[
                {"label":{"en":"Potential energy",
                          "ms":"Tenaga keupayaan",
                          "zh":"\u52bf\u80fd"}}]},
        }

    def test_trilingual_scientific_prompt_identity(self):
        for locale in ("en","ms","zh"):
            check_science_surface(
                self.mcq,locale,self.mcq["prompt"][locale],"Body")

    def test_new_malay_conservative_word_and_no_eternal_claim(self):
        check_science_surface(
            self.mcq,"ms","Ayunan konservatif?","Daya graviti konservatif")
        with self.assertRaisesRegex(ValueError,"incorrect eternal"):
            check_science_surface(self.mcq,"ms","Ayunan konservatif?",
                                  "daya graviti abadi")
        # Embedded words such as 'diabadikan' mean 'conserved', not eternal.
        check_science_surface(self.mcq,"ms","Ayunan konservatif?",
                              "Momentum diabadikan oleh sistem.")

    def test_missing_or_changed_question_rejected(self):
        with self.assertRaisesRegex(ValueError,"question differs"):
            check_science_surface(self.mcq,"en","Changed?","Body")
        with self.assertRaisesRegex(ValueError,"replacement character"):
            a=dict(self.mcq)
            a["prompt"]=dict(self.mcq["prompt"],en="Conservative \ufffdswing?")
            check_science_surface(a,"en","Conservative \ufffdswing?","Body")
        with self.assertRaisesRegex(ValueError,"unsupported locale"):
            check_science_surface(self.mcq,"fr","What?","Body")

    def test_interactive_item_missing_or_translated(self):
        for locale in ("en","ms","zh"):
            a=self.interactive
            check_science_surface(a,locale,a["prompt"][locale],
                                  "Shown: "+a["interaction"]["items"][0]["label"][locale])
        with self.assertRaisesRegex(ValueError,"not visible"):
            check_science_surface(self.interactive,"ms","Kelaskan daya","No label")
        broken={**self.interactive,"interaction":{"items":[]}}
        with self.assertRaisesRegex(ValueError,"items missing"):
            check_science_surface(broken,"ms","Kelaskan daya","Label")


if __name__=="__main__":
    unittest.main()
