import hashlib
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from app_generator.errors import DriveAccessError, SourceAmbiguous, SourceDownloadError, SourceNotFound
from app_generator.sources.google_drive import (
    DriveItem,
    FOLDER_MIME,
    PDF_MIME,
    discover_drive_sources_with_corpus_keys,
    discover_topic_corpus,
    topic_corpus_job_key,
)
from app_generator.sources.local_sources import inspect_sources
from app_generator.sources.manifest import (
    build_manifest, load_existing_manifest, select_primary_source,
)
from app_generator.errors import RepositoryCompatibilityError


class FakeDrive:
    def __init__(self, bank_checksum="bbb"):
        self.children = {
            "root123456789": (
                DriveItem("ch8folder123", "8", FOLDER_MIME),
                DriveItem("statefolder123", "_appgen_state", FOLDER_MIME),
            ),
            "ch8folder123": (DriveItem("topic82folder", "8.2", FOLDER_MIME),),
            "topic82folder": (
                DriveItem("primaryfile123", "source.pdf", PDF_MIME, md5_checksum="aaa"),
                DriveItem("bankfile12345", "question-bank.pdf", PDF_MIME, md5_checksum=bank_checksum),
                DriveItem("notesfile1234", "notes.txt", "text/plain"),
            ),
        }
    def get_item(self, file_id):
        if file_id == "root123456789":
            return DriveItem(file_id, "root", FOLDER_MIME)
        raise AssertionError(file_id)

    def list_children(self, folder_id):
        if folder_id == "statefolder123":
            raise AssertionError("source discovery must not traverse _appgen_state")
        return self.children.get(folder_id, ())


