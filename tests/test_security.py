import unittest

from perplexity_cli.security import sanitize_terminal_text


class TerminalSecurityTests(unittest.TestCase):
    def test_removes_ansi_and_osc_sequences(self) -> None:
        unsafe = "safe\x1b[31mred\x1b[0m\x1b]52;c;secret\x07\nnext"
        self.assertEqual(sanitize_terminal_text(unsafe), "safered\nnext")

    def test_preserves_tabs_and_newlines(self) -> None:
        self.assertEqual(sanitize_terminal_text("a\tb\nc"), "a\tb\nc")


if __name__ == "__main__":
    unittest.main()

