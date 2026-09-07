#!/usr/bin/env bash
#
# Stage 1 — scan.
#
# Runs a read-only gap scan over every repository in config/repos.yaml, folds
# the result into state, and reports how many findings are new. Safe to run
# every day: findings already known are recognised by fingerprint and only bump
# their seen_count, so the tracker never sees the same gap twice.
#
# Usage: scan.sh [--repo owner/name] [--config <file>] [--keep-going]
set -euo pipefail

# shellcheck source=lib/common.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

REPO_FILTER=""
KEEP_GOING=1

while [ $# -gt 0 ]; do
  case "$1" in
    --repo)       REPO_FILTER="$2"; shift 2 ;;
    --config)     CONFIG_FILE="$2"; shift 2 ;;
    --fail-fast)  KEEP_GOING=0; shift ;;
    --keep-going) KEEP_GOING=1; shift ;;
    -h|--help) awk 'NR>1 && /^#/ {sub(/^# ?/, ""); print; next} NR>1 {exit}' "$0"; exit 0 ;;
    *) die "scan.sh: unknown argument '$1'" ;;
  esac
done

PY="$(python_bin)"
[ -f "$CONFIG_FILE" ] || die "config not found: $CONFIG_FILE"

ensure_dirs
acquire_lock "scan"

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_PATH="$RUN_DIR/$RUN_ID-scan"
mkdir -p "$RUN_PATH"

if [ -n "$REPO_FILTER" ]; then
  "$PY" "$LIB_DIR/config.py" "$CONFIG_FILE" --repo "$REPO_FILTER" > "$RUN_PATH/repos.json"
else
  "$PY" "$LIB_DIR/config.py" "$CONFIG_FILE" > "$RUN_PATH/repos.json"
fi

COUNT="$("$PY" -c 'import json,sys;print(len(json.load(open(sys.argv[1]))))' "$RUN_PATH/repos.json")"
[ "$COUNT" -gt 0 ] || die "no repositories configured in $CONFIG_FILE"

log_info "scanning $COUNT repository/repositories (run $RUN_ID, agent ${AGENT_CMD:-codex})"

failures=0
for (( i = 0; i < COUNT; i++ )); do
  "$PY" -c 'import json,sys;json.dump(json.load(open(sys.argv[1]))[int(sys.argv[2])],open(sys.argv[3],"w"),ensure_ascii=False)' \
    "$RUN_PATH/repos.json" "$i" "$RUN_PATH/repo-$i.json"

  repo="$(json_get "$RUN_PATH/repo-$i.json" repo)"
  focus="$(json_get "$RUN_PATH/repo-$i.json" focus)"
  max_issues="$(json_get "$RUN_PATH/repo-$i.json" max_issues_per_run)"
  repo_path="$(resolve_path "$(json_get "$RUN_PATH/repo-$i.json" path)")"
  slug="$(slug_repo "$repo")"

  if [ ! -d "$repo_path" ]; then
    log_error "$repo: checkout not found at $repo_path — clone it or fix 'path' in $CONFIG_FILE"
    failures=$((failures + 1))
    [ "$KEEP_GOING" -eq 1 ] || exit 1
    continue
  fi

  log_info "--- $repo (path: $repo_path)"

  "$PY" "$LIB_DIR/state.py" --state-dir "$STATE_DIR" titles --repo "$repo" > "$RUN_PATH/$slug-known.md"

  "$PY" - "$RUN_PATH/repo-$i.json" "$RUN_PATH/$slug-known.md" "$RUN_PATH/$slug-vars.json" <<'PY'
import json, sys
repo_cfg = json.load(open(sys.argv[1], encoding="utf-8"))
known = open(sys.argv[2], encoding="utf-8").read().strip()
json.dump(
    {
        "repo": repo_cfg["repo"],
        "focus": repo_cfg.get("focus") or "general correctness, documentation, and tests",
        "max_issues": repo_cfg.get("max_issues_per_run", 3),
        "known_titles": known,
    },
    open(sys.argv[3], "w", encoding="utf-8"),
    ensure_ascii=False,
)
PY

  "$PY" "$LIB_DIR/render.py" "$PROMPT_DIR/scan.md" "$RUN_PATH/$slug-vars.json" > "$RUN_PATH/$slug-prompt.md"

  if ! "$PIPELINE_BIN_DIR/run-agent.sh" \
        --stage "scan-$slug" \
        --prompt "$RUN_PATH/$slug-prompt.md" \
        --out "$RUN_PATH/$slug-raw.txt" \
        --cwd "$repo_path"; then
    log_error "$repo: agent run failed"
    failures=$((failures + 1))
    [ "$KEEP_GOING" -eq 1 ] || exit 1
    continue
  fi

  if ! extract_and_validate "$RUN_PATH/$slug-raw.txt" "$SCHEMA_DIR/findings.schema.json" "$RUN_PATH/$slug-findings.json"; then
    log_error "$repo: output did not meet the findings contract — nothing written to state"
    failures=$((failures + 1))
    [ "$KEEP_GOING" -eq 1 ] || exit 1
    continue
  fi

  summary="$("$PY" "$LIB_DIR/state.py" --state-dir "$STATE_DIR" merge \
    --repo "$repo" --findings "$RUN_PATH/$slug-findings.json")"
  new="$("$PY" -c 'import json,sys;print(json.loads(sys.argv[1])["new"])' "$summary")"
  pending="$("$PY" -c 'import json,sys;print(json.loads(sys.argv[1])["pending"])' "$summary")"
  log_ok "$repo: $new new finding(s), $pending pending review"
done

log_info "run artifacts: $RUN_PATH"

if [ "$failures" -gt 0 ]; then
  log_error "$failures repository/repositories failed"
  exit 1
fi

log_ok "scan complete — review with: make triage"
