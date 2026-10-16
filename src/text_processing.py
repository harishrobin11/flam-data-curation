"""Text normalization and baseline language classification."""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """Normalize Unicode and remove invisible formatting characters."""
    text = unicodedata.normalize("NFC", text)

    # Remove common invisible formatting characters, but preserve
    # meaningful Unicode letters, combining marks, and punctuation.
    text = "".join(
        char for char in text
        if unicodedata.category(char) != "Cf"
    )

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text).strip()
    return text


def classify_language(text: str) -> str:
    """Return a baseline label: hi, hi-Latn, en, or other.

    This is a transparent heuristic, not a production-grade
    language-identification model.
    """
    devanagari = sum(
        "\u0900" <= char <= "\u097F" for char in text
    )
    latin = sum(
        ("a" <= char.lower() <= "z") for char in text
    )

    if devanagari:
        return "hi"

    if not latin:
        return "other"

    words = re.findall(r"[a-z]+", text.lower())

    # Small baseline vocabulary for testing only. We will improve
    # this using corpus inspection and measured validation results.
    hindi_words = {
        "hai", "hain",  "tha", "thi",
        "ka", "ki", "ke", "ko", "mein", "nahi",
        "nahin", "aur", "kya", "aaj", "bahut",
        "accha", "achha", "mera", "meri", "tum",
        "aap", "hum", "kyunki", "lekin", "yaar",
    }

    hindi_hits = sum(word in hindi_words for word in words)

    if hindi_hits >= 2 or (
        len(words) <= 5 and hindi_hits >= 1
    ):
        return "hi-Latn"

    return "en"
