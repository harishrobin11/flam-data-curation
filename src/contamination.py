"""Efficient exact and near-duplicate checks for evaluation data."""

import json
import sys
from collections import defaultdict
from pathlib import Path

from deduplication import word_shingles, jaccard_similarity
from text_processing import normalize_text

THRESHOLD = 0.50


def load_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{path}:{line_number}: invalid JSON: {exc}"
                ) from exc
            if isinstance(row, dict) and isinstance(row.get("text"), str):
                yield row


def main():
    if len(sys.argv) != 4:
        raise SystemExit(
            "Usage: python src/contamination.py "
            "<eval.jsonl> <clean.jsonl> <report.jsonl>"
        )

    eval_path, clean_path, report_path = map(Path, sys.argv[1:])
    exact_index = {}
    shingles_by_id = {}
    inverted_index = defaultdict(set)

    print("Indexing cleaned training data...", flush=True)

    for row in load_jsonl(clean_path):
        doc_id = row.get("id")
        normalized = normalize_text(row["text"]).casefold()
        exact_index.setdefault(normalized, doc_id)

        shingles = word_shingles(row["text"])
        shingles_by_id[doc_id] = shingles
        for shingle in shingles:
            inverted_index[shingle].add(doc_id)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    checked = contaminated = 0

    print("Checking evaluation examples...", flush=True)

    with report_path.open("w", encoding="utf-8") as out:
        for row in load_jsonl(eval_path):
            checked += 1
            text = normalize_text(row["text"])
            normalized = text.casefold()
            match_type = "none"
            match_id = None
            best_score = 0.0

            if normalized in exact_index:
                match_type = "exact_normalized"
                match_id = exact_index[normalized]
                best_score = 1.0
            else:
                shingles = word_shingles(text)
                candidates = set()
                for shingle in shingles:
                    candidates.update(inverted_index.get(shingle, ()))

                for candidate_id in candidates:
                    candidate_shingles = shingles_by_id[candidate_id]
                    score = jaccard_similarity(shingles, candidate_shingles)
                    if score > best_score or (
                        score == best_score
                        and score > 0
                        and (match_id is None or candidate_id < match_id)
                    ):
                        best_score = score
                        match_id = candidate_id

                if best_score >= THRESHOLD:
                    match_type = "near_duplicate"
                else:
                    match_id = None

            is_contaminated = match_type != "none"
            contaminated += int(is_contaminated)

            out.write(json.dumps({
                "eval_id": row.get("id"),
                "contaminated": is_contaminated,
                "match_type": match_type,
                "matched_training_id": match_id,
                "similarity": round(best_score, 4),
            }, ensure_ascii=False) + "\n")

            if checked % 25 == 0:
                print(f"Checked {checked} evaluation examples...", flush=True)

    print(json.dumps({
        "evaluation_examples_checked": checked,
        "contaminated_examples": contaminated,
        "clean_examples": checked - contaminated,
        "threshold": THRESHOLD,
        "report": str(report_path),
    }, indent=2))


if __name__ == "__main__":
    main()
