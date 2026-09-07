# Pipeline

A local maintenance pipeline: it scans the repositories you list, turns real gaps
into GitHub issues, and leaves the judgement calls to you. It runs on your own
machine — no CI service, no hosted runner — and it can drive either Codex CLI or
Claude Code.

The reasoning behind it, and how the remaining stages are meant to be added, is
in [`../docs/ai-automation-pipeline.md`](../docs/ai-automation-pipeline.md).

## Quick start

```bash
make doctor          # is this machine able to run it?
make scan            # stage 1 — read-only, writes findings to pipeline/state/
make triage          # stage 2 — shows the issues it would file, files nothing
make triage APPLY=1  # actually file them
make status          # what is pending, per repository
make test            # offline test suite: no tokens, no network, no gh
```

First run should be `make scan REPO=<one repo> AGENT_CMD=<your executor>` so you
can read the transcript before trusting it with the whole list.

## Configuration

`config/repos.yaml` is the whole configuration. Adding a repository is the entire
onboarding step:

```yaml
repos:
  - repo: owner/name
    path: ~/code/name          # local checkout the agent reads
    focus: "what to look at in this repo"
    labels: [pipeline]
    max_issues_per_run: 3      # ceiling per run, so a bad scan cannot flood
```

`focus` matters more than it looks. A vague focus produces vague findings, and
vague findings are the thing that makes people stop reading the issue tracker.

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `AGENT_CMD` | `codex` | Which executor runs the prompt: `codex`, `claude`, or `stub` |
| `AGENT_TIMEOUT` | `900` | Seconds before an agent run is killed |
| `CODEX_BIN` / `CLAUDE_BIN` | `codex` / `claude` | Override the binary name or path |
| `CODEX_EXEC_ARGS` | `--skip-git-repo-check` | Extra args for `codex exec` |
| `CLAUDE_EXEC_ARGS` | `--output-format text` | Extra args for `claude -p` |
| `AGENT_STUB_OUTPUT` | — | Fixture file read when `AGENT_CMD=stub` |
| `PIPELINE_STATE_DIR` | `pipeline/state` | Where findings and logs live |
| `PIPELINE_CONFIG` | `pipeline/config/repos.yaml` | Alternate config file |

Only `python3` is required — the helpers deliberately avoid third-party packages,
including PyYAML (there is a fallback parser for the config file). `gh` is needed
only for `--apply`; `timeout` (or `gtimeout` from coreutils on macOS) is what
keeps a stuck run from hanging forever.

## Layout

```
bin/run-agent.sh     the only place that knows how codex and claude differ
bin/scan.sh          stage 1 — findings, deduplicated against state
bin/triage.sh        stage 2 — findings to issues, dry-run by default
bin/doctor.sh        environment check with actionable messages
bin/lib/*.py         config, templating, JSON extraction, schema validation, state
prompts/*.md         the prompts, with {{placeholders}}
schema/*.json        the output contracts every agent reply is validated against
schedule/            cron and launchd templates — install them last, not first
state/               findings, run artifacts, transcripts (git-ignored)
tests/run-tests.sh   offline suite driven by fixtures
```

## How a finding stays a single finding

Every finding is fingerprinted from `repo + normalized title + area`. A re-scan
that reports the same gap bumps its `seen_count` instead of creating a second
entry, so a daily scan never files a duplicate — and a finding seen in five
consecutive scans is one you can trust more than a one-off.

`pipeline/state/<owner>__<repo>/findings.json` is the whole memory of the system:
delete it and the next scan starts from zero.

## Quality gate

An agent reply is only allowed into state if it parses as JSON and validates
against `schema/findings.schema.json`. A reply that fails is written to
`*.rejected` next to its transcript, the run exits non-zero, and state is left
untouched. This is not optional strictness — an unvalidated pipeline quietly
fills your tracker with hallucinated issues, and then nobody reads the tracker.

## Testing

`make test` runs 45 assertions with a stubbed executor: syntax, both YAML parser
paths, the output contract, deduplication across two scans, the quality gate
rejecting a bad payload, dry-run triage never touching `gh`, and `--apply`
recording issue URLs without re-filing what it already filed.
