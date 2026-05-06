#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 --target /path/to/repo [--copy]" >&2
}

target=""
mode="symlink"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      target="${2:-}"
      shift 2
      ;;
    --copy)
      mode="copy"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

if [ -z "$target" ]; then
  usage
  exit 2
fi

src="$(cd "$(dirname "$0")" && pwd)/relay_session"
mkdir -p "$target"
rm -rf "$target/relay_session"
if [ "$mode" = "copy" ]; then
  cp -R "$src" "$target/relay_session"
else
  ln -s "$src" "$target/relay_session"
fi

echo "installed relay_session in $target ($mode)"

