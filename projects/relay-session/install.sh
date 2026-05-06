#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
usage: install.sh --target /path/to/repo [--copy] [--install-skill] [--skill-target /path/to/skills]

Examples:
  bash projects/relay-session/install.sh --target "$PWD" --copy
  bash projects/relay-session/install.sh --target "$PWD" --copy --install-skill
  curl -fsSL https://raw.githubusercontent.com/SaarShai/token-economy/main/projects/relay-session/install.sh \
    | bash -s -- --target "$PWD" --copy --install-skill
EOF
}

target=""
mode="symlink"
install_skill=0
skill_target="${CODEX_HOME:-$HOME/.codex}/skills"
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
    --install-skill)
      install_skill=1
      shift
      ;;
    --skill-target)
      skill_target="${2:-}"
      shift 2
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

script_dir="$(cd "$(dirname "$0")" 2>/dev/null && pwd || pwd)"
src="$script_dir/relay_session"
skill_src="$script_dir/../../skills/relay-sessions"
tmp=""

cleanup() {
  if [ -n "$tmp" ] && [ -d "$tmp" ]; then
    rm -rf "$tmp"
  fi
}
trap cleanup EXIT

if [ ! -d "$src" ] || { [ "$install_skill" -eq 1 ] && [ ! -d "$skill_src" ]; }; then
  tmp="$(mktemp -d)"
  archive="$tmp/token-economy.tar.gz"
  curl -fsSL "https://codeload.github.com/SaarShai/token-economy/tar.gz/main" -o "$archive"
  tar -xzf "$archive" -C "$tmp"
  src="$tmp/token-economy-main/projects/relay-session/relay_session"
  skill_src="$tmp/token-economy-main/skills/relay-sessions"
fi

if [ ! -d "$src" ]; then
  echo "relay_session package source not found" >&2
  exit 1
fi

mkdir -p "$target"
rm -rf "$target/relay_session"
if [ "$mode" = "copy" ]; then
  cp -R "$src" "$target/relay_session"
else
  ln -s "$src" "$target/relay_session"
fi

echo "installed relay_session in $target ($mode)"

if [ "$install_skill" -eq 1 ]; then
  if [ ! -d "$skill_src" ]; then
    echo "relay-sessions skill source not found" >&2
    exit 1
  fi
  mkdir -p "$skill_target"
  rm -rf "$skill_target/relay-sessions"
  cp -R "$skill_src" "$skill_target/relay-sessions"
  echo "installed relay-sessions skill in $skill_target/relay-sessions"
fi
