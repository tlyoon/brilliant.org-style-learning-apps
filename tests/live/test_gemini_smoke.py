"""Opt-in live test. Never runs during ordinary unit-test discovery without explicit environment opt-in."""

import os
import unittest


@unittest.skipUnless(os.environ.get("BRILLIANT_GENERATOR_LIVE_TEST") == "1", "live Gemini test is opt-in")
class GeminiLiveSmokeTest(unittest.TestCase):
    def test_live_flow_is_invoked_through_cli(self):
        self.skipTest("Run `python -m app_generator run --config <local.toml>` for the controlled live flow")


if __name__ == "__main__":
    unittest.main()
