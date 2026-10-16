
"""Streaming baseline pipeline for the Flam data-curation assessment."""

import gzip
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

from deduplication import NearDuplicateIndex, SIMILARITY_THRESHOLD
from quality import quality_check
from redaction import redact_pii
from text_processing import classify_language, normalize_text


def stable_id(source_file: str, line_number: int) -> str:
    """Generate a deterministic ID for an input record."""
    value = f"{source_file}:{line_number}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def text_hash(text: str) -> str:
    """Hash normalized text for exact duplicate detection."""
    normalized = normalize_text(text).casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def process_file(path, source_root, clean_file, ledger_file, seen_hashes, near_index, stats):
    """Process a JSONL file one line at a time."""

    relative_source = str(path.relative_to(source_root))

    with path.open("r", encoding="utf-8", errors="replace") as raw:
        for line_number, raw_line in enumerate(raw, start=1):
            stats["input_lines"] += 1

            record_id = stable_id(relative_source, line_number)
            ledger = {
                "id": record_id,
                "source_file": relative_source,
                "line_number": line_number,
                "status": "dropped",
                "stage": "parse",
                "reason": "",
                "dup_of": None,
            }

            if not raw_line.strip():
                ledger["reason"] = "blank_line"
                stats["dropped"] += 1
                stats["drop_reasons"]["blank_line"] += 1
                ledger_file.write(json.dumps(ledger, ensure_ascii=False) + "\n")
                continue

            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                ledger["reason"] = "malformed_json"
                stats["malformed_json"] += 1
                stats["dropped"] += 1
                stats["drop_reasons"]["malformed_json"] += 1
                ledger_file.write(json.dumps(ledger, ensure_ascii=False) + "\n")
                continue

            if not isinstance(record, dict):
                ledger["reason"] = "non_object_record"
                stats["dropped"] += 1
                stats["drop_reasons"]["non_object_record"] += 1
                ledger_file.write(json.dumps(ledger, ensure_ascii=False) + "\n")
                continue

            stats["valid_records"] += 1
            ledger["stage"] = "text_extraction"

            original_text = record.get("text")
            if not isinstance(original_text, str):
                ledger["reason"] = "missing_or_invalid_text"
                stats["dropped"] += 1
                stats["drop_reasons"]["missing_or_invalid_text"] += 1
                ledger_file.write(json.dumps(ledger, ensure_ascii=False) + "\n")
                continue

            ledger["stage"] = "normalization"
            text = normalize_text(original_text)

            if not text:
                ledger["reason"] = "empty_text"
                stats["dropped"] += 1
                stats["drop_reasons"]["empty_text"] += 1
                ledger_file.write(json.dumps(ledger, ensure_ascii=False) + "\n")
                continue

            ledger["stage"] = "language_classification"
            language = classify_language(text)

            ledger["stage"] = "redaction"
            text = redact_pii(text)

            ledger["stage"] = "quality_filter"
            keep, reason = quality_check(text)

            if not keep:
                ledger["reason"] = reason
                stats["dropped"] += 1
                stats["drop_reasons"][reason] += 1
                ledger_file.write(json.dumps(ledger, ensure_ascii=False) + "\n")
                continue

            ledger["stage"] = "exact_deduplication"
            digest = text_hash(text)

            if digest in seen_hashes:
                ledger["reason"] = "exact_duplicate"
                ledger["dup_of"] = seen_hashes[digest]
                stats["dropped"] += 1
                stats["drop_reasons"]["exact_duplicate"] += 1
                ledger_file.write(json.dumps(ledger, ensure_ascii=False) + "\n")
                continue

            seen_hashes[digest] = record_id

            ledger["stage"] = "near_deduplication"
            near_match = near_index.find_duplicate(text)
            if near_match is not None:
                duplicate_id, similarity = near_match
                ledger["reason"] = "near_duplicate"
                ledger["dup_of"] = duplicate_id
                ledger["similarity"] = round(similarity, 4)
                stats["dropped"] += 1
                stats["drop_reasons"]["near_duplicate"] += 1
                ledger_file.write(json.dumps(ledger, ensure_ascii=False) + "\n")
                continue

            near_index.add(record_id, text)

            source_name = record.get("source", relative_source)
            clean_record = {
                "id": record_id,
                "text": text,
                "lang": language,
                "source": source_name,
            }

            clean_file.write(
                json.dumps(clean_record, ensure_ascii=False) + "\n"
            )

            ledger["status"] = "kept"
            ledger["stage"] = "complete"
            ledger["reason"] = "passed"
            stats["kept"] += 1
            stats["kept_by_language"][language] += 1

            ledger_file.write(json.dumps(ledger, ensure_ascii=False) + "\n")


def main():
    if len(sys.argv) != 3:
        print("Usage: python src/pipeline.py <raw_dir> <out_dir>")
        raise SystemExit(2)

    raw_dir = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()

    if not raw_dir.is_dir():
        raise SystemExit(f"Raw input directory not found: {raw_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(raw_dir.rglob("*.jsonl"))
    if not files:
        raise SystemExit(f"No .jsonl files found in {raw_dir}")

    stats = {
        "input_lines": 0,
        "valid_records": 0,
        "malformed_json": 0,
        "kept": 0,
        "dropped": 0,
        "kept_by_language": Counter(),
        "drop_reasons": Counter(),
    }

    seen_hashes = {}
    near_index = NearDuplicateIndex(SIMILARITY_THRESHOLD)

    # Write to temporary files first, then replace outputs after success.
    clean_tmp = out_dir / "clean.jsonl.tmp"
    ledger_tmp = out_dir / "ledger.jsonl.tmp"
    gzip_tmp = out_dir / "clean.jsonl.gz.tmp"

    try:
        with clean_tmp.open("w", encoding="utf-8") as clean_file, \
             ledger_tmp.open("w", encoding="utf-8") as ledger_file:

            for path in files:
                process_file(
                    path, raw_dir, clean_file, ledger_file,
                    seen_hashes, near_index, stats
                )

        # Create a deterministic compressed copy of the clean JSONL.
        with clean_tmp.open("rb") as source, gzip_tmp.open("wb") as target:
            with gzip.GzipFile(
                fileobj=target, mode="wb", filename="", mtime=0
            ) as compressed:
                shutil.copyfileobj(source, compressed)

        clean_tmp.replace(out_dir / "clean.jsonl")
        ledger_tmp.replace(out_dir / "ledger.jsonl")
        gzip_tmp.replace(out_dir / "clean.jsonl.gz")

    except Exception:
        clean_tmp.unlink(missing_ok=True)
        ledger_tmp.unlink(missing_ok=True)
        gzip_tmp.unlink(missing_ok=True)
        raise

    manifest = {
        "input_files": [str(path.relative_to(raw_dir)) for path in files],
        "input_lines": stats["input_lines"],
        "valid_records": stats["valid_records"],
        "malformed_json": stats["malformed_json"],
        "kept": stats["kept"],
        "dropped": stats["dropped"],
        "kept_by_language": dict(stats["kept_by_language"]),
        "drop_reasons": dict(stats["drop_reasons"]),
        "output_format": "JSONL and deterministic JSONL.GZ",
        "compressed_output": "clean.jsonl.gz",
        "near_duplicate_detection": "word-trigram Jaccard similarity",
        "near_duplicate_threshold": SIMILARITY_THRESHOLD,
        "near_duplicate_index": "in-memory",
        "evaluation_contamination_check": "not implemented yet",
    }

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
