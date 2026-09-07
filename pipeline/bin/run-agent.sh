#!/usr/bin/env bash
#
# The only place in the pipeline that knows how the agents differ.
#
# Every stage hands this script a prompt file and gets back a raw transcript.
# Swap executors with AGENT_CMD so a run can go to whichever subscription has
# quota left, without touching the stages themselves.
#
#   AGENT_CMD=codex   ->  codex exec       (Codex CLI, headless)
#   AGENT_CMD=claude  ->  claude -p        (Claude Code, headless)
#   AGENT_CMD=stub    ->  cat $AGENT_STUB_OUTPUT   (offline tests, no tokens)
#
# Usage: run-agent.sh --stage <name> --prompt <file> --out <file> [--cwd <dir>]
set -euo pipefail

# shellcheck source=lib/common.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

STAGE=""; PROMPT=""; OUT=""; CWD="$PWD"

while [ $# -gt 0 ]; do
  case "$1" in
    --stage)  STAGE="$2"; shift 2 ;;
    --prompt) PROMPT="$2"; shift 2 ;;
    --out)    OUT="$2"; shift 2 ;;
    --cwd)    CWD="$2"; shift 2 ;;
    -h|--help) awk 'NR>1 && /^#/ {sub(/^# ?/, ""); print; next} NR>1 {exit}' "$0"; exit 0 ;;
    *) die "run-agent.sh: unknown argument '$1'" ;;
  esac
done

[ -n "$STAGE" ]  || die "run-agent.sh: --stage is required"
[ -n "$PROMPT" ] || die "run-agent.sh: --prompt is required"
[ -n "$OUT" ]    || die "run-agent.sh: --out is required"
[ -f "$PROMPT" ] || die "run-agent.sh: prompt file not found: $PROMPT"
[ -d "$CWD" ]    || die "run-agent.sh: working directory not found: $CWD"

AGENT_CMD="${AGENT_CMD:-codex}"
AGENT_TIMEOUT="${AGENT_TIMEOUT:-900}"
CODEX_BIN="${CODEX_BIN:-codex}"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"

ensure_dirs
LOG_FILE="$LOG_DIR/$(date -u +%Y%m%dT%H%M%SZ)-$STAGE-$AGENT_CMD.log"

run_with_timeout() {
  local tb
  tb="$(timeout_bin)"
  if [ -n "$tb" ]; then
    "$tb" "$AGENT_TIMEOUT" "$@"
  else
    log_warn "no timeout/gtimeout on PATH — running without a time limit"
    "$@"
  fi
}

log_info "stage=$STAGE agent=$AGENT_CMD cwd=$CWD timeout=${AGENT_TIMEOUT}s"

set +e
case "$AGENT_CMD" in
  codex)
    have "$CODEX_BIN" || die "AGENT_CMD=codex but '$CODEX_BIN' is not on PATH (see pipeline/README.md)"
    # `codex exec -` reads the prompt from stdin and runs non-interactively.
    # shellcheck disable=SC2086  # CODEX_EXEC_ARGS is an intentional word-split hook
    ( cd "$CWD" && run_with_timeout "$CODEX_BIN" exec ${CODEX_EXEC_ARGS:---skip-git-repo-check} - ) \
      < "$PROMPT" > "$OUT" 2> >(tee -a "$LOG_FILE" >&2)
    ;;
  claude)
    have "$CLAUDE_BIN" || die "AGENT_CMD=claude but '$CLAUDE_BIN' is not on PATH (see pipeline/README.md)"
    # shellcheck disable=SC2086  # CLAUDE_EXEC_ARGS is an intentional word-split hook
    ( cd "$CWD" && run_with_timeout "$CLAUDE_BIN" -p ${CLAUDE_EXEC_ARGS:---output-format text} ) \
      < "$PROMPT" > "$OUT" 2> >(tee -a "$LOG_FILE" >&2)
    ;;
  stub)
    [ -n "${AGENT_STUB_OUTPUT:-}" ] || die "AGENT_CMD=stub requires AGENT_STUB_OUTPUT=<fixture file>"
    [ -f "$AGENT_STUB_OUTPUT" ] || die "stub fixture not found: $AGENT_STUB_OUTPUT"
    cat "$AGENT_STUB_OUTPUT" > "$OUT"
    ;;
  *)
    die "unknown AGENT_CMD '$AGENT_CMD' (expected: codex, claude, stub)"
    ;;
esac
status=$?
set -e

cp "$OUT" "$LOG_FILE.transcript" 2>/dev/null || true

if [ "$status" -ne 0 ]; then
  log_error "agent exited $status (log: $LOG_FILE)"
  exit "$status"
fi

log_info "agent finished (transcript: $LOG_FILE.transcript)"
