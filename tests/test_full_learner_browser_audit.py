"""Source-free regression checks for bounded private learner-browser QA."""
import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from scripts.audit_full_learner_browser import (
    _localized, _select_fresh_locale, _safe_failure_origin,
    audit_existing_candidate, ROOT,
)


class LearnerBrowserAuditTests(TestCase):
    def test_browser_error_origin_is_sanitized_and_keeps_call_site(self):
        try:
            raise NotImplementedError("DO_NOT_LOG_PRIVATE_SOURCE_OR_SESSION_TOKEN")
        except NotImplementedError as exc:
            result = _safe_failure_origin(exc)
        self.assertEqual("test_full_learner_browser_audit.py",
                         result["originModule"])
        self.assertEqual("test_browser_error_origin_is_sanitized_and_keeps_call_site",
                         result["originFunction"])
        self.assertNotIn("DO_NOT_LOG_PRIVATE", str(result))
        self.assertEqual({"originModule", "originFunction"}, set(result))

    def test_locale_select_waits_for_enabled_and_loaded_question(self):
        driver = Mock()
        element = driver.find_element.return_value
        element.is_enabled.side_effect = [False, True, True]
        driver.find_elements.side_effect = [[], [Mock()]]
        with patch("selenium.webdriver.support.ui.Select") as select:
            _select_fresh_locale(driver, "http://127.0.0.1:1234",
                                 "test-activity", "ms")
        self.assertEqual(3, element.is_enabled.call_count)
        self.assertEqual(2, driver.find_elements.call_count)
        select.return_value.select_by_value.assert_called_once_with("ms")

    def test_locale_select_refuses_disabled_or_unloaded_state(self):
        from selenium.common.exceptions import TimeoutException
        driver = Mock()
        with patch("selenium.webdriver.support.ui.WebDriverWait") as wait:
            wait.return_value.until.side_effect = TimeoutException()
            with patch("selenium.webdriver.support.ui.Select") as select:
                with self.assertRaises(TimeoutException):
                    _select_fresh_locale(driver, "http://127.0.0.1:1234",
                                         "test-activity", "zh")
        select.assert_not_called()

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


class BrowserViewportGuardTests(TestCase):
    """A requested mobile label cannot mask a desktop-size screenshot."""

    def test_cdp_enforces_requested_css_viewport_before_navigation(self):
        from scripts.audit_full_learner_browser import _set_exact_viewport
        driver = Mock()
        _set_exact_viewport(driver, 390, 844)
        driver.set_window_size.assert_called_once_with(390, 844)
        driver.execute_cdp_cmd.assert_called_once_with(
            "Emulation.setDeviceMetricsOverride",
            {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True},
        )
        desktop = Mock()
        _set_exact_viewport(desktop, 1280, 800)
        self.assertFalse(desktop.execute_cdp_cmd.call_args.args[1]["mobile"])

    def test_wrong_actual_css_viewport_fails_closed(self):
        from scripts.audit_full_learner_browser import _assert_exact_viewport
        driver = Mock()
        driver.execute_script.return_value = [504, 692, 1]
        with self.assertRaisesRegex(ValueError, "REQUESTED_VIEWPORT_NOT_EXERCISED"):
            _assert_exact_viewport(driver, 390, 844)
        driver.execute_script.return_value = [390, 844, 1]
        _assert_exact_viewport(driver, 390, 844)

    def test_mislabeled_historical_png_width_is_rejected(self):
        from scripts.audit_full_learner_browser import _assert_screenshot_viewport
        import struct
        def png_header(w, h):
            return (
                b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR"
                + struct.pack(">II", w, h)
            )
        with self.assertRaisesRegex(ValueError, "SCREENSHOT_VIEWPORT_DIMENSIONS_MISMATCH"):
            _assert_screenshot_viewport(png_header(504, 692), 390, 844)
        with self.assertRaisesRegex(ValueError, "SCREENSHOT_VIEWPORT_DIMENSIONS_MISMATCH"):
            _assert_screenshot_viewport(png_header(1262, 648), 1280, 800)
        _assert_screenshot_viewport(png_header(390, 844), 390, 844)
