import json
import time
from datetime import date
from pathlib import Path
from urllib.parse import quote

import requests

RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)
OUTPUT = RAW / "hindi_wikipedia_bulk.jsonl"
TARGET = 8000
BATCH = 50

API = "https" + "://" + "hi.wikipedia.org" + "/w/api.php"
DOMAIN = "hi.wikipedia.org"
LICENSE = "CC BY-SA 4.0; verify individual page terms"
TODAY = date.today().isoformat()

session = requests.Session()
session.headers.update({
    "User-Agent": "FlamDataCuration/1.0 (educational dataset collection)"
})

seen_ids = set()
if OUTPUT.exists():
    with OUTPUT.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
                seen_ids.add(str(row.get("pageid", "")))
            except json.JSONDecodeError:
                continue

def get_json(params):
    for attempt in range(6):
        try:
            response = session.get(API, params=params, timeout=45)
            if response.status_code == 429 or response.status_code >= 500:
                time.sleep(min(2 ** attempt, 30))
                continue
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise RuntimeError(data["error"])
            return data
        except (requests.RequestException, ValueError):
            if attempt == 5:
                raise
            time.sleep(min(2 ** attempt, 30))
    raise RuntimeError("API retries exhausted")

written = len(seen_ids)
failures = 0

print("Existing unique pages:", written)
print("Target:", TARGET)

with OUTPUT.open("a", encoding="utf-8") as out:
    while written < TARGET:
        try:
            title_data = get_json({
                "action": "query",
                "list": "random",
                "rnnamespace": 0,
                "rnlimit": BATCH,
                "format": "json"
            })
            titles = [
                item["title"]
                for item in title_data.get("query", {}).get("random", [])
            ]
            if not titles:
                raise RuntimeError("API returned no article titles")

            details = get_json({
                "action": "query",
                "titles": "|".join(titles),
                "prop": "extracts|info",
                "explaintext": 1,
                "inprop": "url",
                "redirects": 1,
                "format": "json",
                "formatversion": 2
            })

            added = 0
            for page in details.get("query", {}).get("pages", []):
                pageid = page.get("pageid")
                text = page.get("extract", "")
                if pageid is None or not text.strip():
                    continue
                pageid = str(pageid)
                if pageid in seen_ids:
                    continue

                title = page.get("title", "")
                url = page.get("fullurl") or (
                    "https://" + DOMAIN + "/wiki/" +
                    quote(title.replace(" ", "_"), safe="/")
                )
                record = {
                    "id": "wiki:" + pageid,
                    "pageid": pageid,
                    "title": title,
                    "text": text,
                    "source": "Hindi Wikipedia",
                    "url": url,
                    "license": LICENSE,
                    "download_date": TODAY
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                seen_ids.add(pageid)
                written += 1
                added += 1

            out.flush()
            failures = 0
            print(f"Saved {written}/{TARGET} unique pages (+{added})")
            time.sleep(0.15)

        except Exception as exc:
            failures += 1
            print(f"Batch failed ({failures}/8): {exc}")
            if failures >= 8:
                print("Stopped safely. Run this script again to resume.")
                break
            time.sleep(min(2 ** failures, 30))

print("Output:", OUTPUT)
print("Total unique pages:", written)
