
"""Basic, script-aware quality checks for text documents."""

import re
import unicodedata


def quality_check(text: str) -> tuple[bool, str]:
    """Return (keep, reason) for a text document."""

    text = text.strip()

    if not text:
        return False, "empty_text"

    if len(text) < 20:
        return False, "too_short"

    # Count Unicode letters, including letters from Indic scripts.
    letters = sum(
        unicodedata.category(char).startswith("L")
        for char in text
    )

    # Ignore whitespace and punctuation when assessing content.
    meaningful = sum(
        not char.isspace()
        and unicodedata.category(char)[0] not in {"P", "S"}
        for char in text
    )

    if meaningful == 0 or letters / meaningful < 0.50:
        return False, "low_letter_ratio"

    # Reject obvious repeated-character spam.
    if re.search(r"(.)\1{9,}", text):
        return False, "repeated_character_spam"

    # Reject text containing Unicode replacement characters.
    if "\ufffd" in text:
        return False, "replacement_character_present"

    return True, "passed"
