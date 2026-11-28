"""BSA283: original PDF is NOT LaTeX; digest-safe page extraction reuse."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import subprocess

from app_generator.validation import source_passages as passages


class OriginalTextbookExtractionTests(TestCase):
    def test_identical_original_is_reused_without_another_pdftotext_process(self):
        with TemporaryDirectory() as t:
            source=Path(t)/"source.pdf"
            source.write_bytes(b"%PDF-1.7\noriginal Serway one textbook\n")
            out=subprocess.CompletedProcess([],0,
                b"first textbook page\fsecond textbook page\f",b"")
            with patch.object(passages.subprocess,"run",return_value=out) as run:
                first=passages.extract_pages(source)
                second=passages.extract_pages(source)
            self.assertEqual(first,("first textbook page","second textbook page"))
            self.assertEqual(first,second)
            run.assert_called_once()
            args=run.call_args.args[0]
            self.assertEqual(args[0],"pdftotext")
            self.assertNotIn("pdflatex",args)

    def test_changed_pdf_digest_forces_new_original_extraction(self):
        with TemporaryDirectory() as t:
            source=Path(t)/"source.pdf"
            source.write_bytes(b"%PDF-1.7\nOriginal textbook revision A")
            with patch.object(passages.subprocess,"run",
                              side_effect=[
                    subprocess.CompletedProcess([],0,b"page A\f",b""),
                    subprocess.CompletedProcess([],0,b"page B\f",b""),
                              ]) as run:
                self.assertEqual(passages.extract_pages(source),("page A",))
                source.write_bytes(b"%PDF-1.7\nModified textbook revision B")
                self.assertEqual(passages.extract_pages(source),("page B",))
                self.assertEqual(run.call_count,2)

    def test_change_during_extraction_is_rejected_not_cached(self):
        with TemporaryDirectory() as t:
            source=Path(t)/"source.pdf"
            source.write_bytes(b"%PDF-1.7\noriginal\n")
            def mutate(args,**kwargs):
                source.write_bytes(b"%PDF-1.7\nreplaced midway\n")
                return subprocess.CompletedProcess(args,0,b"stale\n",b"")
            with patch.object(passages.subprocess,"run",side_effect=mutate):
                with self.assertRaisesRegex(
                        ValueError,"CHANGED_DURING_TEXT_EXTRACTION"):
                    passages.extract_pages(source)

    def test_tool_error_does_not_create_persistent_false_cache(self):
        with TemporaryDirectory() as t:
            source=Path(t)/"source.pdf"
            source.write_bytes(b"%PDF-1.7\noriginal unchanging\n")
            with patch.object(passages.subprocess,"run",
                              side_effect=[
                    subprocess.CompletedProcess([],1,b"",b"bad"),
                    subprocess.CompletedProcess([],0,b"success\f",b""),
                              ]) as run:
                with self.assertRaisesRegex(ValueError,"extraction failed"):
                    passages.extract_pages(source)
                self.assertEqual(passages.extract_pages(source),("success",))
                self.assertEqual(run.call_count,2)

    def test_non_pdf_never_runs_extractor_or_latex(self):
        with TemporaryDirectory() as t:
            source=Path(t)/"source.pdf"
            source.write_bytes(b"not a PDF at all")
            with patch.object(passages.subprocess,"run") as run:
                with self.assertRaisesRegex(ValueError,"not a PDF"):
                    passages.extract_pages(source)
                run.assert_not_called()

    def test_no_semantic_or_publication_pass_from_cached_pages(self):
        with TemporaryDirectory() as t:
            source=Path(t)/"source.pdf"
            source.write_bytes(b"%PDF-1.7\nsource text only")
            with patch.object(passages.subprocess,"run",return_value=
                              subprocess.CompletedProcess([],0,b"only text\f",b"")):
                self.assertEqual(passages.extract_pages(source),("only text",))
            self.assertFalse(hasattr(passages,"academicPASS"))
            self.assertFalse(hasattr(passages,"publicationAuthorized"))
