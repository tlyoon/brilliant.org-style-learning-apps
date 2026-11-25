"""Exact collision witness and fail-closed private v8 repair tests."""
import copy,hashlib,unittest
from app_generator.validation.relative_velocity_derivation import restitution_witness,patch_derivation

class RelativeVelocityDerivationTests(unittest.TestCase):
    def setUp(self):
        self.a={"activities":[{"id":"activity-"+str(i)} for i in range(17)]+[
            {"id":"mcq-relative-velocity-scope","answerKey":{"correct":"A"},
             "answerLogic":{"en":"A"+"p"*180,"ms":"B"+"q"*180,"zh":"C"+"r"*180}}]}
        self.rules={"activityId":"mcq-relative-velocity-scope","replacements":{}}
        for loc,old in self.a["activities"][-1]["answerLogic"].items():
            self.rules["replacements"][loc]={
                "oldFieldSha256":hashlib.sha256(old.encode()).hexdigest(),
                "newText":"Correct energy premise and momentum equations "+old}

    def test_exact_inelastic_velocity_and_energy(self):
        x=restitution_witness()
        self.assertEqual("5/8",x["1/2"]["kineticEnergyRatio"])
        self.assertEqual("1",x["1/2"]["finalMomentum"])
        self.assertEqual("1/2",x["1/2"]["relativeSeparationSpeed"])
        self.assertEqual("1",x["1"]["kineticEnergyRatio"])

    def test_three_locale_only_copy_on_write(self):
        old=copy.deepcopy(self.a)
        new=patch_derivation(self.a,self.rules)
        self.assertEqual(self.a,old)
        self.assertEqual(old["activities"][:17],new["activities"][:17])
        self.assertEqual(old["activities"][-1]["answerKey"],new["activities"][-1]["answerKey"])
        self.assertNotEqual(old["activities"][-1]["answerLogic"],new["activities"][-1]["answerLogic"])

    def test_stale_hash_rejected(self):
        self.a["activities"][-1]["answerLogic"]["ms"]="new text"*30
        with self.assertRaisesRegex(ValueError,"unverified"):patch_derivation(self.a,self.rules)

    def test_missing_locale_or_bad_scope_rejected(self):
        self.rules["replacements"].pop("zh")
        with self.assertRaisesRegex(ValueError,"three locale"):patch_derivation(self.a,self.rules)
        self.rules["replacements"]["zh"]={"oldFieldSha256":"0"*64,"newText":"x"*200}
        self.rules["activityId"]="wrong"
        with self.assertRaisesRegex(ValueError,"scope"):patch_derivation(self.a,self.rules)

if __name__=="__main__":unittest.main()