class MultiPdfCorpusTests(unittest.TestCase):
    def test_topic_corpus_includes_all_sibling_pdfs(self):
        corpus = discover_topic_corpus(
            FakeDrive(),
            sourcepath="root123456789",
            pdf_subchapter_path="8.2",
            target_filename="source.pdf",
            max_folders=20,
        )
        self.assertEqual(
            ["question-bank.pdf", "source.pdf"],
            [item.filename for item in corpus],
        )
        self.assertEqual(corpus[0].subchapter_id, "8.2")
        self.assertNotEqual(topic_corpus_job_key(corpus), topic_corpus_job_key(corpus[:1]))

    def test_supplementary_pdf_change_changes_auto_corpus_identity(self):
        before = discover_topic_corpus(
            FakeDrive("bbb"), sourcepath="root123456789", pdf_subchapter_path="8.2",
            target_filename="source.pdf", max_folders=20,
        )
        after = discover_topic_corpus(
            FakeDrive("ccc"), sourcepath="root123456789", pdf_subchapter_path="8.2",
            target_filename="source.pdf", max_folders=20,
        )
        self.assertNotEqual(topic_corpus_job_key(before), topic_corpus_job_key(after))

    def test_auto_inventory_binds_full_corpus_key_in_one_source_discovery(self):
        inventory = discover_drive_sources_with_corpus_keys(
            FakeDrive(), sourcepath="root123456789", target_filename="source.pdf", max_folders=20,
        )
        corpus = discover_topic_corpus(
            FakeDrive(), sourcepath="root123456789", pdf_subchapter_path="8.2",
            target_filename="source.pdf", max_folders=20,
        )
        self.assertEqual(1, len(inventory))
        self.assertEqual(topic_corpus_job_key(corpus), inventory[0].job_key)

    def test_targeted_corpus_uses_one_root_traversal_and_same_auto_key(self):
        class CountedDrive(FakeDrive):
            def __init__(self):
                super().__init__()
                self.calls = []
                self.root_calls = 0

            def get_item(self, file_id):
                self.root_calls += 1
                return super().get_item(file_id)

            def list_children(self, folder_id):
                self.calls.append(folder_id)
                return super().list_children(folder_id)

        client = CountedDrive()
        corpus = discover_topic_corpus(
            client, sourcepath="root123456789",
            pdf_subchapter_path="8.2", target_filename="source.pdf",
            max_folders=20,
        )
        self.assertEqual(
            ["root123456789", "ch8folder123", "topic82folder"], client.calls,
            "A topic lookup should never walk the root twice",
        )
        self.assertEqual(1, client.root_calls)
        expected = hashlib.sha256(
            b"bankfile12345:bbb\nprimaryfile123:aaa"
        ).hexdigest()
        self.assertEqual(expected, topic_corpus_job_key(corpus),
                         "Existing coordinator/lease job keys must be unchanged")

    def test_ambiguous_topic_folders_do_not_choose_one_silently(self):
        client = FakeDrive()
        client.children["root123456789"] += (
            DriveItem("otherch8folder", "duplicate", FOLDER_MIME),
        )
        client.children["otherch8folder"] = (
            DriveItem("other82folder", "8.2", FOLDER_MIME),
        )
        client.children["other82folder"] = (
            DriveItem("other-pdf-id", "source.pdf", PDF_MIME),
        )
        with self.assertRaises(SourceAmbiguous):
            discover_topic_corpus(
                client, sourcepath="root123456789",
                pdf_subchapter_path="8.2", target_filename="source.pdf",
                max_folders=20,
            )

    def test_case_aliased_supplementary_sources_fail_before_download(self):
        client = FakeDrive()
        client.children["topic82folder"] += (
            DriveItem("collisionpdf", "QUESTION-BANK.PDF", PDF_MIME),
        )
        kwargs = dict(sourcepath="root123456789",
                      pdf_subchapter_path="8.2", target_filename="source.pdf",
                      max_folders=20)
        with self.assertRaisesRegex(SourceAmbiguous, "case-insensitively"):
            discover_topic_corpus(client, **kwargs)
        with self.assertRaisesRegex(SourceAmbiguous, "case-insensitively"):
            discover_drive_sources_with_corpus_keys(
                client, sourcepath=kwargs["sourcepath"],
                target_filename=kwargs["target_filename"],
                max_folders=kwargs["max_folders"],
            )

    def test_disabled_supplementary_pdf_and_missing_anchor_fail_closed(self):
        client = FakeDrive()
        client.children["topic82folder"] = (
            DriveItem("primaryfile123", "source.pdf", PDF_MIME, md5_checksum="aaa"),
            DriveItem("blockedbank123", "question-bank.pdf", PDF_MIME,
                      can_download=False),
        )
        with self.assertRaises(SourceDownloadError):
            discover_topic_corpus(
                client, sourcepath="root123456789",
                pdf_subchapter_path="8.2", target_filename="source.pdf",
                max_folders=20,
            )
        with self.assertRaises(SourceNotFound):
            discover_topic_corpus(
                FakeDrive(), sourcepath="root123456789",
                pdf_subchapter_path="8.3", target_filename="source.pdf",
                max_folders=20,
            )
        with self.assertRaises(DriveAccessError):
            discover_topic_corpus(
                FakeDrive(), sourcepath="root123456789",
                pdf_subchapter_path="8.2", target_filename="source.pdf",
                max_folders=2,
            )

    def test_primary_manifest_selection_ignores_supplementary_sort_order(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bank = root / "question-bank.pdf"
            primary = root / "source.pdf"
            bank.write_bytes(b"%PDF-synthetic-questions")
            primary.write_bytes(b"%PDF-synthetic-primary")
            sources = inspect_sources((bank, primary))
            self.assertEqual(sources[0].controlled_filename, "question-bank.pdf")
            selected = select_primary_source(sources, "source.pdf")
            self.assertEqual(selected.controlled_filename, "source.pdf")

            config = SimpleNamespace(
                target_filename="source.pdf", source_id="synthetic-8-2",
                edition="test", chapter="8", subchapter="8.2",
                heading="Synthetic test", page_range="whole source",
                learning_boundary="bounded", reviewer="pending",
                rights_note="synthetic", drive_file_id=None,
            )
            manifest = build_manifest(config, sources)
            path = root / "source-manifest.json"
            import json
            path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(
                manifest, load_existing_manifest(path, selected, config)
            )
            with self.assertRaises(RepositoryCompatibilityError):
                load_existing_manifest(path, sources[0], config)

    def test_multi_pdf_missing_or_duplicate_primary_fails_closed(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bank = root / "bank.pdf"
            notes = root / "notes.pdf"
            bank.write_bytes(b"%PDF-bank")
            notes.write_bytes(b"%PDF-notes")
            sources = inspect_sources((bank, notes))
            with self.assertRaisesRegex(
                RepositoryCompatibilityError, "no controlled primary"
            ):
                select_primary_source(sources, "source.pdf")
            config = SimpleNamespace(target_filename="source.pdf")
            with self.assertRaisesRegex(
                RepositoryCompatibilityError, "no controlled primary"
            ):
                build_manifest(config, sources)
            self.assertEqual(
                "bank.pdf", select_primary_source(sources[:1], "source.pdf").controlled_filename,
                "Single-PDF legacy corpus fallback must not be retroactively broken",
            )
            # A directly supplied tuple may not yet have passed source-inspection
            # uniqueness checks. It must not silently choose an arbitrary primary.
            duplicate = (sources[0], sources[0])
            with self.assertRaisesRegex(
                RepositoryCompatibilityError, "Several source files"
            ):
                select_primary_source(duplicate, "bank.pdf")

    def test_manifest_11_records_primary_and_supplementary_sources(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            primary = root / "source.pdf"
            bank = root / "question-bank.pdf"
            primary.write_bytes(b"%PDF-primary")
            bank.write_bytes(b"%PDF-bank")
            sources = inspect_sources((bank, primary))
            config = SimpleNamespace(
                target_filename="source.pdf", source_id="physics-8-2",
                edition="test", chapter="8", subchapter="8.2",
                heading="Topic 8.2", page_range="complete corpus",
                learning_boundary="controlled corpus", reviewer="pending",
                rights_note="test", drive_file_id=None,
            )
            manifest = build_manifest(
                config, sources, drive_file_ids=("bank123", "primary123")
            )
            self.assertEqual(manifest["manifestVersion"], "1.1")
            self.assertEqual(len(manifest["sources"]), 2)
            roles = {entry["controlledFilename"]: entry["role"] for entry in manifest["sources"]}
            self.assertEqual(roles["source.pdf"], "primary")
            self.assertEqual(roles["question-bank.pdf"], "supplementary")
            self.assertEqual(len(manifest["corpusSha256"]), 64)


if __name__ == "__main__":
    unittest.main()
