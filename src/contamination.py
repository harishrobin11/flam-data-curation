"""Check held-out evaluation examples against the cleaned corpus."""

import json
import sys
from pathlib import Path

from deduplication import word_shingles, jaccard_similarity
from text_processing import normalize_text


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
            "Usage: python src/contamination.py <eval.jsonl> "
            "<clean.jsonl> <report.jsonl>"
        )

    eval_path, clean_path, report_path = map(Path, sys.argv[1:])
    clean = list(load_jsonl(clean_path))

    exact_index = {}
    for row in clean:
        normalized = normalize_text(row["text"]).casefold()
        exact_index.setdefault(normalized, row.get("id"))

    clean_shingles = [
        (row.get("id"), word_shingles(row["text"]))
        for row in clean
    ]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    checked = contaminated = 0

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
                for candidate_id, candidate_shingles in clean_shingles:
                    score = jaccard_similarity(shingles, candidate_shingles)
                    if score > best_score:
                        best_score = score
                        match_id = candidate_id

                if best_score >= 0.50:
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

    print(json.dumps({
        "evaluation_examples_checked": checked,
        "contaminated_examples": contaminated,
        "clean_examples": checked - contaminated,
        "threshold": 0.50,
        "report": str(report_path),
    }, indent=2))


if __name__ == "__main__":
    main()
