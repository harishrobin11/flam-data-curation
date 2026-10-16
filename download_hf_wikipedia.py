import json
from datetime import date
from pathlib import Path

from datasets import load_dataset

RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)

OUTPUT = RAW / "hindi_wikipedia_hf.jsonl"
TARGET = 7000
DATASET = "wikimedia/wikipedia"
CONFIG = "20231101.hi"
TODAY = date.today().isoformat()

# Collect existing Wikipedia page IDs to avoid importing them again.
seen_ids = set()

for path in RAW.glob("*.jsonl"):
    if path == OUTPUT:
        continue
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
                pageid = row.get("pageid")
                if pageid is not None:
                    seen_ids.add(str(pageid))
            except (json.JSONDecodeError, AttributeError):
                continue

# Resume safely if this downloader has already run.
saved_ids = set()
if OUTPUT.exists():
    with OUTPUT.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
                pageid = row.get("pageid")
                if pageid is not None:
                    saved_ids.add(str(pageid))
            except (json.JSONDecodeError, AttributeError):
                continue

seen_ids.update(saved_ids)
written = len(saved_ids)

print("Existing page IDs:", len(seen_ids))
print(f"Target: {TARGET} new records")
print("Output:", OUTPUT)

if written >= TARGET:
    print("Target already reached; nothing to download.")
    raise SystemExit(0)

ds = load_dataset(
    DATASET,
    CONFIG,
    split="train",
    streaming=True,
)

try:
    with OUTPUT.open("a", encoding="utf-8") as out:
        for row in ds:
            pageid = str(row.get("id", ""))
            title = row.get("title", "")
            text = row.get("text", "")
            url = row.get("url", "")

            if not pageid or pageid in seen_ids or not text.strip():
                continue

            record = {
                "id": "wiki-hf:" + pageid,
                "pageid": pageid,
                "title": title,
                "text": text,
                "source": "Hindi Wikipedia via Wikimedia dataset",
                "dataset": DATASET,
                "dataset_config": CONFIG,
                "url": url,
                "license": (
                    "See Wikimedia Wikipedia dataset card and applicable "
                    "article terms; verify before redistribution"
                ),
                "download_date": TODAY,
            }

            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            seen_ids.add(pageid)
            written += 1

            if written % 100 == 0:
                out.flush()
                print(f"Saved {written}/{TARGET} new records")

            if written >= TARGET:
                break

        out.flush()

except KeyboardInterrupt:
    print("\nInterrupted. Saved records are preserved; rerun to resume.")
except Exception as exc:
    print(f"\nDownload interrupted: {exc}")
    print("Saved records are preserved; rerun to resume.")

print(f"Records saved by this downloader: {written}/{TARGET}")
print("Output:", OUTPUT)
