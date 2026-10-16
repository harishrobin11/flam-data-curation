import json
import re
from pathlib import Path

from datasets import load_dataset

RAW = Path("data/raw")
EVAL = Path("data/holdout/eval.jsonl")
TEMP = Path("data/holdout/eval_new.jsonl")
TARGET = 200

# Collect page IDs from every training JSONL file.
training_ids = set()
for path in RAW.glob("*.jsonl"):
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
                pageid = row.get("pageid")
                if pageid is not None:
                    training_ids.add(str(pageid))
            except (json.JSONDecodeError, AttributeError):
                continue

print("Training page IDs excluded:", len(training_ids))
print("Searching for substantive, unseen Hindi Wikipedia articles...")

ds = load_dataset(
    "wikimedia/wikipedia",
    "20231101.hi",
    split="train",
    streaming=True,
)

selected_ids = set()
written = 0

with TEMP.open("w", encoding="utf-8") as out:
    for row in ds:
        pageid = str(row.get("id", ""))
        title = str(row.get("title", "")).strip()
        text = str(row.get("text", "")).strip()
        url = str(row.get("url", ""))

        if not pageid or pageid in training_ids or pageid in selected_ids:
            continue
        if not title or not text:
            continue

        # Skip year-only pages and very short/template-like articles.
        if re.fullmatch(r"\d{1,4}", title):
            continue
        if len(text) < 1000:
            continue
        if len(re.findall(r"\w+", text)) < 150:
            continue

        record = {
            "id": f"eval-wiki-{pageid}",
            "pageid": pageid,
            "title": title,
            "text": text,
            "source": "Hindi Wikipedia held-out article",
            "url": url,
        }

        out.write(json.dumps(record, ensure_ascii=False) + "\n")
        selected_ids.add(pageid)
        written += 1

        if written % 25 == 0:
            out.flush()
            print(f"Selected {written}/{TARGET} articles")

        if written >= TARGET:
            break

if written == TARGET:
    TEMP.replace(EVAL)
    print(f"Success: replaced evaluation set with {written} articles.")
else:
    print(f"Only found {written} qualifying articles.")
    print("The original evaluation file was preserved.")
    print("Review the selection criteria before trying again.")

print("Evaluation file:", EVAL if written == TARGET else TEMP)
