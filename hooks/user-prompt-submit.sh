#!/usr/bin/env bash
set -euo pipefail

ROOT="${TOKEN_ECONOMY_ROOT:-$(pwd)}"
PROMPT="$(cat)"
"$ROOT/te" delegate classify "$PROMPT"

