import unittest

from src.text_processing import normalize_text, classify_language
from src.redaction import redact_pii
from src.quality import quality_check
from src.deduplication import (
    NearDuplicateIndex,
    jaccard_similarity,
    word_shingles,
)


class TextProcessingTests(unittest.TestCase):
    def test_normalizes_unicode_and_whitespace(self):
        self.assertEqual(normalize_text("  नमस्ते   दुनिया  "), "नमस्ते दुनिया")

    def test_classifies_devanagari_hindi(self):
        self.assertEqual(classify_language("भारत एक सुंदर देश है"), "hi")

    def test_classifies_hinglish(self):
        self.assertEqual(classify_language("Aaj mausam bahut accha hai"), "hi-Latn")

    def test_classifies_english(self):
        self.assertEqual(
            classify_language("The weather is pleasant today"),
            "en",
        )

    def test_classifies_text_without_latin_or_devanagari(self):
        self.assertEqual(classify_language("12345 !!!"), "other")


class RedactionTests(unittest.TestCase):
    def test_redacts_email(self):
        self.assertIn("<EMAIL>", redact_pii("Contact robin@example.com"))

    def test_redacts_indian_phone(self):
        self.assertIn("<PHONE>", redact_pii("Call 9876543210"))

    def test_redacts_aadhaar_like_number(self):
        self.assertIn("<AADHAAR>", redact_pii("ID 1234 5678 9012"))

    def test_redacts_pan(self):
        self.assertIn("<PAN>", redact_pii("PAN ABCDE1234F"))

    def test_preserves_ordinary_number(self):
        self.assertEqual(redact_pii("Count 12345"), "Count 12345")


class QualityTests(unittest.TestCase):
    def test_rejects_empty_text(self):
        self.assertEqual(quality_check("   "), (False, "empty_text"))

    def test_rejects_short_text(self):
        self.assertEqual(quality_check("Short"), (False, "too_short"))

    def test_accepts_substantive_hindi_text(self):
        text = "भारत एक विविधता वाला देश है जहाँ अनेक भाषाएँ और संस्कृतियाँ हैं।"
        self.assertEqual(quality_check(text), (True, "passed"))


class DeduplicationTests(unittest.TestCase):
    def test_identical_text_has_full_similarity(self):
        shingles = word_shingles("one two three four")
        self.assertEqual(jaccard_similarity(shingles, shingles), 1.0)

    def test_finds_exact_duplicate(self):
        index = NearDuplicateIndex()
        text = "भारत एक सुंदर देश है और यहाँ अनेक भाषाएँ बोली जाती हैं"
        index.add("doc-1", text)
        match = index.find_duplicate(text)
        self.assertIsNotNone(match)
        self.assertEqual(match[0], "doc-1")
        self.assertAlmostEqual(match[1], 1.0)

    def test_rejects_invalid_threshold(self):
        with self.assertRaises(ValueError):
            NearDuplicateIndex(threshold=0)


if __name__ == "__main__":
    unittest.main()
