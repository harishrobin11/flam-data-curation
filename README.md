# Flam Data Curation Pipeline

A Python prototype for streaming JSONL text curation, language classification,
PII redaction, quality filtering, deduplication, and evaluation contamination
checks.

## Requirements

- Python 3.10 or later
- No third-party packages are required by the core pipeline

## Run the pipeline

From the repository root:

```bash
./run.sh data/raw output
```

The pipeline reads JSONL files from the input directory and writes:

- `output/clean.jsonl` — retained documents
- `output/ledger.jsonl` — one processing record per input line
- `output/manifest.json` — processing counts and configuration

Each retained document contains an ID, text, language label, and source
metadata where available.

## Check evaluation contamination

```bash
python src/contamination.py \
  data/holdout/eval.jsonl \
  output/clean.jsonl \
  output/contamination.jsonl
```

The checker reports normalized exact matches and word-trigram Jaccard
near-duplicates. Cross-script transliteration matching is not implemented.

## Repository layout

- `src/` — pipeline modules
- `data/sample/` — small example input sample
- `data/holdout/` — evaluation examples
- `download_wikipedia.py` and `download_wikipedia_bulk.py` — source acquisition
- `run.sh` — pipeline entry point
- `DECISIONS.md` — decisions, measured results, and limitations

Full raw datasets and generated outputs are intentionally excluded from Git.

## Current limitations

The current run processed 4,936 input lines and retained 4,745 records.
The evaluation set currently contains only five examples. Therefore, this
prototype does not yet meet the 10,000-document target or the approximately
200-example evaluation target. Source license verification, cross-script
contamination checking, and large-scale performance validation remain
incomplete.

See `DECISIONS.md` for current measurements and known limitations.
