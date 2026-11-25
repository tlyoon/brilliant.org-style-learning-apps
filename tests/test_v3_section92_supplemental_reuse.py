"""BSA213: source-free metadata of four saved scientific reviews, fake-only tests.

These fixtures do NOT constitute new independent Gemini model assessments.
"""
from contextlib import ExitStack
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app_generator.runtime.v3_four_new92_review import (
    PINNED, PARENT, SECTION, stage_exact_one,
)
from app_generator.runtime.v3_frozen_original_tail import _slice
from app_generator.runtime.v3_section92_supplemental_reuse import (
    verified_section92_original_tail_passes,
)
from app_generator.runtime.v3_auto_repair import (
    _ACTIVITY, _CANDIDATE, _CHANGES,
)
from app_generator.runtime.v3_versioned_acceptance_scope import (
    prepare_versioned_course_proposal,
)
from app_generator.validation.v3_versioned_text_repair import (
    make_locale_repair, store_private_repair,
)
from app_generator.validation.autonomous_completion import package_identity
from app_generator.validation.autonomous_ai_review import canonical_digest

REPO = Path(__file__).resolve().parents[1]
COURSE = REPO / "content" / "chapter-9"


def _four_fixture_entries() -> tuple[str,tuple,list[dict]]:
    # BSA214: real Yoga6 source SHA remains pinned in production, but
    # synthetic hosted-Linux tests must derive SHA from their own checkout
    # bytes. Git line endings can differ between Windows and Ubuntu.
    raw = (COURSE / SECTION / "package.json").read_bytes()
    digest, items = package_identity(raw)
    entries = []
    local_pins = []
    for index, name, _owner_sha in PINNED:
        assert items[index]["id"] == name
        slice_raw, review_sha, manifest = _slice(
            digest,SECTION,index,items[index])
        local_pins.append((index,name,review_sha))
        entries.append({
            "index":index,"activityId":name,"sha":review_sha,
            "raw":slice_raw,"manifest":manifest,
            "originalReviewState":"AGGREGATE_EXISTS",
        })
    return digest,tuple(local_pins),entries


class FourNewEvidenceReuseTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.private=Path(self.temp.name)/"private"
        self.private.mkdir()
        self.fixture_parent,self.fixture_pins,self.entries=_four_fixture_entries()
        for variable,value in (
            ("PARENT",self.fixture_parent),
            ("PINNED",self.fixture_pins),
        ):
            fixture=patch(
                "app_generator.runtime.v3_section92_supplemental_reuse."
                +variable,value)
            fixture.start()
            self.addCleanup(fixture.stop)

    def test_synthetic_source_hash_uses_local_checkout_not_paid_owner_pin(self):
        raw=(COURSE/SECTION/"package.json").read_bytes()
        self.assertEqual(package_identity(raw)[0],self.fixture_parent)
        self.assertEqual(
            [x["sha"] for x in self.entries],
            [digest for _, _, digest in self.fixture_pins])
        # Never redefine the actual owner-authorized Yoga6 input hashes.
        self.assertEqual(PARENT,
            "cfe7bab820aa01ce71bd7a6a334c742101ebd10d8895cccd5f05d599030f971c")

    def _install_fake_evidence(self):
        for e in self.entries:
            stage_exact_one(self.private,e)
            folder=self.private/("v3-generated-"+e["sha"])/"batches"
            folder.mkdir(parents=True)
            (folder/("v3-assessment-"+e["sha"]+".json")).write_text(
                json.dumps({"reviews":[{"activityId":e["activityId"],
                                       "status":"AI_CONSENSUS_PASS"}]}),encoding="utf8")

    def _simulate_two_role_passes(self):
        stack=ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch(
            "app_generator.runtime.v3_section92_supplemental_reuse."
            "exact_four_unreviewed",return_value=self.entries))
        stack.enter_context(patch(
            "app_generator.runtime.v3_section92_supplemental_reuse."
            "read_prior_two_role_science",
            return_value={"pass":True,"repair":False,"uncertain":False}))
        stack.enter_context(patch(
            "app_generator.runtime.v3_section92_supplemental_reuse."
            "assessment_progress",return_value={
                "activitiesAssessed":1,"activitiesFullyModelReviewed":1,
                "modelConsensusPassActivities":1}))
        return stack

    def test_no_authorized_role_dir_means_no_claim_of_new_four_passes(self):
        self.assertEqual(verified_section92_original_tail_passes(
            COURSE,REPO,self.private),[])

    def test_saved_fixture_cannot_claim_genuine_pass_without_two_real_roles(self):
        self._install_fake_evidence()
        with patch(
            "app_generator.runtime.v3_section92_supplemental_reuse."
            "exact_four_unreviewed",return_value=self.entries):
            with self.assertRaisesRegex(ValueError,
                                        "UNTRUSTED_ASSESSMENT_PROGRESS|"
                                        "TWO_ROLE_EVIDENCE|MISSING_DURABLE"):
                verified_section92_original_tail_passes(
                    COURSE,REPO,self.private)

    def test_four_fake_consensus_proofs_make_only_potential_reuse_metadata(self):
        self._install_fake_evidence()
        with self._simulate_two_role_passes():
            items=verified_section92_original_tail_passes(
                COURSE,REPO,self.private)
        self.assertEqual(len(items),4)
        self.assertEqual(
            [x["originalActivityIndex"] for x in items],[14,15,16,17])
        self.assertTrue(all(x["status"]==
            "POTENTIALLY_REUSABLE_NOT_RELEASE_ACCEPTED" for x in items))
        self.assertTrue(all(x["sourcePackageSha256"]==
                            self.fixture_parent for x in items))

    def test_tampered_private_slice_fails_closed(self):
        self._install_fake_evidence()
        slot=self.private/"four-new-original92-slices"/self.entries[2]["sha"]
        (slot/"package.json").write_bytes(b'{"forged":true}')
        with self._simulate_two_role_passes():
            with self.assertRaisesRegex(ValueError,
                                        "SAVED_SOURCE_CHANGED"):
                verified_section92_original_tail_passes(
                    COURSE,REPO,self.private)

    def test_role_science_fail_never_becomes_reuse_pass(self):
        self._install_fake_evidence()
        with self._simulate_two_role_passes():
            with patch(
                "app_generator.runtime.v3_section92_supplemental_reuse."
                "read_prior_two_role_science",
                return_value={"pass":False,"repair":True,"uncertain":False}):
                self.assertEqual(verified_section92_original_tail_passes(
                    COURSE,REPO,self.private),[])

    def test_synthetic_manifest_links_only_original_four_and_cannot_release(self):
        parent = (COURSE / SECTION / "package.json").read_bytes()
        corrected, receipt = make_locale_repair(parent,_ACTIVITY,"ms",_CHANGES)
        store_private_repair(self.private/"repair-proposals"/SECTION,
                             corrected,receipt)
        _, original_items=package_identity(parent)
        fake_rows=[{
            "section":SECTION,"originalActivityIndex":index,
            "activityId":name,
            "activitySha256":canonical_digest(original_items[index]),
            "sourcePackageSha256":self.fixture_parent,
            "supplementalReviewSliceSha256":sha,
            "sourceReviewSha256":"a"*64,
            "status":"POTENTIALLY_REUSABLE_NOT_RELEASE_ACCEPTED"}
            for index,name,sha in self.fixture_pins]
        with patch(
            "app_generator.runtime.v3_versioned_acceptance_scope."
            "verified_section92_original_tail_passes",return_value=fake_rows):
            result=prepare_versioned_course_proposal(COURSE,REPO,self.private)
        f=(self.private/"versioned-course-proposals"/result["proposalSha256"]
           /"scope-proposal.json")
        stored=json.loads(f.read_text(encoding="utf8"))
        self.assertFalse(stored["publicationAuthorized"])
        self.assertFalse(stored["versionedScopeAdmitted"])
        self.assertFalse(stored["all108ReviewedAndApproved"])
        self.assertEqual(stored["counts"]["newFourSection92SupplementalConsensusPasses"],4)
        self.assertEqual(len(stored["section92FourNewGenuineOriginalReviews"]),4)
        self.assertEqual(stored["counts"]["originalAssessed"],0)
        self.assertEqual(stored["counts"]["potentiallyReusablePasses"],4)


if __name__=="__main__":
    unittest.main()
