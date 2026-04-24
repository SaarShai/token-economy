#!/usr/bin/env bash
set -euo pipefail

ROOT="${TOKEN_ECONOMY_ROOT:-$(pwd)}"
printf '[token-economy] start: read %s/start.md, L0_rules.md, L1_index.md only\n' "$ROOT"

