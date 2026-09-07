#!/usr/bin/env bash
#
# Stage 2 — triage.
#
# Turns pending findings into GitHub issues. Dry-run by default: it prints what
# it *would* file and touches nothing. This is the human gate — the whole point
# is that you skim a short list instead of reading every scan transcript.
#
#   triage.sh                 # show drafts for every configured repo
#   triage.sh --repo o/n      # just one repository
#   triage.sh --enrich        # let the agent verify and rewrite each body first
#   triage.sh --apply         # actually open the issues (needs gh, authenticated)
#
set -euo pipefail

# shellcheck source=lib/common.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

REPO_FILTER=""
LIMIT=0
APPLY=0
ENRICH=0

while [ $# -gt 0 ]; do
  case "$1" in
    --repo)    REPO_FILTER="$2"; shift 2 ;;
    --config)  CONFIG_FILE="$2"; shift 2 ;;
    --limit)   LIMIT="$2"; shift 2 ;;
    --apply)   APPLY=1; shift ;;
    --enrich)  ENRICH=1; shift ;;
    -h|--help) awk 'NR>1 && /^#/ {sub(/^# ?/, ""); print; next} NR>1 {exit}' "$0"; exit 0 ;;
    *) die "triage.sh: unknown argument '$1'" ;;
  esac
done

PY="$(python_bin)"
[ -f "$CONFIG_FILE" ] || die "config not found: $CONFIG_FILE"
if [ "$APPLY" -eq 1 ]; then
  have gh || die "--apply needs the GitHub CLI ('gh') on PATH and authenticated (gh auth login)"
fi

ensure_dirs
acquire_lock "triage"

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_PATH="$RUN_DIR/$RUN_ID-triage"
mkdir -p "$RUN_PATH"

if [ -n "$REPO_FILTER" ]; then
  "$PY" "$LIB_DIR/config.py" "$CONFIG_FILE" --repo "$REPO_FILTER" > "$RUN_PATH/repos.json"
else
  "$PY" "$LIB_DIR/config.py" "$CONFIG_FILE" > "$RUN_PATH/repos.json"
fi
COUNT="$("$PY" -c 'import json,sys;print(len(json.load(open(sys.argv[1]))))' "$RUN_PATH/repos.json")"
[ "$COUNT" -gt 0 ] || die "no repositories configured in $CONFIG_FILE"

[ "$APPLY" -eq 1 ] || log_info "dry run — nothing will be created (add --apply to file these)"

total_drafts=0
created=0

