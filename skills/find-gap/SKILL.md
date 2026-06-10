---
name: find-gap
description: Analyze a project (GitHub repository or product) to identify gaps vs. competitors and unmet market needs. Use this skill whenever the user wants to find gaps, do competitive analysis, benchmark their project, discover market opportunities, understand where their product falls short, or get a strategic improvement plan. Triggers on phrases like "find gaps", "gap analysis", "competitive analysis", "how can I improve my project", "what am I missing", "benchmark my project", "product gaps", or when the user provides a project link and asks for improvement ideas.
---

# Find Gap

## Purpose

Act as a product strategist and technical analyst to evaluate a project holistically: score it against objective criteria, compare it with competitors, surface unmet market needs from real community discussions, and produce a focused gap report that tells the user exactly where to invest effort next.

This skill is broader than internal code-quality audits — it looks outward at the competitive landscape and inward at the project's own strengths and weaknesses, then synthesizes both perspectives into actionable gaps.

## Inputs

The user must provide at least one of:

- A **GitHub repository URL** (e.g., `https://github.com/owner/repo`)
- An **owner/repo** pair (e.g., `owner/repo`)
- A **product URL or name** that can be researched online

Optional context the user may add (ask if ambiguous):

- What kind of users does the project serve (developers, end users, enterprises, etc.)?
- Any known competitors the user already has in mind?
- Specific concerns or areas the user is most worried about?

If no project is specified, look at the current working directory's Git remote and ask for confirmation.

## Workflow

Execute these phases in order. Each phase builds on the last.

---

### Phase 1: Project Discovery & Understanding

Before scoring or comparing, build a solid understanding of the project. Do not skip or rush this — superficial understanding leads to superficial gaps.

**What to read (for GitHub repos):**

- README.md — the project's self-description, target audience, and value proposition
- Documentation files (docs/, wiki, website links)
- Source code structure — top-level directories, entry points, key modules
- Package metadata (package.json, Cargo.toml, setup.py, go.mod, etc.) — dependencies and ecosystem signals
- Changelog, release notes, or version history
- Open and closed issues — what users are complaining about or requesting
- CI/CD configuration — testing and deployment maturity
- Contributing guide, security policy, code of conduct

**What to understand before proceeding:**

- What problem does this project solve? For whom?
- What is its current maturity level (early-stage, stable, legacy)?
- What tech stack does it use?
- How active is development?

If the project is not a GitHub repo but a web product, explore its website, documentation, and any public roadmap or changelog instead.

---

### Phase 2: Project Scoring (100-Point Scale)

Score the project across four dimensions. For each dimension, provide a numeric score, specific evidence from what you observed in Phase 1, and a brief rationale.

#### Scoring Dimensions and Weights

