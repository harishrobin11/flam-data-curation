"""Deterministic exact and near-duplicate detection using word shingles."""

import math
import re
from collections import defaultdict
from functools import lru_cache


SIMILARITY_THRESHOLD = 0.50


@lru_cache(maxsize=8192)
def word_shingles(text: str, size: int = 3) -> frozenset[str]:
    """Return immutable sets of consecutive word sequences."""
    words = re.findall(r"\w+", text.casefold(), flags=re.UNICODE)

    if not words:
        return frozenset()

    if len(words) < size:
        return frozenset({" ".join(words)})

    return frozenset(
        " ".join(words[i:i + size])
        for i in range(len(words) - size + 1)
    )


def jaccard_similarity(left: set[str], right: set[str]) -> float:
    """Calculate Jaccard similarity between two shingle sets."""
    if not left or not right:
        return 0.0

    intersection = len(left & right)
    return intersection / (len(left) + len(right) - intersection)


class NearDuplicateIndex:
    """In-memory shingle index with overlap-based candidate pruning."""

    def __init__(self, threshold: float = SIMILARITY_THRESHOLD):
        if not 0 < threshold <= 1:
            raise ValueError("threshold must be in (0, 1]")

        self.threshold = threshold
        self.documents = {}
        self.document_sizes = {}
        self.inverted_index = defaultdict(set)
        self._required_overlap_cache = {}

    def _required_overlap(self, query_size: int, document_size: int) -> int:
        """Minimum overlap needed to meet the Jaccard threshold."""
        key = (query_size, document_size)
        result = self._required_overlap_cache.get(key)
        if result is None:
            result = math.ceil(
                self.threshold * (query_size + document_size)
                / (1 + self.threshold)
            )
            self._required_overlap_cache[key] = result
        return result

    def find_duplicate(self, text: str):
        shingles = word_shingles(text)

        if not shingles:
            return None

        overlap_counts = defaultdict(int)
        for shingle in shingles:
            for document_id in self.inverted_index.get(shingle, ()):
                overlap_counts[document_id] += 1

        query_size = len(shingles)
        best_id = None
        best_score = 0.0

        for document_id, overlap in overlap_counts.items():
            document_size = self.document_sizes[document_id]

            if overlap < self._required_overlap(query_size, document_size):
                continue

            score = overlap / (query_size + document_size - overlap)

            if score > best_score or (
                score == best_score
                and (best_id is None or document_id < best_id)
            ):
                best_id = document_id
                best_score = score

        if best_id is not None and best_score >= self.threshold:
            return best_id, best_score

        return None

    def add(self, document_id: str, text: str):
        shingles = word_shingles(text)
        self.documents[document_id] = shingles
        self.document_sizes[document_id] = len(shingles)

        for shingle in shingles:
            self.inverted_index[shingle].add(document_id)
