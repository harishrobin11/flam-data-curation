
"""Redact common Indian personal identifiers from text."""

import re


PATTERNS = [
    # Aadhaar: 12 digits, optionally separated into groups.
    (
        "AADHAAR",
        re.compile(r"(?<!\d)(?:\d{4}[ -]?){2}\d{4}(?!\d)"),
    ),
    # Indian PAN: five letters, four digits, one letter.
    (
        "PAN",
        re.compile(r"(?<![A-Z0-9])[A-Z]{5}\d{4}[A-Z](?![A-Z0-9])", re.I),
    ),
    # Email addresses.
    (
        "EMAIL",
        re.compile(
            r"(?i)(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+"
        ),
    ),
    # Indian mobile numbers with optional +91 / 0 prefix.
    (
        "PHONE",
        re.compile(
            r"(?<!\d)(?:\+?91[\s-]?)?(?:0[\s-]?)?[6-9]\d{9}(?!\d)"
        ),
    ),
]


def redact_pii(text: str) -> str:
    """Replace detected identifiers with the required placeholders."""
    for label, pattern in PATTERNS:
        text = pattern.sub(f"<{label}>", text)
    return text
