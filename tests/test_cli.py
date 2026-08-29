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


if __name__ == "__main__":
    unittest.main()