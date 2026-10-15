# Data Curation Pipeline — Engineering Decisions

## 1. Current dataset and results

The pipeline was run on four JSONL input files.

| Metric | Observed result |
|---|---:|
| Input files | 4 |
| Input lines | 4,936 |
| Valid records | 4,936 |
| Malformed JSON | 0 |
| Retained records | 4,745 |
| Dropped records | 191 |
| Exact duplicates dropped | 19 |
| Near duplicates dropped | 164 |
| Too-short records dropped | 7 |
| Low-letter-ratio records dropped | 1 |

The retained records were classified as follows:

- `hi`: 112
- `hi-Latn`: 2,529
- `en`: 2,104

These are current run results, not evidence that the assignment's full dataset-size requirement has been met. The corpus currently contains fewer than the required 10,000 documents.

## 2. Processing decisions

- Input is processed as JSONL, one record at a time.
- Text normalization applies Unicode NFC normalization, removes format-control characters, and collapses whitespace.
- Language labels are `hi`, `hi-Latn`, `en`, and `other`.
- Quality checks reject empty or short text, low letter ratios, repeated-character spam, and replacement characters.
- Personal-data redaction targets common Indian phone numbers, email addresses, Aadhaar-like numbers, and PAN-like identifiers.
- Exact duplicates are identified using normalized, case-folded text.
- Near duplicates use word-trigram Jaccard similarity with a threshold of 0.50.

The threshold is a preliminary engineering choice. Testing so far is limited and does not establish that it is optimal. Three example comparisons were inspected during development; broader threshold calibration remains necessary.

## 3. Evaluation contamination

The current held-out file contains five examples. The contamination checker reported:

- Examples checked: 5
- Contaminated examples detected: 0
- Similarity threshold: 0.50

The check uses normalized exact matching and word-trigram Jaccard similarity. Cross-script transliteration matching is not implemented. Five examples are not sufficient to satisfy the target of approximately 200 held-out examples, and the evaluation set should be expanded and checked for independence from training data.

## 4. Limitations and next steps

- Increase the corpus to at least 10,000 documents from at least two verified public sources.
- Verify and document each source's license and provenance.
- Expand the evaluation set to approximately 200 independently held-out examples.
- Add cross-script contamination checks for Hindi written in Devanagari versus Latin transliteration.
- Validate deduplication thresholds on representative positive and negative pairs.
- Inspect false-positive and false-negative examples from quality filtering and redaction.
- Add automated tests for malformed input, deterministic IDs, redaction, deduplication, and ledger consistency.
- Benchmark memory and runtime before claiming readiness for multi-terabyte processing.

## 5. Reproducibility

Run the pipeline with:

`./run.sh data/raw output`

The pipeline produces cleaned JSONL, a per-input ledger, and a manifest. The separate contamination check is run with:

`python src/contamination.py data/holdout/eval.jsonl output/clean.jsonl output/contamination.jsonl`

The manifest should be regenerated or updated after the contamination check. Output counts above describe the current observed run and may change if the input corpus changes.

## 6. Scope

This is a working prototype, not yet a fully compliant final dataset delivery. The current input count, evaluation-set size, cross-script contamination coverage, and large-scale performance remain below or short of the intended requirements. No claim of multi-terabyte validation is made.