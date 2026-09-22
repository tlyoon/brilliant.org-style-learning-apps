import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from app_generator.sources.google_drive import (
    DriveItem,
    FOLDER_MIME,
    PDF_MIME,
    discover_drive_sources_with_corpus_keys,
    discover_topic_corpus,
    topic_corpus_job_key,
)
from app_generator.sources.local_sources import inspect_sources
from app_generator.sources.manifest import build_manifest


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
