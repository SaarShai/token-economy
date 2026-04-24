#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from token_economy.cli import main


raise SystemExit(main(["context", "meter", *(__import__("sys").argv[1:])]))
