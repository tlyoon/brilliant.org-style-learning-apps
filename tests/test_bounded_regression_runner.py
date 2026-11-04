"""Bounded, fail-closed regression runner and timeout recovery tests."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
import tempfile
import unittest

from scripts.run_bounded_regression import run_suite


class BoundedRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def make_test(self, name, body):
        (self.root / name).write_text(
            "import unittest\n"
            "class Smoke(unittest.TestCase):\n"
            "    def test_case(self):\n" +
            "".join("        " + line + "\n" for line in body.splitlines()),
            encoding="utf-8"
        )

    def run_plan(self, **kw):
        output = StringIO()
        with redirect_stdout(output):
            result = run_suite(self.root, python=sys.executable, **kw)
        return result, output.getvalue()

    def test_isolation_and_bounded_failure_diagnostics(self):
        self.make_test("test_a_ok.py", "self.assertTrue(True)")
        self.make_test("test_b_fail.py", "self.assertEqual(1, 2)")
        result, log = self.run_plan(timeout_seconds=15)
        self.assertEqual(["PASS", "FAIL"], [x["status"] for x in result])
        self.assertEqual([1,1], [x["tests"] for x in result])
        self.assertNotIn("AssertionError", result[0]["diagnostic"])
        self.assertIn("AssertionError", result[1]["diagnostic"])
        self.assertIn("test_b_fail.py", log)

    def test_timeout_is_reported_and_next_module_runs(self):
        self.make_test("test_a_slow.py", "import time\n" "time.sleep(3)")
        self.make_test("test_b_ok.py", "self.assertTrue(True)")
        result, _ = self.run_plan(timeout_seconds=0.3)
        self.assertEqual(["TIMEOUT", "PASS"], [x["status"] for x in result])
        self.assertIsNone(result[0]["tests"])
        self.assertIn("test_case", result[0]["diagnostic"])

    def test_fail_fast_limit_and_input_validation(self):
        self.make_test("test_a_fail.py", "self.fail('expected')")
        self.make_test("test_b_ok.py", "self.assertTrue(True)")
        results, _ = self.run_plan(timeout_seconds=15, fail_fast=True)
        self.assertEqual(1, len(results))
        results, _ = self.run_plan(timeout_seconds=15, limit=1)
        self.assertEqual(1, len(results))
        with self.assertRaisesRegex(ValueError, "patterns"):
            self.run_plan(pattern="../*.py")
        with self.assertRaisesRegex(ValueError, "timeout"):
            self.run_plan(timeout_seconds=0)
        with self.assertRaisesRegex(ValueError, "limit"):
            self.run_plan(limit=0)

    def test_no_matching_tests_is_not_success(self):
        with self.assertRaisesRegex(ValueError, "no matching"):
            self.run_plan()


if __name__ == "__main__":
    unittest.main()
