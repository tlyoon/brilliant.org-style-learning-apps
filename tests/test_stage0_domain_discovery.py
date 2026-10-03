import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app_generator.domains.discovery import (
    domain_binding_path,
    domain_status_path,
    ensure_drive_domain,
    representative_sources,
    source_inventory_fingerprint,
)
from app_generator.errors import DomainDiscoveryError, DomainProfileRequiredError
from app_generator.sources.google_drive import ResolvedDriveSource

ROOT = Path(__file__).resolve().parents[1]


def source(subchapter: str, job: str) -> ResolvedDriveSource:
    return ResolvedDriveSource(
        file_id=f"file-{subchapter.replace('.', '-')}",
        filename="source.pdf",
        relative_path=f"chapter/{subchapter}/source.pdf",
        mime_type="application/pdf",
        size_bytes=100,
        md5_checksum=job,
        subchapter_id=subchapter,
        parent_folder_id=f"folder-{subchapter.replace('.', '-')}",
        corpus_job_key=job,
    )


class FakeDrive:
    def __init__(self):
        self.downloads = []

    def download_file(self, item, destination):
        self.downloads.append(item.subchapter_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"%PDF-domain-sample-" + item.subchapter_id.encode())
        return destination


class FakeClassifier:
    actual_model = "fake-domain-model"

    def __init__(self, paths, document):
        self.paths = paths
        self.document = document
        self.prepared = False
        self.prompts = []

    def prepare(self):
        self.prepared = True

    def ask(self, prompt, *, stage=None):
        self.prompts.append((prompt, stage))
        return "BEGIN_JSON\n" + json.dumps(self.document) + "\nEND_JSON"


def physics_document(sample_ids, *, confidence=0.98, consistency="consistent"):
    return {
        "subject": "physics",
        "academicLevel": "university",
        "matchedDomainId": "university-level-physics",
        "confidence": confidence,
        "consistency": consistency,
        "sampleAssessments": [
            {
                "subchapterId": item,
                "subject": "physics",
                "academicLevel": "university",
                "matchedDomainId": "university-level-physics",
                "confidence": 0.96,
            }
            for item in sample_ids
        ],
    }


