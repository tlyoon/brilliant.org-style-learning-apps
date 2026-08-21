import hashlib
import tempfile
import unittest
from pathlib import Path

from app_generator.errors import SourceSetMismatch
from app_generator.sources.local_sources import inspect_sources


class GeneratorSourceTests(unittest.TestCase):
    def test_checksum_is_calculated_from_local_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.pdf"
            path.write_bytes(b"synthetic controlled PDF bytes")
            source = inspect_sources((path,))[0]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), source.sha256)

    def test_duplicate_controlled_filenames_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "one" / "source.pdf"
            second = root / "two" / "source.pdf"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_bytes(b"one")
            second.write_bytes(b"two")
            with self.assertRaises(SourceSetMismatch):
                inspect_sources((first, second))


if __name__ == "__main__":
    unittest.main()
