"""Deterministic exact and near-duplicate detection using word shingles."""

import math
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

    intersection = len(left & right)
    return intersection / (len(left) + len(right) - intersection)


class NearDuplicateIndex:
    """In-memory shingle index with overlap-based candidate pruning."""

    def __init__(self, threshold: float = SIMILARITY_THRESHOLD):
        if not 0 < threshold <= 1:
            raise ValueError("threshold must be in (0, 1]")

        self.threshold = threshold
        self.documents = {}
        self.inverted_index = defaultdict(set)

    def find_duplicate(self, text: str):
        shingles = word_shingles(text)

        if not shingles:
            return None

        # Count shared shingles without repeatedly constructing set unions.
        overlap_counts = defaultdict(int)
        for shingle in shingles:
            for document_id in self.inverted_index.get(shingle, ()):
                overlap_counts[document_id] += 1

        query_size = len(shingles)
        best_id = None
        best_score = 0.0

        for document_id, overlap in overlap_counts.items():
            document_size = len(self.documents[document_id])

            # Jaccard = overlap / (query_size + document_size - overlap).
            # Prune only when the candidate mathematically cannot meet
            # the configured threshold.
            required_overlap = math.ceil(
                self.threshold * (query_size + document_size)
                / (1 + self.threshold)
            )
            if overlap < required_overlap:
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

        for shingle in shingles:
            self.inverted_index[shingle].add(document_id)
