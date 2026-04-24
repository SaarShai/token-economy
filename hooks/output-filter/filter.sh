#!/usr/bin/env bash
set -euo pipefail

# Generic no-deps output filter: strip ANSI, collapse progress, dedup adjacent lines.
# Exact lines containing error/fail/traceback/fatal are preserved.

python3 -c '
import re, sys
ansi = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
prev = None
repeat = 0
for raw in sys.stdin:
    line = ansi.sub("", raw.rstrip("\n"))
    if "\r" in line or re.search(r"\d+%\s*$", line):
        continue
    important = re.search(r"(error|fail|fatal|traceback|exception)", line, re.I)
    if not important and line == prev:
        repeat += 1
        continue
    if repeat:
        print(f"[deduped {repeat} repeated lines]")
        repeat = 0
    print(line)
    prev = line
if repeat:
    print(f"[deduped {repeat} repeated lines]")
'