for (( i = 0; i < COUNT; i++ )); do
  "$PY" -c 'import json,sys;json.dump(json.load(open(sys.argv[1]))[int(sys.argv[2])],open(sys.argv[3],"w"),ensure_ascii=False)' \
    "$RUN_PATH/repos.json" "$i" "$RUN_PATH/repo-$i.json"

  repo="$(json_get "$RUN_PATH/repo-$i.json" repo)"
  slug="$(slug_repo "$repo")"
  repo_path="$(resolve_path "$(json_get "$RUN_PATH/repo-$i.json" path)")"
  cap="$(json_get "$RUN_PATH/repo-$i.json" max_issues_per_run)"
  if [ "$LIMIT" -gt 0 ]; then cap="$LIMIT"; fi
  labels_csv="$("$PY" -c 'import json,sys;print(",".join(json.load(open(sys.argv[1])).get("labels") or []))' "$RUN_PATH/repo-$i.json")"

  "$PY" "$LIB_DIR/issue.py" --state-dir "$STATE_DIR" drafts \
    --repo "$repo" --limit "$cap" --labels "$labels_csv" > "$RUN_PATH/$slug-drafts.json"

  n="$("$PY" -c 'import json,sys;print(len(json.load(open(sys.argv[1]))))' "$RUN_PATH/$slug-drafts.json")"
  if [ "$n" -eq 0 ]; then
    log_info "$repo: nothing pending"
    continue
  fi

  log_info "--- $repo: $n pending finding(s), cap $cap"
  total_drafts=$((total_drafts + n))

  for (( j = 0; j < n; j++ )); do
    draft="$RUN_PATH/$slug-draft-$j.json"
    "$PY" -c 'import json,sys;json.dump(json.load(open(sys.argv[1]))[int(sys.argv[2])],open(sys.argv[3],"w"),ensure_ascii=False)' \
      "$RUN_PATH/$slug-drafts.json" "$j" "$draft"

    fingerprint="$(json_get "$draft" fingerprint)"
    title="$(json_get "$draft" title)"

    if [ "$ENRICH" -eq 1 ]; then
      "$PY" "$LIB_DIR/render.py" "$PROMPT_DIR/triage.md" "$draft" > "$RUN_PATH/$slug-$j-prompt.md" || {
        log_warn "$repo: could not render enrich prompt for $fingerprint, keeping the plain draft"
      }
      if [ -s "$RUN_PATH/$slug-$j-prompt.md" ] && \
         "$PIPELINE_BIN_DIR/run-agent.sh" --stage "triage-$slug-$j" \
            --prompt "$RUN_PATH/$slug-$j-prompt.md" \
            --out "$RUN_PATH/$slug-$j-raw.txt" --cwd "$repo_path" && \
         extract_and_validate "$RUN_PATH/$slug-$j-raw.txt" "$SCHEMA_DIR/issue.schema.json" "$RUN_PATH/$slug-$j-issue.json"; then
        if [ "$(json_get "$RUN_PATH/$slug-$j-issue.json" valid)" = "false" ]; then
          log_warn "$repo: finding '$title' no longer holds up — skipping (see $RUN_PATH/$slug-$j-issue.json)"
          continue
        fi
        "$PY" -c 'import json,sys
draft = json.load(open(sys.argv[1], encoding="utf-8"))
enriched = json.load(open(sys.argv[2], encoding="utf-8"))
draft["title"] = enriched["title"]
draft["body"] = enriched["body"]
draft["labels"] = list(dict.fromkeys(draft["labels"] + enriched.get("labels", [])))
json.dump(draft, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)' \
          "$draft" "$RUN_PATH/$slug-$j-issue.json"
        title="$(json_get "$draft" title)"
        log_info "$repo: enriched '$title'"
      else
        log_warn "$repo: enrich step failed for '$title' — keeping the plain draft"
      fi
    fi

    body_file="$RUN_PATH/$slug-$j-body.md"
    "$PY" "$LIB_DIR/issue.py" --state-dir "$STATE_DIR" render --draft "$draft" --body-out "$body_file"

    if [ "$APPLY" -eq 0 ]; then
      printf '\n%s[%s] %s%s\n' "$C_GREEN" "$fingerprint" "$title" "$C_OFF"
      sed 's/^/    /' "$body_file"
      continue
    fi

    label_args=()
    while IFS= read -r label; do
      if [ -n "$label" ]; then label_args+=(--label "$label"); fi
    done < <("$PY" -c 'import json,sys;print("\n".join(json.load(open(sys.argv[1])).get("labels") or []))' "$draft")

    url=""
    if url="$(gh issue create --repo "$repo" --title "$title" --body-file "$body_file" "${label_args[@]}" 2>"$RUN_PATH/$slug-$j-gh.err")"; then
      :
    elif url="$(gh issue create --repo "$repo" --title "$title" --body-file "$body_file" 2>>"$RUN_PATH/$slug-$j-gh.err")"; then
      log_warn "$repo: created without labels (a label probably does not exist in the repo)"
    else
      log_error "$repo: gh issue create failed for '$title' — $(tr '\n' ' ' < "$RUN_PATH/$slug-$j-gh.err")"
      continue
    fi

    "$PY" "$LIB_DIR/state.py" --state-dir "$STATE_DIR" record-issue \
      --repo "$repo" --fingerprint "$fingerprint" --issue "$url"
    created=$((created + 1))
    log_ok "$repo: $url"
  done
done

if [ "$APPLY" -eq 1 ]; then
  log_ok "created $created issue(s) from $total_drafts draft(s)"
else
  log_info "$total_drafts draft(s) shown — run 'make triage APPLY=1' to file them"
fi
