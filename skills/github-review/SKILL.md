---
name: github-review
description: Use when the user provides a GitHub pull request number, PR ID, or pull request URL and asks for a merge-readiness review. This skill reviews the PR description, comments, linked issues, implementation diff, tests, and code quality to decide whether the PR can be merged.
---

# GitHub Review

## Purpose

Determine whether a GitHub pull request is ready to merge by tracing it back to the validated issue or requirement, checking whether the implementation actually solves the problem, and reviewing code quality.

## Inputs

The user may provide:

- A full GitHub pull request URL.
- A PR number or ID. If only a number is provided, infer the repository from the current worktree or conversation. Ask for the repository only when it cannot be determined.

## Review Workflow

### 1. Read the PR

Collect the PR context before reviewing code:

- PR title, body, author, target branch, and current state.
- Files changed and diff.
- PR conversation comments.
- Review comments and unresolved review threads.
- CI/check status when available.

Use the GitHub connector or `gh` CLI when available. Prefer thread-level review data when determining whether comments are resolved.

### 1a. Analyze Existing Review Comments

Before forming your own opinion, examine any review comments already left by human reviewers:

- Read each review comment and understand the reviewer's concern or suggestion.
- Assess whether the comment is valid: does it point to a genuine bug, design issue, quality concern, or missing test?
- Check whether the comment has been resolved or addressed by the PR author. If a comment is marked as resolved, verify that the resolution actually addresses the concern.
- Distinguish between non-blocking subjective opinions and comments that identify real defects.
- Reference valuable reviewer comments in your final report — they provide useful context and strengthen your verdict.

### 2. Trace Linked Issues

Find issues referenced by GitHub closing keywords in the PR title, body, commits, and comments. Include common forms such as:

- `fix`, `fixes`, `fixed`
- `close`, `closes`, `closed`
- `resolve`, `resolves`, `resolved`

For each referenced issue:

- Open the issue and read the original report or request.
- Read issue comments and discussion that clarify scope, acceptance criteria, reproduction steps, or maintainer decisions.
- Confirm the issue exists and appears validated. Treat an issue as validated when maintainers, maintainers' labels, reproducible evidence, accepted requirements, or subsequent discussion confirm it is legitimate.

If no linked issue exists, review against the PR's stated requirement, but call out the missing issue traceability as a risk when it matters.

### 3. Understand the Requirement

Before judging the implementation, write down the actual requirement in your own words:

- What user-visible or technical problem must be solved?
- What behavior is expected after the fix?
- What cases are explicitly in or out of scope?
- What tests or evidence would prove the fix?

Do not approve merge-readiness if the underlying issue is missing, inaccessible, invalid, stale, superseded, or contradicted by discussion.

### 4. Verify the Solution

Review the diff and relevant surrounding code. Check whether:

- The code path changed is the one exercised by the issue.
- The fix covers the reported reproduction path and important edge cases.
- The implementation avoids regressions in adjacent behavior.
- Tests were added or updated at the right level. When tests are absent, decide whether that is acceptable based on risk and project norms.
- Existing CI or local test results support the change.

When feasible, run focused tests or static checks. If you cannot run them, state that explicitly and base the verdict on code review evidence.

### 5. Assess Code Quality

Evaluate the code according to the language, framework, and repository conventions:

- Correctness, error handling, concurrency, security, and data validation.
- Simplicity and maintainability.
- Consistency with existing architecture and naming.
- Backward compatibility, migrations, configuration, and documentation when relevant.
- Avoidance of unrelated refactors or behavior changes.

Review comments already raised by humans should be treated as part of the quality bar. A PR with unresolved blocking review comments is not merge-ready unless the comments are clearly obsolete or non-blocking.

### 6. Present Findings to the User

After completing the review, compile and present all findings clearly:

- Summarize the key issues discovered, organized by severity (blocking vs. non-blocking).
- For each issue, reference the specific evidence: which file, what behavior, which reviewer comment, or what issue-discussion revealed it.
- Include positive findings too — what the PR does well, what tests are properly written, what edge cases are handled.
- Present the findings in a structured format so you and the user have a shared understanding of what needs attention.

**Important: Do not automatically fix any issues found during review.** The review skill is for evaluation only. If the user wants issues addressed, they will explicitly ask you to proceed. At that point, switch to the appropriate fix or create-pr workflow — do not assume you should fix everything you find.

## Verdict Rules

Return exactly one primary verdict:

- `Can merge`: The linked issue or requirement is valid, the implementation solves it, quality is acceptable, and no blocking concerns remain.
- `Cannot merge`: The issue is invalid or unverified, the implementation does not solve the requirement, important cases are missing, quality is below the project bar, tests or evidence are insufficient for the risk, CI is failing for relevant reasons, or blocking comments remain.

If evidence is incomplete for a mandatory part of the workflow, use `Cannot merge` and explain what must be checked or fixed before approval.

## Output Format

Start with the verdict, then provide concise evidence:

```markdown
Verdict: Can merge | Cannot merge

Requirement: <one-paragraph summary of the validated issue or PR goal>

Evidence:
- <what was reviewed and what supports the verdict>

Findings:
- <concise list of issues found during review, drawing from reviewer comments, linked issues, code quality assessment, and test results>

Blocking issues:
- <required fixes if cannot merge; use "None" if can merge>

Non-blocking notes:
- <optional improvements, risks, or test gaps>
```

For `Cannot merge`, be specific: name the file, behavior, missing test, unresolved comment, failing check, or issue-discussion mismatch that must be addressed.
