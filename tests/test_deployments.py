import json
import tempfile
import unittest
from pathlib import Path

from app_generator.deployments import (
    deployment_rows,
    load_deployment_registry,
    render_deployments,
)
from app_generator.errors import ConfigurationError


class DeploymentRegistryTests(unittest.TestCase):
    def _write_package(self, root: Path, relative: str, package_id: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"packageId": package_id}), encoding="utf-8")

    def _write_registry(self, root: Path, deployments: list[dict[str, object]]) -> None:
        path = root / "config/deployments.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"schemaVersion": "1.0", "deployments": deployments}),
            encoding="utf-8",
        )

    def test_registered_deployment_reports_generated_and_public_url(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = "content/chapter-8/section-8-2/package.json"
            self._write_package(root, package, "chapter-8-section-8-2")
            self._write_registry(
                root,
                [{
                    "appId": "section-8-2",
                    "label": "Section 8.2",
                    "packagePath": package,
                    "deploymentRepository": "example/chapter-8",
                    "publicUrl": "https://example.github.io/chapter-8/section-8-2/",
                    "deployed": True,
                }],
            )

            rows = deployment_rows(root)

            self.assertEqual(1, len(rows))
            self.assertTrue(rows[0].generated)
            self.assertTrue(rows[0].deployed)
            self.assertEqual(
                "https://example.github.io/chapter-8/section-8-2/",
                rows[0].public_url,
            )

    def test_generated_unregistered_package_is_visible_as_not_deployed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_package(
                root,
                "content/chapter-9/section-9-1/package.json",
                "chapter-9-section-9-1",
            )
            self._write_registry(root, [])

            rows = deployment_rows(root)

            self.assertEqual(1, len(rows))
            self.assertEqual("chapter-9-section-9-1", rows[0].app_id)
            self.assertTrue(rows[0].generated)
            self.assertFalse(rows[0].deployed)
            self.assertEqual("", rows[0].public_url)

    def test_registered_missing_package_reports_not_generated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_registry(
                root,
                [{
                    "appId": "section-10-1",
                    "label": "Section 10.1",
                    "packagePath": "content/chapter-10/section-10-1/package.json",
                    "deploymentRepository": "example/chapter-10",
                    "publicUrl": "https://example.github.io/chapter-10/section-10-1/",
                    "deployed": True,
                }],
            )

            rows = deployment_rows(root)

            self.assertFalse(rows[0].generated)
            self.assertTrue(rows[0].deployed)

    def test_duplicate_app_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = {
                "appId": "section-8-2",
                "label": "Section 8.2",
                "packagePath": "content/chapter-8/section-8-2/package.json",
                "deploymentRepository": "example/chapter-8",
                "publicUrl": "https://example.github.io/chapter-8/section-8-2/",
                "deployed": True,
            }
            self._write_registry(root, [entry, entry])

            with self.assertRaisesRegex(ConfigurationError, "Duplicate deployment appId"):
                load_deployment_registry(root)

    def test_rendered_table_contains_status_and_url(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = "content/chapter-8/section-8-2/package.json"
            self._write_package(root, package, "chapter-8-section-8-2")
            self._write_registry(
                root,
                [{
                    "appId": "section-8-2",
                    "label": "Section 8.2",
                    "packagePath": package,
                    "deploymentRepository": "example/chapter-8",
                    "publicUrl": "https://example.github.io/chapter-8/section-8-2/",
                    "deployed": True,
                }],
            )

            output = render_deployments(deployment_rows(root))

            self.assertIn("APP", output)
            self.assertIn("GENERATED", output)
            self.assertIn("DEPLOYED", output)
            self.assertIn("Section 8.2", output)
            self.assertIn("https://example.github.io/chapter-8/section-8-2/", output)


if __name__ == "__main__":
    unittest.main()
