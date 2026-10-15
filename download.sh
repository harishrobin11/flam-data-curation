#!/usr/bin/env bash
set -euo pipefail

case "${1:-}" in
  hindi)
    exec python download_wikipedia.py
    ;;
  bulk)
    exec python download_wikipedia_bulk.py
    ;;
  *)
    echo "Usage: ./download.sh {hindi|bulk}" >&2
    echo "hindi: run the 1,000-page downloader" >&2
    echo "bulk: run the resumable bulk downloader" >&2
    exit 2
    ;;
esac
