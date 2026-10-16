"""Text normalization and baseline language classification."""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """Normalize Unicode and remove invisible formatting characters."""
    text = unicodedata.normalize("NFC", text)
    text = "".join(
        char for char in text
        if unicodedata.category(char) != "Cf"
    )
    return re.sub(r"\s+", " ", text).strip()


def classify_language(text: str) -> str:
    """Classify text as hi, hi-Latn, en, or other using transparent heuristics."""
    devanagari = sum("\u0900" <= char <= "\u097F" for char in text)
    latin = sum(char.isascii() and char.isalpha() for char in text)

    if not devanagari and not latin:
        return "other"

    words = re.findall(r"[a-z]+", text.lower())

    hindi_words = {
        "hai", "hain", "tha", "thi", "ka", "ki", "ke", "ko",
        "mein", "nahi", "nahin", "aur", "kya", "aaj", "bahut",
        "accha", "achha", "mera", "meri", "tum", "aap", "hum",
        "kyunki", "lekin", "yaar",
    }
    english_words = {
        "the", "is", "are", "was", "were", "this", "that", "for",
        "with", "from", "have", "has", "been", "please", "more",
        "information", "about", "page", "content", "into", "other",
        "article", "topic", "their", "after", "which", "and", "or",
    }

    hindi_hits = sum(word in hindi_words for word in words)
    english_hits = sum(word in english_words for word in words)

    # For mixed-script text, use the Latin word evidence to distinguish
    # English-heavy content from Hindi written in Devanagari.
    if devanagari and latin:
        if english_hits >= 3 and english_hits > hindi_hits * 2:
            return "en"
        return "hi"

    if devanagari:
        return "hi"

    if hindi_hits >= 2 or (len(words) <= 5 and hindi_hits >= 1):
        return "hi-Latn"

    return "en"
