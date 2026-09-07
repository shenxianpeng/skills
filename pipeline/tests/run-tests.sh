#!/usr/bin/env bash
#
# Offline test suite. Runs the whole pipeline with AGENT_CMD=stub, so it costs
# no tokens and needs neither codex, claude, nor gh installed.
#
# Usage: pipeline/tests/run-tests.sh
set -uo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_DIR="$(cd "$TESTS_DIR/.." && pwd)"
FIXTURES="$TESTS_DIR/fixtures"
BIN="$PIPELINE_DIR/bin"
PY=python3

PASS=0
FAIL=0

pass() { printf '  \033[32mPASS\033[0m %s\n' "$1"; PASS=$((PASS + 1)); }
fail() { printf '  \033[31mFAIL\033[0m %s\n' "$1"; FAIL=$((FAIL + 1)); }
check() { if [ "$1" = "$2" ]; then pass "$3"; else fail "$3 (expected '$2', got '$1')"; fi; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
export PIPELINE_STATE_DIR="$WORK/state"
export AGENT_CMD=stub
export NO_COLOR=1

echo "== syntax =="
for script in "$BIN"/*.sh "$BIN"/lib/*.sh "$TESTS_DIR"/run-tests.sh; do
  if bash -n "$script"; then pass "bash -n $(basename "$script")"; else fail "bash -n $(basename "$script")"; fi
done
for script in "$BIN"/lib/*.py; do
  if "$PY" -c "import ast,sys;ast.parse(open(sys.argv[1]).read())" "$script"; then
    pass "python syntax $(basename "$script")"
  else
    fail "python syntax $(basename "$script")"
  fi
done
if command -v shellcheck >/dev/null 2>&1; then
  if shellcheck -x "$BIN"/*.sh "$BIN"/lib/common.sh; then pass "shellcheck"; else fail "shellcheck"; fi
else
  echo "  SKIP shellcheck (not installed)"
fi

echo "== config =="
out="$("$PY" "$BIN/lib/config.py" "$FIXTURES/repos.test.yaml")"
check "$("$PY" -c 'import json,sys;print(json.loads(sys.stdin.read())[0]["repo"])' <<<"$out")" \
  "test-owner/test-repo" "config.py resolves the repo entry"
check "$("$PY" -c 'import json,sys;print(json.loads(sys.stdin.read())[0]["max_issues_per_run"])' <<<"$out")" \
  "2" "entry overrides the default cap"
"$PY" "$BIN/lib/config.py" "$FIXTURES/repos.test.yaml" --repo nope/nope >/dev/null 2>&1
check "$?" "1" "config.py rejects an unknown --repo"

# The fallback parser must agree with PyYAML — it is the path taken on machines
# without PyYAML installed.
fallback_check="$("$PY" - "$BIN/lib" "$FIXTURES/repos.test.yaml" <<'PY'
import json, sys
sys.path.insert(0, sys.argv[1])
real_import = __builtins__.__import__
def no_yaml(name, *a, **k):
    if name == "yaml":
        raise ImportError("forced")
    return real_import(name, *a, **k)
import config
__builtins__.__import__ = no_yaml
mini = config.resolve(config._mini_yaml(open(sys.argv[2], encoding="utf-8").read()))
__builtins__.__import__ = real_import
full = config.resolve(config.load(sys.argv[2]))
print("same" if mini == full else f"different:\n{json.dumps(mini)}\n{json.dumps(full)}")
PY
)"
check "$fallback_check" "same" "fallback YAML parser matches PyYAML"

echo "== output contract =="
"$PY" "$BIN/lib/extract_json.py" "$FIXTURES/scan-output.md" > "$WORK/extracted.json"
check "$?" "0" "extract_json pulls the fenced block out of a transcript"
check "$("$PY" -c 'import json,sys;print(len(json.load(open(sys.argv[1]))["findings"]))' "$WORK/extracted.json")" \
  "2" "extracted document keeps both findings"
"$PY" "$BIN/lib/validate.py" "$PIPELINE_DIR/schema/findings.schema.json" "$WORK/extracted.json"
check "$?" "0" "good findings pass validation"

"$PY" "$BIN/lib/extract_json.py" "$FIXTURES/scan-output-bad.md" > "$WORK/bad.json"
"$PY" "$BIN/lib/validate.py" "$PIPELINE_DIR/schema/findings.schema.json" "$WORK/bad.json" 2>"$WORK/bad.err"
check "$?" "1" "bad findings fail validation"
if grep -q "is not one of" "$WORK/bad.err" && grep -q "minLength" "$WORK/bad.err"; then
  pass "validation errors name the offending fields"
else
  fail "validation errors name the offending fields"
fi

echo '{"a": 1}' > "$WORK/novars.json"
"$PY" "$BIN/lib/render.py" "$PIPELINE_DIR/prompts/scan.md" "$WORK/novars.json" >/dev/null 2>&1
check "$?" "1" "render.py refuses to leave placeholders unfilled"

echo "== scan (stubbed agent) =="
export AGENT_STUB_OUTPUT="$FIXTURES/scan-output.md"
"$BIN/scan.sh" --config "$FIXTURES/repos.test.yaml" >"$WORK/scan1.log" 2>&1
check "$?" "0" "first scan succeeds"
STATE_FILE="$PIPELINE_STATE_DIR/test-owner__test-repo/findings.json"
check "$("$PY" -c 'import json,sys;print(len(json.load(open(sys.argv[1]))))' "$STATE_FILE")" \
  "2" "two findings landed in state"
check "$("$PY" -c 'import json,sys;print(list(json.load(open(sys.argv[1])).values())[0]["seen_count"])' "$STATE_FILE")" \
  "1" "seen_count starts at 1"

"$BIN/scan.sh" --config "$FIXTURES/repos.test.yaml" >"$WORK/scan2.log" 2>&1
check "$?" "0" "second scan succeeds"
check "$("$PY" -c 'import json,sys;print(len(json.load(open(sys.argv[1]))))' "$STATE_FILE")" \
  "2" "re-scan does not duplicate known findings"
if grep -q "0 new finding" "$WORK/scan2.log"; then
  pass "re-scan reports zero new findings"
else
  fail "re-scan reports zero new findings ($(grep -o '[0-9]* new finding' "$WORK/scan2.log" | head -1))"
fi
check "$("$PY" -c 'import json,sys;print(min(r["seen_count"] for r in json.load(open(sys.argv[1])).values()))' "$STATE_FILE")" \
  "2" "re-seen findings bump seen_count"

echo "== quality gate =="
cp "$STATE_FILE" "$WORK/state-before.json"
AGENT_STUB_OUTPUT="$FIXTURES/scan-output-bad.md" "$BIN/scan.sh" --config "$FIXTURES/repos.test.yaml" >"$WORK/scan3.log" 2>&1
check "$?" "1" "a scan that violates the contract fails"
if diff -q "$WORK/state-before.json" "$STATE_FILE" >/dev/null; then
  pass "state is untouched by a rejected scan"
else
  fail "state is untouched by a rejected scan"
fi
if ls "$PIPELINE_STATE_DIR"/runs/*/*-findings.json.rejected >/dev/null 2>&1; then
  pass "rejected payload is kept for inspection"
else
  fail "rejected payload is kept for inspection"
fi

echo "== triage (dry run) =="
PATH_WITHOUT_GH="$WORK/bin-no-gh"
mkdir -p "$PATH_WITHOUT_GH"
cat > "$PATH_WITHOUT_GH/gh" <<'SH'
#!/usr/bin/env bash
echo "gh was called during a dry run" >&2
exit 99
SH
chmod +x "$PATH_WITHOUT_GH/gh"
PATH="$PATH_WITHOUT_GH:$PATH" "$BIN/triage.sh" --config "$FIXTURES/repos.test.yaml" >"$WORK/triage.log" 2>&1
check "$?" "0" "dry-run triage succeeds"
if grep -q "gh was called" "$WORK/triage.log"; then
  fail "dry run must not call gh"
else
  pass "dry run does not call gh"
fi
if grep -q "Acceptance criteria" "$WORK/triage.log" && grep -q "Add eval suites" "$WORK/triage.log"; then
  pass "dry run prints a full issue draft"
else
  fail "dry run prints a full issue draft"
fi
check "$("$PY" -c 'import json,sys;print(sum(1 for r in json.load(open(sys.argv[1])).values() if r["status"]=="new"))' "$STATE_FILE")" \
  "2" "dry run leaves findings pending"

echo "== triage --enrich (stubbed agent) =="
AGENT_STUB_OUTPUT="$FIXTURES/triage-output.md" "$BIN/triage.sh" --config "$FIXTURES/repos.test.yaml" \
  --repo test-owner/test-repo --limit 1 --enrich >"$WORK/enrich.log" 2>&1
check "$?" "0" "enriched dry run succeeds"
if grep -q "enriched 'Add eval suites" "$WORK/enrich.log"; then
  pass "enrich replaces the draft body"
else
  fail "enrich replaces the draft body"
fi

echo "== triage --apply (fake gh) =="
FAKE_BIN="$WORK/bin-fake-gh"
mkdir -p "$FAKE_BIN"
cat > "$FAKE_BIN/gh" <<'SH'
#!/usr/bin/env bash
# Stand-in for the GitHub CLI: records the call and returns an issue URL.
printf '%s\n' "$*" >> "$FAKE_GH_CALLS"
echo "https://github.com/test-owner/test-repo/issues/1"
SH
chmod +x "$FAKE_BIN/gh"
export FAKE_GH_CALLS="$WORK/gh-calls.txt"
PATH="$FAKE_BIN:$PATH" "$BIN/triage.sh" --config "$FIXTURES/repos.test.yaml" --limit 1 --apply >"$WORK/apply.log" 2>&1
check "$?" "0" "apply run succeeds"
if grep -q -- "--label pipeline" "$FAKE_GH_CALLS" && grep -q "issue create" "$FAKE_GH_CALLS"; then
  pass "gh issue create is called with the configured labels"
else
  fail "gh issue create is called with the configured labels"
fi
check "$("$PY" -c 'import json,sys;print(sum(1 for r in json.load(open(sys.argv[1])).values() if r["status"]=="issued"))' "$STATE_FILE")" \
  "1" "the filed finding is recorded as issued"
check "$("$PY" -c 'import json,sys;print(sum(1 for r in json.load(open(sys.argv[1])).values() if r["issue_url"]))' "$STATE_FILE")" \
  "1" "the issue URL is stored on the finding"
PATH="$FAKE_BIN:$PATH" "$BIN/triage.sh" --config "$FIXTURES/repos.test.yaml" --apply >"$WORK/apply2.log" 2>&1
check "$("$PY" -c 'import json,sys;print(sum(1 for r in json.load(open(sys.argv[1])).values() if r["status"]=="issued"))' "$STATE_FILE")" \
  "2" "a second apply files only what is still pending"
check "$(grep -c "issue create" "$FAKE_GH_CALLS")" "2" "already-filed findings are not filed twice"

echo "== status =="
"$PY" "$BIN/lib/state.py" --state-dir "$PIPELINE_STATE_DIR" status >"$WORK/status.txt" 2>&1
if grep -q "test-owner/test-repo" "$WORK/status.txt"; then pass "status lists the repo"; else fail "status lists the repo"; fi

echo
printf 'passed %d, failed %d\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
