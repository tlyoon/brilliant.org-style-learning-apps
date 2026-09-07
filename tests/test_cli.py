import unittest
from pathlib import Path

from app_generator.cli import DEFAULT_CONFIG, _parser


class CliParserTests(unittest.TestCase):
    def test_config_defaults_to_project_local_toml(self):
        args = _parser().parse_args(["run"])

        self.assertEqual(args.config, DEFAULT_CONFIG)
        self.assertEqual(args.config, Path("project.local.toml"))

    def test_explicit_config_overrides_default(self):
        config = Path("configs/custom.toml")

        args = _parser().parse_args(["run", "--config", str(config)])

        self.assertEqual(args.config, config)

    def test_auto_selection_mode_is_exposed(self):
        args = _parser().parse_args(["run", "--selection-mode", "auto"])
        self.assertEqual("auto", args.selection_mode)

    def test_auto_can_accept_explicit_target_subchapter(self):
        args = _parser().parse_args([
            "run",
            "--selection-mode",
            "auto",
            "--pdf-subchapter-path",
            "8.6",
        ])
        self.assertEqual("auto", args.selection_mode)
        self.assertEqual("8.6", args.pdf_subchapter_path)


if __name__ == "__main__":
    unittest.main()
