
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

OUT = Path("data/raw/hindi_wikipedia.jsonl")
TARGET = 1000
API = "https://hi.wikipedia.org/w/api.php"

OUT.parent.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "FlamDataCurationAssessment/1.0 "
        "(educational data-curation project)"
    )
})


def get_json(params, attempts=6):
    for attempt in range(attempts):
        response = session.get(API, params=params, timeout=40)

        if response.status_code == 429 or response.status_code >= 500:
            retry_after = response.headers.get("Retry-After")
            delay = (
                float(retry_after)
                if retry_after and retry_after.isdigit()
                else min(60, 5 * (2 ** attempt)) + random.random()
            )
            print(f"HTTP {response.status_code}; waiting {delay:.1f}s")
            time.sleep(delay)
            continue

        response.raise_for_status()
        return response.json()

    raise RuntimeError("Wikipedia remained rate-limited; stop and retry later.")


existing = set()
if OUT.exists():
    with OUT.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
                if row.get("id"):
                    existing.add(str(row["id"]))
            except json.JSONDecodeError:
                continue

saved = len(existing)
continuation = {}
download_date = datetime.now(timezone.utc).date().isoformat()

with OUT.open("a", encoding="utf-8") as out:
    while saved < TARGET:
        params = {
            "action": "query",
            "list": "allpages",
            "apnamespace": 0,
            "aplimit": 10,
            "format": "json",
            **continuation,
        }
        payload = get_json(params)
        pages = payload.get("query", {}).get("allpages", [])
        if not pages:
            break

        for page_info in pages:
            page_id = str(page_info["pageid"])
            if page_id in existing:
                continue

            detail = get_json({
                "action": "query",
                "prop": "extracts",
                "explaintext": 1,
                "pageids": page_id,
                "format": "json",
            })
            page = detail.get("query", {}).get("pages", {}).get(page_id, {})
            text = page.get("extract", "").strip()

            if text:
                title = page.get("title", "")
                row = {
                    "id": page_id,
                    "title": title,
                    "text": text,
                    "source": "Hindi Wikipedia",
                    "url": "https://hi.wikipedia.org/wiki/" + quote(
                        title.replace(" ", "_"), safe="/"
                    ),
                    "license": "CC BY-SA; confirm applicable page terms",
                    "download_date": download_date,
                }
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                out.flush()
                existing.add(page_id)
                saved += 1
                print(f"Saved {saved}/{TARGET}: {title}")

            time.sleep(2)

            if saved >= TARGET:
                break

        continuation = payload.get("continue", {})
        if not continuation:
            break

        time.sleep(5)

print(f"Saved {saved} unique page IDs to {OUT}")
