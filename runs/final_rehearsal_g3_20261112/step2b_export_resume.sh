#!/usr/bin/env bash
# resume of step2 after the session was cut (export only; check stamp already written, cache r1/retrieval.sqlite kept)
set -eu; source "$(dirname "$0")/common.sh"
$FR --step export --out $O/r1
