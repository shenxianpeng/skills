#!/usr/bin/env bash
#
# Check that this machine can actually run the pipeline, and say plainly what
# is missing. Exits non-zero only when something *required* is absent — a
# missing `gh` or a missing executor is reported but not fatal, because a
# dry-run scan with the other executor still works.
#
# Usage: doctor.sh
set -uo pipefail

# shellcheck source=lib/common.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

ok=0
warnings=0
required_missing=0

report() {
  case "$1" in
    ok)   printf '  %s✓%s %s\n' "$C_GREEN" "$C_OFF" "$2"; ok=$((ok + 1)) ;;
    warn) printf '  %s!%s %s\n' "$C_YELLOW" "$C_OFF" "$2"; warnings=$((warnings + 1)) ;;
    bad)  printf '  %s✗%s %s\n' "$C_RED" "$C_OFF" "$2"; required_missing=$((required_missing + 1)) ;;
  esac
}

echo "required"
if have python3; then
  report ok "python3 — $(python3 --version 2>&1)"
else
  report bad "python3 is missing (every helper in pipeline/bin/lib needs it)"
fi
if [ -n "$(timeout_bin)" ]; then
  report ok "timeout — $(timeout_bin) (agent runs are time-limited)"
else
  report warn "no timeout/gtimeout: a stuck agent run will hang forever. On macOS: brew install coreutils"
fi

echo
echo "config"
if [ -f "$CONFIG_FILE" ]; then
  if repos_json="$(python3 "$LIB_DIR/config.py" "$CONFIG_FILE" 2>&1)"; then
    n="$(python3 -c 'import json,sys;print(len(json.loads(sys.argv[1])))' "$repos_json")"
    report ok "$CONFIG_FILE parses — $n repository/repositories configured"
    python3 - "$repos_json" "$REPO_ROOT" <<'PY'
import json, os, sys
for entry in json.loads(sys.argv[1]):
    raw = entry.get("path") or "."
    path = os.path.expanduser(raw)
    if not os.path.isabs(path):
        path = os.path.join(sys.argv[2], path)
    mark = "  ✓" if os.path.isdir(path) else "  ✗"
    note = "" if os.path.isdir(path) else "  <- not a directory; clone it or fix 'path'"
    print(f"{mark} {entry['repo']} -> {path}{note}")
PY
  else
    report bad "$CONFIG_FILE does not parse: $repos_json"
  fi
else
  report bad "no config at $CONFIG_FILE"
fi

echo
echo "executors (AGENT_CMD)"
if have "${CODEX_BIN:-codex}"; then
  report ok "codex — AGENT_CMD=codex works"
else
  report warn "codex not on PATH — AGENT_CMD=codex will fail"
fi
if have "${CLAUDE_BIN:-claude}"; then
  report ok "claude — AGENT_CMD=claude works"
else
  report warn "claude not on PATH — AGENT_CMD=claude will fail"
fi
report ok "stub — AGENT_CMD=stub always works (used by the test suite)"

echo
echo "filing issues"
if have gh; then
  if gh auth status >/dev/null 2>&1; then
    report ok "gh is installed and authenticated — 'make triage APPLY=1' can file issues"
  else
    report warn "gh is installed but not authenticated — run: gh auth login"
  fi
else
  report warn "gh not on PATH — dry-run triage works, --apply does not"
fi

echo
echo "state"
if [ -d "$STATE_DIR" ]; then
  report ok "state dir: $STATE_DIR"
  python3 "$LIB_DIR/state.py" --state-dir "$STATE_DIR" status | sed 's/^/    /'
else
  report ok "state dir will be created on first run: $STATE_DIR"
fi

echo
printf '%d ok, %d warning(s), %d blocking problem(s)\n' "$ok" "$warnings" "$required_missing"
[ "$required_missing" -eq 0 ]