class StageZeroDomainDiscoveryTests(unittest.TestCase):
    def config(self, state_root: Path, **overrides):
        values = dict(
            repo_root=ROOT,
            state_dir=state_root / "runs",
            domain_id="auto",
            domain_sample_count=3,
            domain_min_confidence=0.85,
        )
        values.update(overrides)
        return SimpleNamespace(**values)

    def inventory(self):
        return tuple(source(f"{chapter}.1", f"job-{chapter}") for chapter in range(1, 6))

    def test_representative_sampling_spreads_across_the_textbook(self):
        selected = representative_sources(self.inventory(), 3)
        self.assertEqual(("1.1", "3.1", "5.1"), tuple(item.subchapter_id for item in selected))

    def test_source_fingerprint_covers_every_discovered_topic_corpus(self):
        inventory = self.inventory()
        first = source_inventory_fingerprint(inventory)
        changed = list(inventory)
        changed[3] = source("4.1", "job-4-changed")
        self.assertNotEqual(first, source_inventory_fingerprint(tuple(changed)))
        self.assertEqual(first, source_inventory_fingerprint(tuple(reversed(inventory))))

    def test_automatic_detection_binds_and_reuses_matching_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            config = self.config(state)
            inventory = self.inventory()
            sample_ids = ("1.1", "3.1", "5.1")
            created = []

            def factory(_config, paths):
                client = FakeClassifier(paths, physics_document(sample_ids))
                created.append(client)
                return client

            drive = FakeDrive()
            profile = ensure_drive_domain(config, drive, inventory, client_factory=factory)
            self.assertEqual("university-level-physics", profile.id)
            self.assertEqual(sample_ids, tuple(drive.downloads))
            self.assertEqual(1, len(created))
            self.assertTrue(created[0].prepared)
            self.assertEqual("domain-discovery", created[0].prompts[0][1])

            binding = json.loads(domain_binding_path(config).read_text(encoding="utf-8"))
            self.assertEqual(source_inventory_fingerprint(inventory), binding["sourceFingerprint"])
            self.assertEqual(profile.profile_version, binding["domainProfileVersion"])
            self.assertEqual(list(sample_ids), binding["sampleSubchapters"])

            drive2 = FakeDrive()
            reused = ensure_drive_domain(
                config,
                drive2,
                inventory,
                client_factory=lambda *_: self.fail("cached binding should avoid a second classifier call"),
            )
            self.assertEqual(profile.id, reused.id)
            self.assertEqual([], drive2.downloads)

    def test_changed_source_tree_invalidates_binding_and_reclassifies(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(Path(directory))
            inventory = self.inventory()
            calls = []

            def factory(_config, paths):
                calls.append(tuple(path.name for path in paths))
                ids = tuple(path.name.split("-source.pdf")[0] for path in paths)
                return FakeClassifier(paths, physics_document(ids))

            ensure_drive_domain(config, FakeDrive(), inventory, client_factory=factory)
            changed = list(inventory)
            changed[-1] = source("5.1", "job-5-new")
            ensure_drive_domain(config, FakeDrive(), tuple(changed), client_factory=factory)
            self.assertEqual(2, len(calls))

    def test_unsupported_textbook_requires_new_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(Path(directory))
            inventory = self.inventory()
            sample_ids = ("1.1", "3.1", "5.1")
            document = {
                "subject": "chemistry",
                "academicLevel": "university",
                "matchedDomainId": "unsupported",
                "confidence": 0.99,
                "consistency": "consistent",
                "sampleAssessments": [
                    {
                        "subchapterId": item,
                        "subject": "chemistry",
                        "academicLevel": "university",
                        "matchedDomainId": "unsupported",
                        "confidence": 0.98,
                    }
                    for item in sample_ids
                ],
            }
            with self.assertRaisesRegex(DomainProfileRequiredError, "chemistry"):
                ensure_drive_domain(
                    config,
                    FakeDrive(),
                    inventory,
                    client_factory=lambda _config, paths: FakeClassifier(paths, document),
                )
            self.assertFalse(domain_binding_path(config).exists())
            status = json.loads(domain_status_path(config).read_text(encoding="utf-8"))
            self.assertEqual("profile-required", status["status"])
            self.assertEqual("DOMAIN_PROFILE_REQUIRED", status["errorCode"])
            self.assertEqual(source_inventory_fingerprint(inventory), status["sourceFingerprint"])

    def test_ambiguous_or_low_confidence_detection_fails_closed(self):
        for confidence, consistency in ((0.6, "consistent"), (0.96, "mixed")):
            with self.subTest(confidence=confidence, consistency=consistency), tempfile.TemporaryDirectory() as directory:
                config = self.config(Path(directory))
                inventory = self.inventory()
                sample_ids = ("1.1", "3.1", "5.1")
                document = physics_document(sample_ids, confidence=confidence, consistency=consistency)
                with self.assertRaises(DomainDiscoveryError):
                    ensure_drive_domain(
                        config,
                        FakeDrive(),
                        inventory,
                        client_factory=lambda _config, paths, doc=document: FakeClassifier(paths, doc),
                    )

    def test_explicit_domain_override_is_deliberate_and_does_not_call_classifier(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(Path(directory), domain_id="university-level-physics")
            inventory = self.inventory()
            profile = ensure_drive_domain(
                config,
                FakeDrive(),
                inventory,
                client_factory=lambda *_: self.fail("explicit domain must not call classifier"),
            )
            self.assertEqual("university-level-physics", profile.id)
            binding = json.loads(domain_binding_path(config).read_text(encoding="utf-8"))
            self.assertEqual("explicit", binding["selection"])
            self.assertEqual([], binding["sampleSubchapters"])

    def test_profile_version_change_invalidates_cached_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(Path(directory))
            inventory = self.inventory()
            sample_ids = ("1.1", "3.1", "5.1")
            ensure_drive_domain(
                config,
                FakeDrive(),
                inventory,
                client_factory=lambda _config, paths: FakeClassifier(paths, physics_document(sample_ids)),
            )
            binding_path = domain_binding_path(config)
            binding = json.loads(binding_path.read_text(encoding="utf-8"))
            binding["domainProfileVersion"] = "0.0.0-stale"
            binding_path.write_text(json.dumps(binding), encoding="utf-8")
            calls = []
            ensure_drive_domain(
                config,
                FakeDrive(),
                inventory,
                client_factory=lambda _config, paths: calls.append(True) or FakeClassifier(paths, physics_document(sample_ids)),
            )
            self.assertEqual([True], calls)


if __name__ == "__main__":
    unittest.main()
