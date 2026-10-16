# Flam Data Curation Pipeline

A Python prototype for curating Hindi and Hinglish text with Unicode
normalization, language classification, personal-information redaction,
quality filtering, deduplication, a processing ledger, and evaluation
contamination checks.

## Requirements

- Python 3.10 or later
- No third-party packages required by the core pipeline

## Run the pipeline

From the repository root:

```bash
./run.sh data/raw output
```

The pipeline reads JSONL files from the input directory and generates:

- `output/clean.jsonl` — retained documents in JSONL format
- `output/clean.jsonl.gz` — deterministic compressed JSONL for delivery
- `output/ledger.jsonl` — a processing record for each input line
- `output/manifest.json` — run counts and configuration

Run the evaluation contamination check separately:

```bash
python src/contamination.py \
  data/holdout/eval.jsonl \
  output/clean.jsonl \
  output/contamination.jsonl
```

## Automated tests

Run the unit tests with:

```bash
python -m unittest discover -s tests -v
```

The current 16-test suite passes and covers text normalization,
language classification, common PII redaction cases, quality checks,
and near-duplicate detection. It does not cover every pipeline edge case.

## Observed dataset run

The latest documented run processed five JSONL input files:

- Input lines: 11,936
- Valid records: 11,936
- Retained records: 10,363
- Dropped records: 1,573
- Held-out evaluation examples: 200
- Contamination flags: 0 using the implemented checks

These figures describe a specific local run; they are not guaranteed
for different input files or code versions.

## Sources and licensing

The input corpus includes Hindi Wikipedia-derived text and Hinglish
records from the HinGE dataset. Check each source's license, attribution
requirements, and redistribution terms before redistributing data.
See `DECISIONS.md` for the current provenance notes and limitations.

## Repository layout

- `src/` — processing, quality, redaction, deduplication, and contamination modules
- `tests/` — automated unit tests
- `data/sample/` — a small example dataset
- `data/holdout/` — held-out evaluation examples
- `download.sh` — entry point for the Hindi Wikipedia downloaders
- `download_eval.py` — evaluation-set acquisition
- `download_hf_wikipedia.py` — Hugging Face Wikipedia acquisition
- `run.sh` — pipeline entry point
- `DECISIONS.md` — observed results, engineering decisions, and limitations

Raw datasets and generated output files are excluded from Git. Follow the
source providers' terms when downloading, using, or sharing any data.

## Known limitations

- Language classification is heuristic and may misclassify mixed-language text.
- PII redaction uses regular expressions and can have false positives or negatives.
- Near-duplicate detection uses word-trigram Jaccard similarity with a preliminary
  threshold of 0.50.
- Evaluation contamination checks do not implement cross-script Hindi/Latin
  transliteration matching. Zero detected matches does not prove zero leakage.
- Source licensing and attribution requirements still need full verification.
- Multi-terabyte performance has not been benchmarked.

This is a working prototype, not a production-ready data-curation system.
See `DECISIONS.md` for further details.