| Dimension | Max Points | Weight | What to Evaluate |
|-----------|-----------|--------|-----------------|
| **Functional Completeness** | 35 | 35% | Does the project deliver on its core promises? Are there missing features that users would reasonably expect? How does the feature set compare to the stated goals in the README? Are there obvious functional gaps (e.g., promised integrations that don't exist, documented features that are stubs)? |
| **Code Quality** | 25 | 25% | Is the code well-structured, readable, and maintainable? Are there tests? Is there static analysis or linting? Is error handling adequate? Are there obvious security concerns, hardcoded secrets, or unsafe defaults? Does CI pass consistently? |
| **Documentation Quality** | 20 | 20% | Is there a clear quickstart guide? Are installation instructions accurate? Is the API documented? Are there usage examples, tutorials, or demos? Is there architecture documentation? Can a new user go from zero to working in under 10 minutes? |
| **User Experience** | 20 | 20% | How easy is it to install, configure, and use? Is the CLI intuitive? Is the API ergonomic? Are error messages helpful? Is onboarding smooth? This applies to developer tools (DX) as much as end-user products. |

#### Scoring Guidelines

- **30-35 (Excellent)**: Near-complete, competitive with best-in-class, few if any gaps
- **20-29 (Good)**: Solid, covers the essentials well, some room for improvement
- **10-19 (Fair)**: Basic coverage, noticeable gaps, workable but rough
- **0-9 (Poor)**: Major gaps, missing essentials, hard to use or unreliable

Score each dimension based on what's reasonable for the project's maturity and stated scope. An early-stage project with a clear README and working prototype might score high on documentation even if features are incomplete. A mature project with missing tests should score lower on code quality regardless of its feature set.

**Present scores like this:**

```markdown
## Project Score: <total>/100

| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Functional Completeness | 24/35 | 35% | 24.0 |
| Code Quality | 18/25 | 25% | 18.0 |
| Documentation Quality | 14/20 | 20% | 14.0 |
| User Experience | 15/20 | 20% | 15.0 |
| **Total** | | | **71.0/100** |
```

Below the table, write a paragraph for each dimension explaining the score with concrete evidence.

---

### Phase 3: Competitor Analysis

Find and analyze competing or adjacent projects. The goal is not an exhaustive list but a focused set of 3-7 meaningful competitors whose strengths reveal gaps in the user's project.

#### 3a. GitHub Search

Search GitHub for repositories with similar descriptions, topics, or functionality:

```bash
gh search repos "<project-name> <keywords>" --sort stars --limit 10
gh search repos "topic:<relevant-topic>" --sort stars --limit 10
```

If `gh` is unavailable, use GitHub's web search: `https://github.com/search?q=<keywords>&type=repositories&s=stars`

Look for repositories that:
- Solve the same or similar problem
- Share the same tech stack or ecosystem
- Target the same audience
- Are frequently mentioned as alternatives in issues or discussions

#### 3b. Web Search

Search broadly for commercial and open-source competitors:

- **Google/Bing search**: `"<project category> alternatives"`, `"<project name> vs"`, `"best <category> tools 2025"`
- **Product Hunt**: `site:producthunt.com <project category>`
- **GitHub awesome lists**: `awesome <topic> site:github.com`
- **Comparison articles**: blog posts and review sites that compare tools in this space

#### 3c. Competitor Deep-Dive

For each competitor found, quickly assess:

- **What they do well**: features, UX, documentation, community, performance
- **What the user's project does better**: identify strengths to preserve and build on
- **What the user's project is missing**: features, polish, integrations, or positioning that competitors have

Present in a comparison table:

```markdown
## Competitor Landscape

| Competitor | Stars / Popularity | Key Strengths | What We're Missing |
|-----------|-------------------|---------------|-------------------|
| competitor-a | 5.2k ⭐ | ... | ... |
| competitor-b | 12k ⭐ | ... | ... |
```

---

### Phase 4: Market Demand Insights

Search real community discussions to understand what users actually want and what's currently unmet. This is where the most valuable gaps are found — not what competitors have, but what users are asking for that nobody has built yet.

#### 4a. Search Platforms and Strategies

Search each platform with queries tailored to the project's domain. Do not search all platforms if the project's audience is clearly concentrated on a few — focus where the users are.

**English-language platforms:**

| Platform | Search Strategy |
|----------|----------------|
| **Reddit** | `site:reddit.com <project category> recommendation` `site:reddit.com "looking for" <keywords>` `site:reddit.com "wish <tool> had"` |
| **Hacker News** | `site:news.ycombinator.com <project name>` `site:news.ycombinator.com "Ask HN" <keywords>` |
| **Product Hunt** | `site:producthunt.com <project category>` — look at comments for feature requests and complaints |
| **GitHub Issues** | Search the user's own repo AND competitor repos for feature requests, especially those with many 👍 reactions |
| **Discourse** | `site:<topic>.discourse.group <keywords>` — many open-source projects use Discourse for community |

**Chinese-language platforms:**

| Platform | Search Strategy |
|----------|----------------|
| **V2EX** | `site:v2ex.com <keywords> 推荐` `site:v2ex.com <keywords> 替代` `site:v2ex.com "有没有" <keywords>` |

#### 4b. Identifying Unmet Needs

As you read through discussions, extract:

1. **Pain points** — what frustrates users about existing solutions?
2. **Feature requests** — what do users consistently ask for that doesn't exist yet?
3. **Workarounds** — what hacks or multi-tool workflows are people using because no single tool solves the problem?
4. **Emerging demand** — are there new use cases or user segments that existing tools don't address?

Present findings as a ranked list with evidence links:

```markdown
## Market Demand Insights

### Unmet Needs (ranked by signal strength)

1. **[Need description]**
   - Signal: <3-5 links to discussions mentioning this>
   - Current workaround: <what people do now>
   - Opportunity: <why this is a gap worth filling>

2. ...
```

A strong signal = multiple independent discussions, high engagement (upvotes/comments), or repeated requests over time. A weak signal = a single thread with low engagement. Be transparent about signal strength.

---

### Phase 5: Gap Report

Compile everything into `GAP_ANALYSIS_REPORT.md`. Save it in the current working directory (or at a path the user specifies).

#### Report Structure

```markdown
# Gap Analysis Report: <Project Name>

> Generated on <date> | Analyzed by Find Gap

## 1. Executive Summary
<2-3 paragraphs: what the project is, overall score, top 3 gaps to address, and the single biggest opportunity>

## 2. Project Score: <total>/100
<Scoring table and dimension-by-dimension rationale from Phase 2>

## 3. Competitor Landscape
<Competitor comparison table and analysis from Phase 3>

## 4. Market Demand Insights
<Unmet needs with evidence links from Phase 4>

## 5. Top Gaps & Recommendations
<Prioritized list of gaps to address, combining internal scoring weaknesses, competitor advantages, and market demand signals>

## 6. Action Plan
<Suggested next steps, ordered by impact and feasibility. Include estimated effort (S/M/L) for each.>
```

#### Prioritization Logic

When prioritizing gaps in Section 5, weigh three factors together:

1. **Internal weakness** (from Phase 2 scoring) — areas where the project scored low
2. **Competitive pressure** (from Phase 3) — gaps that competitors already fill well
3. **Market pull** (from Phase 4) — gaps that users are actively asking for

A gap that scores high on all three is the most urgent. A gap with only one signal may be lower priority.

## Output Expectations

- **One file**: `GAP_ANALYSIS_REPORT.md` in the working directory
- **Evidence-based**: every score and insight should reference something concrete you actually found
- **Actionable**: every gap should be specific enough that the user knows what to do next
- **Honest**: do not inflate scores or fabricate competitor strengths. If the project is genuinely strong, say so. If data is sparse, say so.
- **Language**: write the report in the same language the user communicates in (Chinese or English). Default to Chinese if the user writes in Chinese.

## Guardrails

- Do not fabricate competitor data or user discussions. If a search returns nothing useful, say "no significant competitor found" or "no relevant community discussions found" — that itself is a signal.
- Do not criticize the project or its maintainers in personal terms. Describe gaps as opportunities, not failures.
- When searching community platforms, respect rate limits. If a platform is inaccessible, note it and move on.
- The goal is insight, not exhaustive coverage. 3-7 competitors and 3-5 unmet needs is better than 20 shallow mentions.
