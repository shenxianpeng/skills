---
name: pipeline-sop
description: >
  Run the standard maintenance pass over a repository: scan for gaps, file the
  approved ones as issues, implement them, and review the result. Use this skill
  when the user says something like "run the SOP", "按 SOP 处理一下", "do the
  maintenance pass on this repo", "run the pipeline", "process the pending
  findings", "what is the pipeline waiting on", or otherwise asks for the
  routine end-to-end maintenance chain rather than one specific step. This skill
  orchestrates the other skills in this repository (find-gap, github-gap-finder,
  create-pr, github-review) and knows where the human approval gates are.
---

# Pipeline SOP — one sentence drives the whole chain

## Purpose

Turn "this repo should get a pass" into a finished, reviewable change without the
user having to name each step. The value is that the steps are *always the same*:
same order, same gates, same output shape. That is what makes the work
delegatable — and what lets it be scheduled later.

Background and design rationale: `docs/ai-automation-pipeline.md`.

## Core principles

### Language rules
- **Conversation**: reply in the language the user writes to you in.
- **Artifacts**: issue titles and bodies, commit messages, branch names, and PR
  text are always in English.

### The two gates are not optional
Stage 2 (filing issues) and stage 4 (merging) require explicit human approval.
Never file issues or merge without being told to in this conversation. Showing a
draft and asking is always correct; "I went ahead and filed them" is not.

### Report state, not narration
The user is running this to save attention. Lead with what changed and what needs
a decision. Do not recount every file you read.

## Workflow

### Step 0 — establish the target

Determine which repository this pass is about, in this order: an explicit
argument from the user, the current git remote, or ask. If `pipeline/config/repos.yaml`
lists it, use that entry's `focus`, `labels`, and `max_issues_per_run`.

Then report the current state before doing anything expensive:

```bash
make status
```

If findings are already pending, say so and offer to triage those instead of
scanning again. Re-scanning on top of an unreviewed backlog is how a tracker
becomes noise.

### Step 1 — scan (automated, read-only)

```bash
make scan REPO=<owner/name>
```

This is read-only: no branches, no commits, no issues. The run writes validated
findings into `pipeline/state/<owner>__<repo>/findings.json`, deduplicated by
fingerprint, and prints how many are new.

If the run fails schema validation, do not paper over it — the transcript and the
rejected payload are kept next to each other in `pipeline/state/runs/`. Read them
and report what the agent got wrong. A silently-retried scan hides a prompt bug.

### Step 2 — triage (human gate ★)

```bash
make triage REPO=<owner/name>
```

Show the drafts. For each one, give the user enough to decide in one line each:
severity, area, how many scans it has appeared in, and the one-sentence proposal.

Then ask, and wait:

> These are the findings ready to file. Should I open them as issues?

Only after an explicit yes:

```bash
make triage REPO=<owner/name> APPLY=1
```

Add `ENRICH=1` when a finding is subtle enough that the issue body deserves an
agent-written verification pass first — it re-checks the finding against the
current code and drops it if it no longer holds.

If the user approves only some, file those with `--limit` or by filing from the
issue they pick; never file what they did not approve.

### Step 3 — implement (use the `create-pr` skill)

For each approved issue the user wants worked on now, follow the `create-pr`
skill. Non-negotiable in this context:

- Work on a branch, never the default branch.
- Run the repository's own checks before pushing (`make test`, its linters, its
  test suite — whatever it actually uses). "It looks right" is not a check.
- Open the PR as a draft unless the user says otherwise, and reference the issue.
- One issue per PR. A PR that closes three issues is a PR nobody reviews.

### Step 4 — review (use the `github-review` skill)

Run the `github-review` skill against the PR and report the verdict. Then stop.
**Never merge** — that is the second gate, and it belongs to the user.

## Output format

Close every SOP run with a short status block:

```
Repository:  owner/name
Scanned:     N findings (M new)
Filed:       <issue links, or "nothing — awaiting your approval">
PRs opened:  <links, or "none">
Needs you:   <the specific decision you are waiting on>
```

`Needs you` is the most important line. If it is empty, say the pass is complete.

## Notes

- If `make scan` reports a checkout that does not exist, fix the `path` in
  `pipeline/config/repos.yaml` rather than cloning somewhere arbitrary.
- The pipeline is designed to run repeatedly, so a partial pass is fine: stopping
  after step 2 with issues filed is a perfectly good outcome.
- If the user asks to schedule this, point them at
  `docs/ai-automation-pipeline.md` — specifically the checklist that has to pass
  before a scheduler is installed.
