#!/usr/bin/env bash
# Shared helpers for the pipeline scripts. Source it, do not execute it.
# shellcheck shell=bash

PIPELINE_BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIPELINE_DIR="$(cd "$PIPELINE_BIN_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PIPELINE_DIR/.." && pwd)"
LIB_DIR="$PIPELINE_BIN_DIR/lib"
STATE_DIR="${PIPELINE_STATE_DIR:-$PIPELINE_DIR/state}"
LOG_DIR="$STATE_DIR/logs"
RUN_DIR="$STATE_DIR/runs"
CONFIG_FILE="${PIPELINE_CONFIG:-$PIPELINE_DIR/config/repos.yaml}"
SCHEMA_DIR="$PIPELINE_DIR/schema"
PROMPT_DIR="$PIPELINE_DIR/prompts"

export PIPELINE_BIN_DIR PIPELINE_DIR REPO_ROOT LIB_DIR STATE_DIR LOG_DIR RUN_DIR
export CONFIG_FILE SCHEMA_DIR PROMPT_DIR

if [ -t 2 ] && [ -z "${NO_COLOR:-}" ]; then
  C_DIM=$'\033[2m'; C_RED=$'\033[31m'; C_YELLOW=$'\033[33m'; C_GREEN=$'\033[32m'; C_OFF=$'\033[0m'
else
  C_DIM=""; C_RED=""; C_YELLOW=""; C_GREEN=""; C_OFF=""
fi

_stamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

log_info()  { printf '%s%s%s %s\n' "$C_DIM" "$(_stamp)" "$C_OFF" "$*" >&2; }
log_ok()    { printf '%s%s%s %s%s%s\n' "$C_DIM" "$(_stamp)" "$C_OFF" "$C_GREEN" "$*" "$C_OFF" >&2; }
log_warn()  { printf '%s%s%s %swarn:%s %s\n' "$C_DIM" "$(_stamp)" "$C_OFF" "$C_YELLOW" "$C_OFF" "$*" >&2; }
log_error() { printf '%s%s%s %serror:%s %s\n' "$C_DIM" "$(_stamp)" "$C_OFF" "$C_RED" "$C_OFF" "$*" >&2; }
die()       { log_error "$*"; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

# macOS ships neither `timeout` nor `sha256sum` by default; fall back to the
# coreutils/BSD spellings instead of failing on the user's laptop.
timeout_bin() {
  if have timeout; then echo timeout
  elif have gtimeout; then echo gtimeout
  else echo ""
  fi
}

sha256_of() {
  if have sha256sum; then sha256sum "$1" | cut -d' ' -f1
  else shasum -a 256 "$1" | cut -d' ' -f1
  fi
}

python_bin() {
  if have python3; then echo python3
  else die "python3 is required but was not found on PATH"
  fi
}

slug_repo() { printf '%s' "${1//\//__}"; }

ensure_dirs() { mkdir -p "$STATE_DIR" "$LOG_DIR" "$RUN_DIR"; }

# Refuse to run two pipeline stages over the same repo at once — a half-written
# findings.json is worse than a skipped run.
acquire_lock() {
  local name="$1" lock_dir
  lock_dir="$STATE_DIR/.locks/$name.lock"
  mkdir -p "$STATE_DIR/.locks"
  if ! mkdir "$lock_dir" 2>/dev/null; then
    local owner="unknown"
    if [ -f "$lock_dir/pid" ]; then owner="$(cat "$lock_dir/pid")"; fi
    die "another run holds the lock for '$name' (pid $owner); remove $lock_dir if that process is gone"
  fi
  echo "$$" > "$lock_dir/pid"
  # shellcheck disable=SC2064  # expand lock_dir now, not at trap time
  trap "rm -rf '$lock_dir'" EXIT INT TERM
}

# Turn a raw agent transcript into a validated JSON document.
# extract_and_validate <raw-output> <schema> <destination>
extract_and_validate() {
  local raw="$1" schema="$2" dest="$3" py
  py="$(python_bin)"
  if ! "$py" "$LIB_DIR/extract_json.py" "$raw" > "$dest.tmp"; then
    rm -f "$dest.tmp"
    log_error "could not extract JSON from agent output; transcript kept at $raw"
    return 1
  fi
  if ! "$py" "$LIB_DIR/validate.py" "$schema" "$dest.tmp"; then
    mv "$dest.tmp" "$dest.rejected"
    log_error "agent output failed schema validation; rejected payload at $dest.rejected, transcript at $raw"
    return 1
  fi
  mv "$dest.tmp" "$dest"
  return 0
}

# json_get <file> <dotted.path> — small reader so the shell layer never has to
# depend on jq being installed.
json_get() {
  "$(python_bin)" - "$1" "$2" <<'PY'
import json, sys
node = json.load(open(sys.argv[1], encoding="utf-8"))
for key in sys.argv[2].split("."):
    node = node[int(key)] if key.lstrip("-").isdigit() else node[key]
if isinstance(node, (list, dict, bool)) or node is None:
    json.dump(node, sys.stdout, ensure_ascii=False)
else:
    sys.stdout.write(str(node))
PY
}

# resolve_path <path> — expand ~ and resolve relative paths from the repo root.
resolve_path() {
  local path="$1"
  if [ -z "$path" ]; then printf '%s' "$PWD"; return; fi
  case "$path" in
    "~"|"~/"*) path="$HOME${path#\~}" ;;
  esac
  case "$path" in
    /*) printf '%s' "$path" ;;
    *)  printf '%s' "$REPO_ROOT/$path" ;;
  esac
}
