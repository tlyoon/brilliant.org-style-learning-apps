import tempfile
import unittest
from pathlib import Path

from app_generator.errors import SourceAmbiguous, SourceDownloadError, SourceNotFound
from app_generator.sources.google_drive import (
    FOLDER_MIME,
    PDF_MIME,
    DriveItem,
    DriveRestClient,
    ResolvedDriveSource,
    discover_drive_sources,
    extract_drive_folder_id,
    resolve_drive_source,
)


class FakeDriveClient:
    def __init__(self, children):
        self.children = children

    def get_item(self, file_id):
        return DriveItem(file_id, "Serway", FOLDER_MIME)

    def list_children(self, folder_id):
        return tuple(self.children.get(folder_id, ()))


class FakeResponse:
    def __init__(self, content=b"%PDF-synthetic"):
        self.content = content

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size):
        del chunk_size
        yield self.content


class FakeSession:
    def __init__(self, content=b"%PDF-synthetic"):
        self.response = FakeResponse(content)

    def get(self, *args, **kwargs):
        del args, kwargs
        return self.response


class GeneratorGoogleDriveTests(unittest.TestCase):
    def tree(self, duplicate=False):
        children = {
            "root-folder-id": (
                DriveItem("group-eight-id", "Serway_8_14", FOLDER_MIME),
                DriveItem("group-eighteen-id", "Serway_18_21", FOLDER_MIME),
            ),
            "group-eight-id": (DriveItem("chapter-eight-id", "8", FOLDER_MIME),),
            "chapter-eight-id": (DriveItem("section-eight-one-id", "8.1", FOLDER_MIME),),
            "section-eight-one-id": (
                DriveItem("pdf-eight-one-id", "source.pdf", PDF_MIME, 14, True, "abc"),
            ),
            "group-eighteen-id": (DriveItem("chapter-eighteen-id", "18", FOLDER_MIME),),
            "chapter-eighteen-id": (DriveItem("section-eighteen-one-id", "18.1", FOLDER_MIME),),
            "section-eighteen-one-id": (
                DriveItem("pdf-eighteen-one-id", "source.pdf", PDF_MIME, 20, True, "def"),
            ),
        }
        if duplicate:
            children["root-folder-id"] += (DriveItem("other-eight-one-id", "8.1", FOLDER_MIME),)
            children["other-eight-one-id"] = (
                DriveItem("other-pdf-id", "source.pdf", PDF_MIME, 14, True, "ghi"),
            )
        return children

    def test_drive_link_forms_extract_the_same_folder_id(self):
        expected = "1BqdcGJR3usQvItCNMC997fkcXaScNYqc"
        self.assertEqual(expected, extract_drive_folder_id(f"https://drive.google.com/open?id={expected}"))
        self.assertEqual(expected, extract_drive_folder_id(f"https://drive.google.com/drive/folders/{expected}"))

    def test_recursive_resolution_matches_an_exact_folder_component(self):
        source = resolve_drive_source(
            FakeDriveClient(self.tree()),
            sourcepath="root-folder-id",
            pdf_subchapter_path="8.1",
            target_filename="source.pdf",
            max_folders=100,
        )
        self.assertEqual("pdf-eight-one-id", source.file_id)
        self.assertEqual("Serway_8_14/8/8.1/source.pdf", source.relative_path)
        self.assertEqual("8.1", source.subchapter_id)

    def test_discovery_returns_all_subchapters_in_numeric_order(self):
        sources = discover_drive_sources(
            FakeDriveClient(self.tree()),
            sourcepath="root-folder-id",
            target_filename="source.pdf",
            max_folders=100,
        )
        self.assertEqual(["8.1", "18.1"], [source.subchapter_id for source in sources])
        self.assertNotEqual(sources[0].job_key, sources[1].job_key)

    def test_duplicate_and_missing_sources_stop_safely(self):
        with self.assertRaises(SourceAmbiguous):
            resolve_drive_source(
                FakeDriveClient(self.tree(duplicate=True)),
                sourcepath="root-folder-id",
                pdf_subchapter_path="8.1",
                target_filename="source.pdf",
                max_folders=100,
            )
        with self.assertLogs("app_generator.sources.google_drive", level="WARNING"):
            with self.assertRaises(SourceNotFound):
                resolve_drive_source(
                    FakeDriveClient(self.tree()),
                    sourcepath="root-folder-id",
                    pdf_subchapter_path="9.9",
                    target_filename="source.pdf",
                    max_folders=100,
                )

    def test_download_is_atomic_and_checks_pdf_signature(self):
        source = ResolvedDriveSource(
            "pdf-id-value",
            "source.pdf",
            "8/8.1/source.pdf",
            PDF_MIME,
            14,
            None,
            "8.1",
        )
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "source.pdf"
            DriveRestClient(FakeSession(), 1).download_file(source, destination)
            self.assertEqual(b"%PDF-synthetic", destination.read_bytes())
            with self.assertRaises(SourceDownloadError):
                DriveRestClient(FakeSession(b"not a PDF file"), 1).download_file(
                    ResolvedDriveSource("pdf-id-value", "source.pdf", "8/8.1/source.pdf", PDF_MIME, 14, None, "8.1"),
                    destination,
                )


if __name__ == "__main__":
    unittest.main()
