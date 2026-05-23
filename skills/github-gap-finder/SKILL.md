---
name: github-gap-finder
description: Use when the user asks to inspect a GitHub repository and find missing pieces, product gaps, contribution opportunities, roadmap ideas, quality issues, documentation gaps, or issue ideas. This skill analyzes the repository like a senior open source contributor and product manager, lists actionable gaps first, requires explicit user approval, and only then creates GitHub issues for selected ideas.
---

# GitHub Gap Finder

## Purpose

Find valuable gaps in a GitHub repository and turn approved ideas into trackable GitHub issues. Approach the repository as both:

- A senior open source contributor looking for correctness, maintainability, onboarding, testing, release, security, and ecosystem gaps.
- A product manager looking for user workflows, adoption blockers, positioning, roadmap opportunities, and issue-sized improvements.

## Inputs

The user may provide:

- A GitHub repository URL.
- An owner/repo pair.
- A local worktree that has a GitHub remote.
- A topic such as docs, tests, CI, roadmap, developer experience, product gaps, or first-time contributor opportunities.

If the repository cannot be determined from the request, current worktree, or conversation, ask for it.

## Workflow

### 1. Read Repository Context

Gather enough evidence before proposing gaps:

- README, docs, website links, examples, demos, changelog, release notes, package metadata, and configuration.
- Existing open and closed issues, labels, milestones, discussions, and pull requests when available.
- CI workflows, tests, dependency setup, contribution guide, security policy, code of conduct, and release automation.
- Source layout, public APIs, CLI commands, app entry points, integrations, and extension points.
- Project positioning: intended users, main value proposition, maturity, competitors or adjacent projects when obvious.

Use the GitHub connector or `gh` CLI when available. Prefer primary repository sources over external guesses. If network or GitHub access is unavailable, use the local worktree and state the limitation.

### 2. Identify Gaps

Look for concrete, issue-sized opportunities across these areas:

- Product: unclear target users, missing workflows, weak onboarding path, missing integrations, incomplete UX, unprioritized roadmap, confusing feature boundaries.
- Documentation: missing quickstart, install guide, examples, API reference, architecture notes, troubleshooting, migration guide, screenshots, or demo.
- Quality: missing tests, brittle tests, untested critical paths, flaky CI, absent static analysis, insufficient error handling, weak validation, performance risks.
- Maintainer experience: unclear contribution process, absent issue templates, poor labels, missing release process, no changelog discipline, dependency update gaps.
- Security and operations: missing security policy, secret handling risks, supply-chain gaps, unsafe defaults, permissions that are broader than needed.
- Developer experience: difficult local setup, hidden prerequisites, slow feedback loops, inconsistent formatting, missing sample data or fixtures.
- Community and adoption: missing examples for common use cases, no comparison or positioning, unclear license, missing badges, stale project signals.

Avoid duplicates with existing issues. If a similar issue exists, reference it instead of proposing a new one, unless there is a clearly distinct angle.

### 3. Prioritize and Present for Approval

Before creating issues, present candidate gaps and stop for user approval. Do not create any issue before the user explicitly approves.

Use this format:

```markdown
Repository: <owner/repo>

Candidate gaps:
1. <Issue title>
   Why it matters: <short evidence-backed rationale>
   Evidence: <files, docs, issue links, or observed absence>
   Suggested issue scope: <specific deliverable>
   Priority: P0 | P1 | P2
   Effort: S | M | L

Existing related issues:
- <issue link or "None found">

Approval needed:
Reply with the numbers to create as GitHub issues, or ask for changes.
```

Keep the first pass focused. Prefer 5-12 strong candidates over an exhaustive list of weak ideas.

### 4. Create Issues After Approval

Only after explicit user approval, create one issue per approved idea. Each issue should be specific, actionable, and deduplicated.

Issue title:

- Start with an imperative verb when natural.
- Be specific enough to distinguish the issue from related work.
- Avoid vague titles like "Improve docs" or "Add tests".

Issue body:

```markdown
## Problem
<What gap exists and why it matters.>

## Evidence
- <Repository evidence, links, files, or observed absence.>

## Suggested Scope
- <Concrete tasks that would close the gap.>

## Acceptance Criteria
- <Observable outcomes.>

## Notes
<Related issues, risks, or implementation hints. Omit if unnecessary.>
```

Apply labels only when the repository already has suitable labels. Do not invent labels unless the user asks.

### 5. Report Results

After creating issues, summarize:

- Created issue links.
- Approved ideas that were not created and why.
- Any existing issues that should be updated instead of duplicated.

## Guardrails

- User approval is mandatory before issue creation.
- Do not create broad roadmap dumps. Convert ideas into small, trackable issues.
- Do not fabricate evidence. If a gap is inferred from absence, say what was checked.
- Do not criticize maintainers or contributors. Describe repository gaps in neutral, actionable terms.
- Do not open issues for speculative ideas when the repository evidence is weak; list them separately as low-confidence opportunities.
