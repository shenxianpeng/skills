# AI Agent Skills

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

A collection of reusable agent skills for AI coding assistants. Each skill helps an AI agent perform a specific task — reviewing pull requests, analyzing competitive gaps, creating PRs from issues, and more.

This repository is intentionally small and explicit: each skill should be easy to inspect, copy, install, or adapt without relying on hidden local state.

## Quick Install

Install **all skills** at once with the `skills` CLI:

```bash
npx skills add https://github.com/shenxianpeng/skills
```

Or install a **single skill**:

```bash
npx skills add https://github.com/shenxianpeng/skills --skill create-pr
npx skills add https://github.com/shenxianpeng/skills --skill find-gap
npx skills add https://github.com/shenxianpeng/skills --skill github-gap-finder
npx skills add https://github.com/shenxianpeng/skills --skill github-review
npx skills add https://github.com/shenxianpeng/skills --skill pipeline-sop
```

## Manual Install

For agents or setups that don't support the `skills` CLI, clone and copy:

```bash
git clone https://github.com/shenxianpeng/skills.git /tmp/shenxianpeng-skills
mkdir -p ~/.codex/skills

# Install all skills
cp -R /tmp/shenxianpeng-skills/skills/* ~/.codex/skills/

# Or install a single skill (e.g., create-pr)
cp -R /tmp/shenxianpeng-skills/skills/create-pr ~/.codex/skills/
```

## Skills Overview

| Skill | Description | Install |
|-------|-------------|---------|
| [**Create PR**](skills/create-pr/) | Analyze GitHub issues, implement fixes or features, and create pull requests with Conventional Commits. | `npx skills add ... --skill create-pr` |
| [**Find Gap**](skills/find-gap/) | Analyze a project against competitors and market needs. Score, compare, and produce a gap report. | `npx skills add ... --skill find-gap` |
| [**GitHub Gap Finder**](skills/github-gap-finder/) | Inspect a repository, identify actionable gaps, get approval, then create GitHub issues. | `npx skills add ... --skill github-gap-finder` |
| [**GitHub Review**](skills/github-review/) | Review GitHub pull requests for merge readiness — checks context, linked issues, implementation, tests, and code quality. | `npx skills add ... --skill github-review` |
| [**Pipeline SOP**](skills/pipeline-sop/) | Run the standard maintenance pass over a repository: scan → issues → PR → review, with the human gates in the right places. | `npx skills add ... --skill pipeline-sop` |

## Repository Layout

```text
skills/
  create-pr/            Agent skill for analyzing issues, implementing fixes, and creating PRs
  find-gap/             Agent skill for competitive analysis and project gap discovery
  github-gap-finder/    Agent skill for finding repository gaps and creating approved GitHub issues
  github-review/        Agent skill for GitHub PR merge-readiness reviews
  pipeline-sop/         Agent skill that runs the four stages above as one maintenance pass
pipeline/               Local automation that runs the pipeline on your own machine
docs/                   Design notes, starting with the automation pipeline blueprint
```

## Automation Pipeline

The skills above are the four stages of a maintenance loop. [`pipeline/`](pipeline/)
runs the first two of them on your own machine — no CI service — against every
repository listed in `pipeline/config/repos.yaml`:

```bash
make doctor          # check the machine can run it
make scan            # stage 1: read-only gap scan, deduplicated against state
make triage          # stage 2: show the issues it would file (files nothing)
make triage APPLY=1  # file them
```

It drives either Codex CLI or Claude Code (`AGENT_CMD=codex|claude`), validates
every agent reply against a JSON schema before trusting it, and never files an
issue or merges a PR without you saying so. The design rationale, the metrics
worth tracking, and the checklist to clear before putting it on a scheduler are
in [docs/ai-automation-pipeline.md](docs/ai-automation-pipeline.md).

## Conventions

- Keep each reusable skill under `skills/<skill-name>/`.
- Every skill should include a `SKILL.md` file with front matter, a clear trigger description, required inputs, workflow steps, and output expectations.
- Keep agent-specific metadata inside the skill directory, for example `agents/openai.yaml`.
- Do not commit generated outputs, local permissions, API keys, or machine-specific settings.
- If a dependency file is added, document which artifact uses it and how to run it.

## Standards

Skills follow the [Agent Skills Specification](https://agentskills.io/specification) where possible, so they remain portable across compatible agents and tooling.

## License

This work is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Each skill's content may have its own license as noted in its `SKILL.md` front matter.
