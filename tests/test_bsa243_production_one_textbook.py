"""BSA243 BOSLA production source contract and fault injection tests.

A topic's selected source.pdf alone is authoritative. Extra PDFs can be
present in the source tree but are never downloaded, attached or incorporated.
The archived exact-three C3 evaluator is historical only, not a release gate.
"""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from app_generator.errors import RepositoryCompatibilityError, SourceAmbiguous
from app_generator.sources.google_drive import (
    DriveItem, PDF_MIME, discover_drive_sources_with_corpus_keys,
    discover_topic_corpus, topic_corpus_job_key,
)
from app_generator.sources.local_sources import inspect_sources
from app_generator.sources.manifest import build_manifest, load_existing_manifest
from app_generator.sources.production_source_policy import (
    one_configured_textbook_source, reject_multiple_authoritative_sources,
)
from tests.test_multi_pdf_corpus import FakeDrive


class BoslaOneTextbookSourceContractTests(unittest.TestCase):
    @staticmethod
    def _kwargs():
        return {
            "sourcepath": "root123456789",
            "pdf_subchapter_path": "8.2",
            "target_filename": "source.pdf",
            "max_folders": 20,
        }

    def test_drive_resolves_only_configured_authority_not_other_pdf(self):
        chosen = one_configured_textbook_source(
            discover_topic_corpus(FakeDrive(), **self._kwargs()),
            target_filename="source.pdf",
        )
        self.assertEqual([x.filename for x in chosen], ["source.pdf"])
        self.assertEqual([x.file_id for x in chosen], ["primaryfile123"])

    def test_auto_job_key_does_not_depend_on_question_bank_pdf(self):
        a = discover_drive_sources_with_corpus_keys(
            FakeDrive("bbb"), sourcepath="root123456789",
            target_filename="source.pdf", max_folders=20,
        )
        b = discover_drive_sources_with_corpus_keys(
            FakeDrive("ccc"), sourcepath="root123456789",
            target_filename="source.pdf", max_folders=20,
        )
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0].job_key, b[0].job_key)
        self.assertEqual(a[0].job_key, topic_corpus_job_key((a[0],)))

    def test_sibling_pdf_unavailable_or_aliased_does_not_block_textbook(self):
        drive = FakeDrive()
        drive.children["topic82folder"] += (
            DriveItem("unrelatedprivate", "EXTRA.PDF", PDF_MIME, can_download=False),
            DriveItem("aliasbankfile", "QUESTION-BANK.PDF", PDF_MIME),
        )
        inventory = discover_drive_sources_with_corpus_keys(
            drive, sourcepath="root123456789",
            target_filename="source.pdf", max_folders=20,
        )
        self.assertEqual([x.filename for x in inventory], ["source.pdf"])

    def test_missing_target_never_substitutes_sibling_pdf(self):
        with self.assertRaisesRegex(
            RepositoryCompatibilityError, "SOURCE_MISSING_NO_EXTERNAL_PDF_FALLBACK",
        ):
            one_configured_textbook_source(
                (SimpleNamespace(filename="outside.pdf"),),
                target_filename="source.pdf",
            )

    def test_duplicate_configured_target_is_not_selected_arbitrarily(self):
        with self.assertRaisesRegex(SourceAmbiguous, "DUPLICATE_PRIMARY_SOURCE"):
            one_configured_textbook_source((
                SimpleNamespace(filename="source.pdf"),
                SimpleNamespace(filename="SOURCE.PDF"),
            ), target_filename="source.pdf")

    def test_no_downloadable_primary_does_not_trigger_fallback(self):
        with self.assertRaisesRegex(
            RepositoryCompatibilityError, "PRIMARY_UNAVAILABLE_NO_EXTERNAL_PDF_FALLBACK",
        ):
            one_configured_textbook_source((
                SimpleNamespace(filename="source.pdf", can_download=False),
                SimpleNamespace(filename="unrelated.pdf", can_download=True),
            ), target_filename="source.pdf")

    def test_no_new_manifest_with_more_than_one_textbook(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            a, b = root / "source.pdf", root / "other.pdf"
            a.write_bytes(b"%PDF-a")
            b.write_bytes(b"%PDF-b")
            candidates = inspect_sources((a,b))
            config = SimpleNamespace(target_filename="source.pdf")
            with self.assertRaisesRegex(RepositoryCompatibilityError, "EXACTLY_ONE_SELECTED_PDF"):
                build_manifest(config, candidates)
            with self.assertRaisesRegex(RepositoryCompatibilityError, "EXACTLY_ONE_SELECTED_PDF"):
                reject_multiple_authoritative_sources(candidates)

    def test_single_manifest_and_legacy_multisource_manifest_rejection(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.pdf"
            source.write_bytes(b"%PDF-1.7 source content")
            record = inspect_sources((source,))[0]
            config = SimpleNamespace(
                target_filename="source.pdf", source_id="serway-8-2",
                edition="Serway textbook", chapter="8", subchapter="8.2",
                heading="Source only", page_range="all",
                learning_boundary="one textbook", reviewer="auto",
                rights_note="unadmitted", drive_file_id=None,
            )
            manifest = build_manifest(config, (record,))
            self.assertEqual(len(manifest["sources"]), 1)
            self.assertEqual(manifest["sources"][0]["role"], "primary")
            file = root / "manifest.json"
            file.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(load_existing_manifest(file, record, config), manifest)
            manifest["sources"].append({
                "controlledFilename": "unrelated.pdf", "sha256": "f"*64,
                "role": "supplementary",
            })
            file.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(RepositoryCompatibilityError, "EXISTING_MULTISOURCE_MANIFEST"):
                load_existing_manifest(file, record, config)


if __name__ == "__main__":
    unittest.main()
