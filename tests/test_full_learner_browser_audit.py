"""Source-free regression checks for bounded private learner-browser QA."""
import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from scripts.audit_full_learner_browser import (
    _localized, _select_fresh_locale, audit_existing_candidate, ROOT,
)


class LearnerBrowserAuditTests(TestCase):
    def test_each_locale_reloads_the_page_before_interaction(self):
        driver = Mock()
        with patch("selenium.webdriver.support.ui.Select") as select:
            for language in ("en", "ms", "zh"):
                _select_fresh_locale(driver, "http://127.0.0.1:1234",
                                     "synthetic-select", language)
        self.assertEqual(driver.get.call_count, 3)
        self.assertEqual(
            [call.args[0] for call in driver.get.call_args_list],
            ["http://127.0.0.1:1234/index.html?activity=synthetic-select"] * 3,
        )
        self.assertEqual(
            [call.args[0] for call in
             select.return_value.select_by_value.call_args_list],
            ["en", "ms", "zh"],
        )

    def test_localization_does_not_fabricate_missing_language(self):
        self.assertEqual(_localized({"en": "A", "ms": "B"}, "zh"), "")
        self.assertEqual(_localized({"en": " A "}, "en"), "A")

    def test_reject_repository_output_before_browser(self):
        package = ROOT / "tests" / "fixtures" / "learner_browser_selection.json"
        with patch("selenium.webdriver.Chrome") as chrome:
            with self.assertRaises(ValueError):
                audit_existing_candidate(package, ROOT)
        chrome.assert_not_called()

    def test_exact_package_one_shot_refuses_prior_receipt(self):
        package = ROOT / "tests" / "fixtures" / "learner_browser_selection.json"
        from hashlib import sha256
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            destination = output / (
                "learner-browser-" + sha256(package.read_bytes()).hexdigest()[:16])
            destination.mkdir()
            with patch("selenium.webdriver.Chrome") as chrome:
                with self.assertRaises(FileExistsError):
                    audit_existing_candidate(package, output)
            chrome.assert_not_called()
