# Data Curation Pipeline — Engineering Decisions

## 1. Latest observed run

The latest completed pipeline run processed five JSONL files.

| Metric | Observed result |
|---|---:|
| Input files | 5 |
| Input lines | 11,936 |
| Valid records | 11,936 |
| Malformed JSON | 0 |
| Retained records | 10,363 |
| Dropped records | 1,573 |
| Exact duplicates dropped | 438 |
| Near duplicates dropped | 1,058 |
| Too-short records dropped | 20 |
| Low-letter-ratio records dropped | 47 |
| Repeated-character spam dropped | 9 |
| Replacement-character records dropped | 1 |

Retained language labels:

| Label | Count |
|---|---:|
| `hi` | 5,730 |
| `hi-Latn` | 2,529 |
| `en` | 2,104 |
| `other` | 0 |

The input files were `hindi_wikipedia.jsonl`,
`hindi_wikipedia_bulk.jsonl`, `hindi_wikipedia_checked.jsonl`,
`hindi_wikipedia_hf.jsonl`, and `hinglish.jsonl`.

## 2. Sources and provenance

The corpus includes Hindi Wikipedia-derived records and Hinglish records
from the HinGE dataset. Verify each source's license, attribution
requirements, and redistribution terms before distributing the data.
The Wikipedia downloader uses a cautious license note; not every
article's licensing obligations have been independently verified.

## 3. Processing decisions

- Input is read from sorted JSONL files under the raw directory.
- Text normalization applies Unicode NFC normalization, removes Unicode
  format-control characters, and collapses whitespace.
- Language labels are `hi`, `hi-Latn`, `en`, and `other`. Classification
  is heuristic; mixed-language records may be misclassified.
- Quality checks reject empty or short text, low letter ratios,
  repeated-character spam, and replacement characters.
- Regex-based redaction targets common Indian phone numbers, email
  addresses, Aadhaar-like numbers, and PAN-like identifiers. False
  positives and false negatives remain possible.
- Exact duplicates use normalized, case-folded text.
- Near duplicates use word-trigram Jaccard similarity with a threshold
  of 0.50. This threshold is preliminary and has not been calibrated
  against a representative labeled dataset.

## 4. Evaluation contamination

The current evaluation file contains 200 Hindi Wikipedia articles
selected to exclude page IDs found in the available training JSONL files.
Short articles and year-only titles were excluded. A previous candidate,
`उस्मानाबाद`, was replaced after a substantial overlap with a training
article about Osmanabad district was detected.

Latest contamination check:

- Evaluation examples checked: 200
- Examples flagged: 0
- Examples not flagged: 200
- Similarity threshold: 0.50

The checker uses normalized exact matching and word-trigram Jaccard
similarity. Zero flags means no matches were detected by these methods;
it does not prove the absence of all leakage. Cross-script Hindi/Latin
transliteration matching is not implemented. The checker may miss
paraphrases or flag unrelated text that shares common phrases.
The report is `output/contamination.jsonl`.

## 5. Limitations and next steps

- Verify and document source licenses and attribution obligations.
- Add cross-script contamination checks for Hindi in Devanagari versus
  Latin transliteration.
- Calibrate the near-duplicate threshold using representative positive
  and negative pairs, including borderline cases.
- Inspect false positives and false negatives from filtering and redaction.
- Add automated tests for malformed input, deterministic IDs, redaction,
  deduplication, and ledger consistency.
- Validate one ledger outcome per input record and check the final sample
  against the required schema.
- Confirm source metadata and URLs are preserved in the clean output.
- Benchmark runtime and memory before claiming multi-terabyte readiness.

No multi-terabyte performance validation is claimed. The language
classifier and regex filters are heuristic.

## 6. Reproducibility

Run the pipeline with:

`./run.sh data/raw output`

The pipeline writes cleaned JSONL, a per-input ledger, and a manifest.
Run the contamination check separately with:

`python src/contamination.py data/holdout/eval.jsonl output/clean.jsonl output/contamination.jsonl`

Refresh the manifest's evaluation section after every new check.
Raw datasets and generated output are excluded from Git. Counts in this
document describe the specific observed run and may change with inputs
or code.

## 7. Scope

This is a working prototype with more than 10,000 retained records and
a 200-example held-out check. Licensing verification, cross-script
contamination detection, comprehensive tests, threshold calibration,
and large-scale performance validation remain incomplete.
