#!/usr/bin/env python3
"""Download a dataset by registry key. Kaggle or Hugging Face.

Usage:
  python3 fetch.py coqa
  python3 fetch.py code_refactoring_120k
"""
import argparse, os, subprocess, sys
from pathlib import Path

try: import yaml
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "--user", "pyyaml"])
    import yaml

BENCH = Path(__file__).resolve().parent
DATA = BENCH / "data"
REGISTRY = BENCH / "registry.yaml"
KAGGLE = os.path.expanduser("~/.local/bin/kaggle")


def load():
    return yaml.safe_load(REGISTRY.read_text())["datasets"]


def fetch(key):
    reg = load()
    if key not in reg:
        sys.exit(f"unknown dataset: {key}. known: {list(reg)}")
    d = reg[key]
    target = DATA / key
    target.mkdir(parents=True, exist_ok=True)

    if d["source"] == "kaggle":
        print(f"→ kaggle: {d['id']} → {target}")
        subprocess.check_call([KAGGLE, "datasets", "download", "-d", d["id"],
                                "-p", str(target), "--unzip"])
    elif d["source"] == "hf":
        print(f"→ hf: {d['id']} (loaded at runtime via datasets lib; no local copy)")
        # Verify accessible
        from datasets import load_dataset
        kwargs = {"split": d.get("split", "train")}
        if "subset" in d: kwargs["name"] = d["subset"]
        ds = load_dataset(d["id"], **kwargs)
        print(f"  ok, {len(ds)} items")
    else:
        sys.exit(f"unknown source: {d['source']}")

    print(f"✓ {key} ready at {target}")
    return target


def list_all():
    reg = load()
    print(f"{'key':<25} {'source':<8} {'tests':<30} {'type'}")
    for k, v in reg.items():
        print(f"{k:<25} {v['source']:<8} {','.join(v['tests']):<30} {v['type']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("key", nargs="?", help="dataset registry key, or omit to list")
    args = ap.parse_args()
    if not args.key: list_all()
    else: fetch(args.key)


if __name__ == "__main__":
    main()
