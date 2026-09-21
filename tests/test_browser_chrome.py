import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from app_generator.browser.chrome import ChromeSession, GEMINI_HOME, chrome_executable, ready_debug_address
from app_generator.errors import BrowserError


class ChromeSessionTests(unittest.TestCase):
    def config(self, root, mode="controlled"):
        return SimpleNamespace(
            browser_mode=mode,
            chrome_profile_dir=Path(root),
            debugger_address="127.0.0.1:9222",
            login_name="operator@example.com",
            gem_url="https://gemini.google.com/gem/demo",
            gem_edit_url="https://gemini.google.com/gems/edit/demo",
        )

    def test_controlled_opens_regular_gemini_window_before_driver_connection(self):
        with tempfile.TemporaryDirectory() as root:
            config = self.config(root)
            with patch("app_generator.browser.chrome.chrome_executable", return_value="chrome.exe"), \
                 patch("app_generator.browser.chrome.subprocess.Popen") as launch, \
                 patch("app_generator.browser.chrome.ready_debug_address", return_value="127.0.0.1:54321"), \
                 patch("selenium.webdriver.Chrome") as chrome:
                events = []
                launch.side_effect = lambda *a, **kw: events.append("window")
                chrome.side_effect = lambda **kw: events.append("driver") or Mock()
                session = ChromeSession(config)
                driver = session.start()
                self.assertEqual(["window", "driver"], events)
                args = launch.call_args.args[0]
                self.assertIn(config.gem_url, args)
                self.assertNotIn(config.gem_edit_url, args)
                self.assertIn("--new-window", args)
                self.assertIn("--remote-debugging-port=0", args)
                self.assertIn("--remote-debugging-address=127.0.0.1", args)
                self.assertIn(f"--user-data-dir={Path(root) / 'gemini-browser'}", args)
                self.assertNotIn("--enable-automation", args)
                self.assertEqual("127.0.0.1:54321", chrome.call_args.kwargs["options"].debugger_address)
                session.close()
                driver.execute_cdp_cmd.assert_called_once_with("Browser.close", {})
                driver.quit.assert_called_once_with()

    def test_manual_sign_in_window_has_no_debugging_before_automation_relaunch(self):
        manual_process = Mock()
        manual_process.poll.return_value = 0
        with tempfile.TemporaryDirectory() as root, \
             patch("app_generator.browser.chrome.chrome_executable", return_value="chrome.exe"), \
             patch("app_generator.browser.chrome.subprocess.Popen", side_effect=[manual_process, Mock()]) as launch, \
             patch("app_generator.browser.chrome.ready_debug_address", return_value="127.0.0.1:54321"), \
             patch("builtins.input", return_value=""), \
             patch("selenium.webdriver.Chrome") as chrome:
            session = ChromeSession(self.config(root))
            self.assertEqual("", session.open_window())
            manual_args = launch.call_args_list[0].args[0]
            self.assertNotIn("--remote-debugging-port=0", manual_args)
            self.assertNotIn("--remote-debugging-address=127.0.0.1", manual_args)
            self.assertIn(self.config(root).gem_url, manual_args)
            chrome.assert_not_called()
            session.wait_for_manual_sign_in()
            session.start()
            automation_args = launch.call_args_list[1].args[0]
            self.assertIn("--remote-debugging-port=0", automation_args)
            self.assertIn("--remote-debugging-address=127.0.0.1", automation_args)
            self.assertEqual(2, launch.call_count)
            session.close()

    def test_manual_sign_in_prompt_names_default_account_and_both_gem_urls(self):
        with tempfile.TemporaryDirectory() as root, \
             patch("builtins.input", return_value="") as prompt, \
             patch("builtins.print") as output:
            session = ChromeSession(self.config(root))
            session.wait_for_manual_sign_in()
            prompt.assert_called_once()
            message = output.call_args.args[0]
            self.assertIn("operator@example.com", message)
            self.assertIn("https://gemini.google.com/gem/demo", message)
            self.assertIn("https://gemini.google.com/gems/edit/demo", message)
            self.assertIn("close that Chrome window", message)

    def test_sign_in_window_must_close_before_automation(self):
        process = Mock()
        process.poll.return_value = None
        with tempfile.TemporaryDirectory() as root, \
             patch("builtins.input", return_value=""), \
             patch("app_generator.browser.chrome.time.monotonic", side_effect=[0, 16]):
            session = ChromeSession(self.config(root), _manual_process=process)
            with self.assertRaisesRegex(BrowserError, "still running"):
                session.wait_for_manual_sign_in()

    def test_non_interactive_sign_in_prompt_is_actionable(self):
        with tempfile.TemporaryDirectory() as root, patch("builtins.input", side_effect=EOFError):
            with self.assertRaisesRegex(BrowserError, "interactive terminal"):
                ChromeSession(self.config(root)).wait_for_manual_sign_in()

    def test_attach_sign_in_prompt_is_skipped(self):
        with tempfile.TemporaryDirectory() as root, patch("builtins.input") as prompt:
            ChromeSession(self.config(root, "attach")).wait_for_manual_sign_in()
            prompt.assert_not_called()

    def test_attach_never_launches_or_closes_existing_browser(self):
        with tempfile.TemporaryDirectory() as root, \
             patch("app_generator.browser.chrome.subprocess.Popen") as launch, \
             patch("selenium.webdriver.Chrome") as chrome:
            session = ChromeSession(self.config(root, "attach"))
            session.start()
            self.assertEqual("127.0.0.1:9222", chrome.call_args.kwargs["options"].debugger_address)
            session.close()
            launch.assert_not_called()
            chrome.return_value.quit.assert_not_called()
            chrome.return_value.execute_cdp_cmd.assert_not_called()
            chrome.return_value.service.stop.assert_called_once_with()

    def test_readiness_timeout_does_not_attempt_old_debug_session(self):
        with tempfile.TemporaryDirectory() as root, \
             patch("app_generator.browser.chrome.chrome_executable", return_value="chrome.exe"), \
             patch("app_generator.browser.chrome.subprocess.Popen"), \
             patch("app_generator.browser.chrome.time.monotonic", side_effect=[0, 16]), \
             patch("selenium.webdriver.Chrome") as chrome:
            with self.assertRaisesRegex(BrowserError, "15 seconds"):
                ChromeSession(self.config(root)).start()
            chrome.assert_not_called()

    def test_launch_failure_is_actionable(self):
        with tempfile.TemporaryDirectory() as root, \
             patch("app_generator.browser.chrome.chrome_executable", return_value="chrome.exe"), \
             patch("app_generator.browser.chrome.subprocess.Popen", side_effect=OSError("unavailable")):
            with self.assertRaisesRegex(BrowserError, "could not be launched"):
                ChromeSession(self.config(root)).open_window()

    def test_missing_chrome_is_actionable(self):
        with patch("app_generator.browser.chrome.shutil.which", return_value=None), \
             patch("app_generator.browser.chrome.Path.is_file", return_value=False):
            with self.assertRaisesRegex(BrowserError, "Chrome was not found"):
                chrome_executable()

    def debug_profile(self):
        profile = MagicMock()
        (profile / "DevToolsActivePort").read_text.return_value = "54321\n/devtools/browser/expected\n"
        return profile

    def test_debug_metadata_requires_matching_endpoint_and_page(self):
        profile = self.debug_profile()
        version = {"webSocketDebuggerUrl": "ws://127.0.0.1:54321/devtools/browser/expected"}
        with patch("app_generator.browser.chrome.urlopen", side_effect=[
            io.StringIO(json.dumps(version)), io.StringIO('[{"type":"page"}]'),
        ]):
            self.assertEqual("127.0.0.1:54321", ready_debug_address(profile))

    def test_stale_debug_endpoint_is_rejected(self):
        profile = self.debug_profile()
        version = {"webSocketDebuggerUrl": "ws://127.0.0.1:54321/devtools/browser/other"}
        with patch("app_generator.browser.chrome.urlopen", return_value=io.StringIO(json.dumps(version))):
            with self.assertRaisesRegex(ValueError, "does not match"):
                ready_debug_address(profile)

    def test_debug_browser_without_pages_is_rejected(self):
        profile = self.debug_profile()
        version = {"webSocketDebuggerUrl": "ws://127.0.0.1:54321/devtools/browser/expected"}
        with patch("app_generator.browser.chrome.urlopen", side_effect=[
            io.StringIO(json.dumps(version)), io.StringIO('[{"type":"service_worker"}]'),
        ]):
            with self.assertRaisesRegex(ValueError, "no page"):
                ready_debug_address(profile)


if __name__ == "__main__":
    unittest.main()
