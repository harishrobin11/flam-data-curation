"""Deterministic exact and near-duplicate detection using word shingles."""

import re
from collections import defaultdict


SIMILARITY_THRESHOLD = 0.50


def word_shingles(text: str, size: int = 3) -> set[str]:
    """Return sets of consecutive word sequences."""
    words = re.findall(r"\w+", text.casefold(), flags=re.UNICODE)

    if not words:
        return set()

    if len(words) < size:
        return {" ".join(words)}

    return {
        " ".join(words[i:i + size])
        for i in range(len(words) - size + 1)
    }


def jaccard_similarity(left: set[str], right: set[str]) -> float:
    """Calculate Jaccard similarity between two shingle sets."""
    if not left or not right:
        return 0.0

    return len(left & right) / len(left | right)


class NearDuplicateIndex:
    """In-memory shingle index for a manageable corpus."""

    def __init__(self, threshold: float = SIMILARITY_THRESHOLD):
        self.threshold = threshold
        self.documents = {}
        self.inverted_index = defaultdict(set)

    def find_duplicate(self, text: str):
        shingles = word_shingles(text)

        if not shingles:
            return None

        candidates = set()
        for shingle in shingles:
            candidates.update(self.inverted_index[shingle])

        best_id = None
        best_score = 0.0

        for document_id in sorted(candidates):
            score = jaccard_similarity(
                shingles, self.documents[document_id]
            )
            if score > best_score:
                best_id = document_id
                best_score = score

        if best_id is not None and best_score >= self.threshold:
            return best_id, best_score

        return None

    def add(self, document_id: str, text: str):
        shingles = word_shingles(text)
        self.documents[document_id] = shingles

        for shingle in shingles:
            self.inverted_index[shingle].add(document_id)
