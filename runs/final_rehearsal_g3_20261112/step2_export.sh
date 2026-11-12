#!/usr/bin/env bash
set -eu; source "$(dirname "$0")/common.sh"
$FR --step check --out $O/r1
$FR --step export --out $O/r1
