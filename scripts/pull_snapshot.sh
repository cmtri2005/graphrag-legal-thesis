#!/usr/bin/env bash
# Fetch a data/ snapshot from the Hugging Face dataset repo into this checkout.
#
#   scripts/pull_snapshot.sh [revision] [repo]     (revision: commit sha, default latest)
set -euo pipefail
REV="${1:-main}"
REPO="${2:-tricaominh/temporal_vietnames_law}"
if [ -n "$(ls -A data/raw 2>/dev/null)" ]; then
  echo "data/raw is not empty; move it aside first — this will not overwrite a crawl" >&2
  exit 1
fi

tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
hf download "$REPO" data.tar.gz data.tar.gz.sha256 --repo-type dataset --revision "$REV" --local-dir "$tmp"
(cd "$tmp" && sha256sum -c data.tar.gz.sha256)
tar -xzf "$tmp/data.tar.gz"
cat data/SNAPSHOT.txt
echo
echo "next: python scripts/check/verify_pipeline.py"
echo "      python scripts/pipeline/build_store.py --with-subtrees   # data/temporal.sqlite"
echo "      python scripts/pipeline/resolve_expiry_targets.py        # data/expiry_targets.jsonl"
echo
echo "Those two are the only files the snapshot leaves out. Everything else,"
echo "including data/derived/versions.jsonl and the ViLexTime sets, is already here."
