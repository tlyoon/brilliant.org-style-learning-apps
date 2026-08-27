import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CoordinatorAppsScriptTests(unittest.TestCase):
    def code(self) -> str:
        return (ROOT / "coordinator" / "apps-script" / "Code.gs").read_text(encoding="utf-8")

    def test_coordinator_uses_generic_project_scoped_properties(self):
        code = self.code()
        self.assertIn("'PROJECT_NAME'", code)
        self.assertIn("'WORKER_TOKEN'", code)
        self.assertNotIn("BRILLIANT_WORKER_TOKEN", code)
        self.assertIn("'project_name', 'job_key'", code)
        self.assertIn("requireProject_(request.project_name)", code)

    def test_initializer_generates_token_without_overwriting_one(self):
        code = self.code()
        self.assertIn("function initializeCoordinator()", code)
        self.assertIn("if (!properties.getProperty('WORKER_TOKEN'))", code)
        self.assertIn("Utilities.computeDigest", code)
        self.assertIn("Utilities.base64EncodeWebSafe", code)


if __name__ == "__main__":
    unittest.main()
