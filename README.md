# AI Artifacts

Personal AI artifacts, agent skills, and reusable workflows.

This repository is intentionally small and explicit: each artifact should be easy to inspect, copy, install, or adapt without relying on hidden local state.

## Repository Layout

```text
skills/
  find-gap/             Agent skill for competitive analysis and project gap discovery
  github-gap-finder/    Agent skill for finding repository gaps and creating approved GitHub issues
  github-review/        Agent skill for GitHub PR merge-readiness reviews
```

## Available Skills

### Find Gap

Path: [`skills/find-gap/`](skills/find-gap/)

Analyzes a project (GitHub repository or product) to identify gaps vs. competitors and unmet market needs. Scores the project against objective criteria, compares it with competitors, surfaces unmet needs from real community discussions, and produces a focused gap report.

Install with the `skills` CLI:

```bash
npx skills add shenxianpeng/skills --skill find-gap -g
```

Manual install:

```bash
git clone https://github.com/shenxianpeng/skills.git /tmp/shenxianpeng-skills
mkdir -p ~/.codex/skills
cp -R /tmp/shenxianpeng-skills/skills/find-gap ~/.codex/skills/
```

### GitHub Review

Path: [`skills/github-review/`](skills/github-review/)

Reviews GitHub pull requests for merge readiness by reading PR context, tracing linked issues or requirements, validating the implementation, checking tests and CI evidence, and assessing code quality.

Install with the `skills` CLI:

```bash
npx skills add shenxianpeng/skills --skill github-review -g
```

Manual install:

```bash
git clone https://github.com/shenxianpeng/skills.git /tmp/shenxianpeng-skills
mkdir -p ~/.codex/skills
cp -R /tmp/shenxianpeng-skills/skills/github-review ~/.codex/skills/
```

### GitHub Gap Finder

Path: [`skills/github-gap-finder/`](skills/github-gap-finder/)

Inspects GitHub repositories like a senior open source contributor and product manager, identifies actionable project gaps, asks for approval, then creates one GitHub issue per approved idea.

Install with the `skills` CLI:

```bash
npx skills add shenxianpeng/skills --skill github-gap-finder -g
```

Manual install:

```bash
git clone https://github.com/shenxianpeng/skills.git /tmp/shenxianpeng-skills
mkdir -p ~/.codex/skills
cp -R /tmp/shenxianpeng-skills/skills/github-gap-finder ~/.codex/skills/
```

> **Tip:** To install all skills at once, run:
> ```bash
> npx skills add shenxianpeng/skills -g
> ```

## Conventions

- Keep each reusable skill under `skills/<skill-name>/`.
- Every skill should include a `SKILL.md` file with front matter, a clear trigger description, required inputs, workflow steps, and output expectations.
- Keep agent-specific metadata inside the skill directory, for example `agents/openai.yaml`.
- Do not commit generated outputs, local permissions, API keys, or machine-specific settings.
- If a dependency file is added, document which artifact uses it and how to run it.

## Standards

Skills should follow the [Agent Skills Specification](https://agentskills.io/specification) where possible, so they remain portable across compatible agents and tooling.
