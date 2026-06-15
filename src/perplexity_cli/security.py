import re


_TERMINAL_CONTROL_SEQUENCE = re.compile(
    r"(?:\x1B\][^\x07]*(?:\x07|\x1B\\))"
    r"|(?:\x1B\[[0-?]*[ -/]*[@-~])"
    r"|[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"
)


def sanitize_terminal_text(value: object) -> str:
    """Remove terminal control sequences while preserving newlines and tabs."""
    return _TERMINAL_CONTROL_SEQUENCE.sub("", str(value))

