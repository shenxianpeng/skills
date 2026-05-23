# Skills

A collection of agent skills for various tasks.

## Installation

Install a specific skill with the `skills` CLI:

```bash
npx skills add shenxianpeng/skills --skill github-review -a codex -g
```

To install for Claude Code instead:

```bash
npx skills add shenxianpeng/skills --skill github-review -a claude-code -g
```

You can also install manually by copying the skill directory into your agent's global skills folder:

```bash
git clone https://github.com/shenxianpeng/skills.git /tmp/shenxianpeng-skills
mkdir -p ~/.codex/skills
cp -R /tmp/shenxianpeng-skills/skills/github-review ~/.codex/skills/
```

## Available Skills

### Weekly Newsletter ([.claude/skills/weekly/](.claude/skills/weekly/))

A comprehensive toolkit for automating tech weekly newsletter generation, including content searching, GitHub project verification, link validation, and image management. Covers AI, DevOps, open-source, and tech industry updates.

### Technical Blog Writing ([.claude/skills/technical-blog-writing/](.claude/skills/technical-blog-writing/))

Technical blog post writing with structure, code examples, and developer audience conventions. Covers post types (tutorials, deep dives, postmortems, benchmarks, architecture posts), code formatting, explanation depth, and developer-specific engagement patterns.

### GitHub Review ([skills/github-review/](skills/github-review/))

Review GitHub pull requests for merge readiness by reading PR context, tracking linked issues, validating requirements, checking implementation correctness, and assessing code quality.

## Standards

All skills follow the [Agent Skills Specification](https://agentskills.io/specification) for compatibility and best practices.
