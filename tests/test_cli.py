import os
import unittest
from unittest.mock import patch

from perplexity_cli.cli import build_parser, run


class CliTests(unittest.TestCase):
    def test_default_model_is_the_cheaper_sonar_model(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(build_parser().parse_args([]).model, "sonar")

    def test_rejects_non_positive_timeout(self) -> None:
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["--timeout", "0"])

    def test_reports_missing_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(run(["question"]), 1)


if __name__ == "__main__":
    unittest.main()

