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
        self.assertEqual(1, code.count("BRILLIANT_WORKER_TOKEN"))
        self.assertIn("'project_name', 'job_key'", code)
        self.assertIn("requireProject_(request.project_name)", code)

    def test_initializer_generates_token_without_overwriting_one(self):
        code = self.code()
        self.assertIn("function initializeCoordinator()", code)
        self.assertIn("if (!properties.getProperty('WORKER_TOKEN'))", code)
        self.assertIn("Utilities.computeDigest", code)
        self.assertIn("Utilities.base64EncodeWebSafe", code)

    def test_exact_legacy_property_and_ledger_are_migrated(self):
        code = self.code()
        self.assertIn("'BRILLIANT_WORKER_TOKEN'", code)
        self.assertIn("const LEGACY_HEADERS = HEADERS.slice(1)", code)
        self.assertIn("function migrateLegacySheet_(sheet)", code)
        self.assertIn("sheet.insertColumnBefore(1)", code)

    def test_protocol_v4_replays_durable_request_receipts_under_the_script_lock(self):
        code = self.code()
        self.assertIn("const COORDINATOR_VERSION = 4", code)
        self.assertIn("const RECEIPT_LIMIT = 100", code)
        self.assertIn("function requestHash_(request)", code)
        self.assertIn("delete value.token", code)
        self.assertIn("function requestReceipt_(request)", code)
        self.assertIn("request_hash: requestHash_(request)", code)
        self.assertIn("function saveRequestReceipt_(request, result)", code)
        self.assertIn("function pruneRequestReceipts_(properties)", code)
        self.assertIn("const replay = requestReceipt_(request)", code)
        self.assertIn("saveRequestReceipt_(request, result)", code)
        self.assertIn("State-changing coordinator actions require a valid request_id", code)
        self.assertNotIn("token: request.token", code)

    def test_auto_mode_has_interrupted_priority_and_checkpoint_contract(self):
        code = self.code()
        self.assertIn("value.status = 'interrupted'", code)
        self.assertIn("value.status === 'interrupted'", code)
        self.assertIn("String(value.worker_id) !== String(workerId)", code)
        self.assertIn("const COORDINATOR_VERSION = 4", code)
        self.assertIn("coordinator_version: COORDINATOR_VERSION", code)
        self.assertIn("case 'snapshot'", code)
        self.assertIn("target_state: target ?", code)
        self.assertIn("attempt_count: Number(target.value.attempt_count", code)
        self.assertIn("error_code: String(target.value.error_code", code)
        self.assertIn("case 'generated'", code)
        self.assertIn("case 'checkpoint_save'", code)
        self.assertIn("case 'retry_failed'", code)
        self.assertIn("function retryFailed_(request)", code)
        self.assertIn("Only a terminally failed job can be retried explicitly", code)
        self.assertIn("value.attempt_count = 0", code)
        self.assertIn("'CHECKPOINT_FOLDER_ID'", code)
        self.assertIn("LockService.getScriptLock()", code)


if __name__ == "__main__":
    unittest.main()
