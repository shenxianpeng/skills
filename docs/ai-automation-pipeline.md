# Building an AI maintenance pipeline

How to get real output out of AI subscriptions you already pay for — by building
a system that runs the boring parts, so your attention only goes where judgement
is actually required.

The argument behind this design: **the subscription is not the bottleneck, the
conversion rate is.** You can burn any amount of tokens re-reading a codebase
and produce nothing. What matters is how much of what the model produces you can
actually verify and merge. So the thing worth building is not a bigger prompt —
it is a pipeline that keeps producing reviewable work while you are asleep, and
presents it to you in a form you can accept or reject in seconds.

## The four stages

```
   ┌──────────┐     ┌──────────┐     ┌────────────┐     ┌──────────┐
   │  1 scan  │ ──▶ │ 2 triage │ ──▶ │ 3 implement│ ──▶ │ 4 review │
   └──────────┘     └──────────┘     └────────────┘     └──────────┘
    find gaps        gaps → issues     issue → PR        PR → verdict
    read-only        human gate ★      branch + tests    human gate ★
   find-gap       github-gap-finder      create-pr       github-review
   [automated]      [automated]          [manual]        [manual]
```

★ = where you spend your attention. Everything else is the system's job.

Stages 1 and 2 are implemented in [`../pipeline/`](../pipeline/). Stages 3 and 4
are the existing skills, still driven by hand — see *Adding stage 3* below for
what has to be true before automating them.

Each stage maps to a skill this repository already ships, which is the point: the
pipeline is glue, not new intelligence.

| Stage | Skill | What it produces |
|-------|-------|------------------|
| 1 scan | [`find-gap`](../skills/find-gap/) | Structured findings, validated against a schema |
| 2 triage | [`github-gap-finder`](../skills/github-gap-finder/) | GitHub issues, after you approve them |
| 3 implement | [`create-pr`](../skills/create-pr/) | A branch, a commit, a pull request |
| 4 review | [`github-review`](../skills/github-review/) | A merge-readiness verdict |
| all four | [`pipeline-sop`](../skills/pipeline-sop/) | One sentence drives the whole chain |

## Three principles this is built on

### 1. Do the things that compound

A run that starts from zero every morning is a treadmill. A run that remembers is
an asset.

Concretely: every finding gets a fingerprint (`repo + normalized title + area`).
Re-scanning tomorrow recognises what it already reported and bumps a counter
instead of filing it again. Three weeks in, that state file tells you something
no single scan can — which gaps keep resurfacing, and which were one-off noise.

The same idea applies to the prompts. `prompts/scan.md` is checked into git, so
every improvement you make to it is permanent. That is the difference between
prompting and building.

### 2. First you do a lot of things that don't scale

The compounding part comes later. The first weeks are manual and unglamorous:
run one repository at a time, read the whole transcript, notice that the model
keeps flagging the same non-issue, tighten `focus`, tighten the prompt, run
again. Every one of those corrections is a permanent improvement to a system
that will run thousands of times.

Skipping this and going straight to a nightly cron gives you an automated
generator of issues nobody reads. Which is worse than nothing, because now the
tracker is noise.

### 3. Scale your scarce resources, not your token spend

Your time, your attention, and your capacity to *verify* work are the scarce
inputs. Tokens are not. So push detail-verification into the machine wherever a
machine can do it:

- structured output instead of prose you have to read
- schema validation instead of eyeballing whether a reply is usable
- fingerprints instead of remembering what was already reported
- `max_issues_per_run` instead of triaging a flood

What remains for you is the macro judgement: *is this worth doing at all?* That
is the one thing that does not delegate — and the whole design exists to make
sure it is the only thing left on your desk.

### The trap to avoid

Do not measure this with token consumption. The moment burn becomes the target,
you will get burn and nothing else — a model can consume any budget you give it
re-reading files to no effect. Measure instead:

- **PRs merged per week** that originated in the pipeline
- **Issue acceptance rate** — filed vs. closed as invalid (below ~70%, stop and
  fix the scan prompt; the pipeline is producing noise)
- **Rework rate** — how often you rewrite the agent's work rather than merge it
- **Minutes of your attention per merged PR** — this should fall over time. If
  it doesn't, the automation isn't working, however busy it looks.

## Roadmap

**Stage 1–2 — scan and triage.** Implemented. `make scan` finds gaps and
deduplicates them against state; `make triage` shows what it would file and only
files with `APPLY=1`. Both run against every repository in `config/repos.yaml`.

**Stage 3 — implement.** Feed an issue to `create-pr` in a throwaway worktree,
run the repo's own checks, push a branch, open a draft PR. Prerequisites, all of
which stage 1–2 exist to establish:

- issue acceptance rate is consistently high — automating implementation of bad
  issues just wastes more of your time downstream
- the target repo has checks that actually fail on bad changes (without them,
  "the agent said it works" is the only signal, which is no signal)
- the PR is a *draft*, on a branch, never a direct push

**Stage 4 — review.** `github-review` on the resulting PR, posting a verdict as a
comment. Cheap to add once stage 3 is real, and it is what makes the loop close:
the reviewer catches what the implementer got wrong before you look.

**Stage 5 — unattended.** Only now install the scheduler
([`../pipeline/schedule/`](../pipeline/schedule/)). Everything before this point
should have been run by hand, on purpose, many times.

## Before you automate the trigger

Do not install the cron entry until all of these are true. This checklist is the
difference between a system that earns trust and one that gets muted:

- [ ] You have run `make scan` manually on at least 5 separate days
- [ ] The last 3 runs produced **zero** findings you would reject as noise
- [ ] Deduplication has been observed working — a re-scan reported `0 new`
- [ ] You know the wall-clock time and rough token cost of one full run
- [ ] `make triage` output is something you can skim in under two minutes
- [ ] A failed run is *visible* to you (you read the log, or it mails you)
- [ ] You know how to stop it: `crontab -e` / `launchctl unload`, and where the
      state file is if you need to reset it

## Running it on more than one machine

The state directory is the only thing that matters. Two machines scanning the
same repository with separate state will file duplicate issues, because neither
knows what the other reported.

Pick one: either one machine owns each repository (simplest, and enough for
most people), or the state directory lives in shared storage. Splitting *stages*
across machines is fine — a laptop that scans and a second machine that
implements share nothing but the issue tracker, which is already the handoff.

## What this deliberately does not do

- **It does not merge anything.** Both human gates are load-bearing.
- **It does not run in CI.** It is yours, on your machine, using your
  subscriptions, and it stops when you close the laptop.
- **It does not chase token consumption.** See the trap above.
- **It does not manage multiple accounts, virtual cards, or identity
  switching.** That is a terms-of-service problem, not an engineering one — and
  by the numbers it was never the constraint that mattered.
