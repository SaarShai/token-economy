#!/usr/bin/env bash
set -euo pipefail

ROOT="${TOKEN_ECONOMY_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
"$ROOT/te" wiki ingest "$@"

