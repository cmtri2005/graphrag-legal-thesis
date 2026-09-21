#!/usr/bin/env bash
# Publish the current data/ to the Hugging Face dataset repo as one tarball.
# Every push is a commit on the repo, so its history is the snapshot history.
# Two derived files are left out, and only two: data/temporal.sqlite and
# data/expiry_targets.jsonl. The receiver rebuilds them with build_store.py
# and then resolve_expiry_targets.py — build_store.py alone does not write
# expiry_targets.jsonl.
#
# Everything under data/derived/ DOES ship, all ~1.2 GB of it, despite the
# name. Do not add it to the excludes to "match" this comment: the released
# vilextime/*.jsonl carry version_id fields that resolve only against
# versions.jsonl, and pull_snapshot.sh does not tell anyone to rebuild it.
# Dropping it would leave a snapshot that pulls, builds and verifies clean
# while every gold answer points at nothing.
#
#   scripts/push_snapshot.sh [repo]        (run from the repo root, after `hf auth login`)
set -euo pipefail
REPO="${1:-tricaominh/temporal_vietnames_law}"
[ -d data/raw ] || { echo "run from the repo root: data/raw not found" >&2; exit 1; }

as_of=$(python3 -c "import json;print(json.loads(open('data/delta_runs.jsonl').read().strip().splitlines()[-1])['at'][:10])")
{
  echo "as_of:       $as_of"
  echo "documents:   $(ls data/raw | wc -l)"
  echo "code_commit: $(git rev-parse HEAD)$(git diff --quiet || echo ' (uncommitted changes)')"
  echo "created:     $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > data/SNAPSHOT.txt
cat data/SNAPSHOT.txt

tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
tar -czf "$tmp/data.tar.gz" --exclude=data/temporal.sqlite --exclude=data/expiry_targets.jsonl data
(cd "$tmp" && sha256sum data.tar.gz > data.tar.gz.sha256)
ls -lh "$tmp"

hf upload "$REPO" "$tmp" . --repo-type dataset --commit-message "data snapshot as of $as_of"
