#!/usr/bin/env python3
"""Turn pending findings into issue drafts.

Deterministic by default: the scan already produced structured fields, so
rendering them into an issue needs no second model call (and no second bill).
The optional --enrich path in triage.sh replaces the body with an agent-written
one when a finding deserves the extra care.

Usage:
  issue.py drafts --repo R [--state-dir D] [--limit N] [--labels a,b]
  issue.py render --draft <draft.json> --body-out <file>
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state  # noqa: E402  (local helper, path set above)

SEVERITY_LABEL = {"high": "priority:high", "medium": "priority:medium", "low": "priority:low"}


def render_body(record):
    lines = [
        "## Context",
        "",
        f"Reported by the maintenance pipeline scan (first seen {record['first_seen']}, "
        f"seen in {record.get('seen_count', 1)} scan(s)).",
        "",
        "## Problem",
        "",
        record["rationale"],
        "",
        "## Proposed change",
        "",
        record["proposal"],
        "",
    ]
    if record.get("evidence"):
        lines += ["## Evidence", ""]
        lines += [f"- `{item}`" for item in record["evidence"]]
        lines.append("")
    lines += [
        "## Acceptance criteria",
        "",
        "- [ ] The problem above no longer reproduces",
        "- [ ] The change is covered by a test or an explicit note on why it cannot be",
        "",
        "---",
        "",
        f"<sub>area: {record['area']} · severity: {record['severity']} · "
        f"pipeline-fingerprint: `{record['fingerprint']}`</sub>",
    ]
    return "\n".join(lines)


def cmd_drafts(args):
    records = state.load_findings(args.state_dir, args.repo)
    pending = sorted(
        (r for r in records.values() if r["status"] == state.STATUS_NEW),
        key=state._sort_key,
    )
    if args.limit:
        pending = pending[: args.limit]

    extra = [label for label in (args.labels or "").split(",") if label]
    drafts = []
    for record in pending:
        labels = list(dict.fromkeys(extra + record.get("labels", []) + [SEVERITY_LABEL[record["severity"]]]))
        drafts.append(
            {
                "fingerprint": record["fingerprint"],
                "repo": record["repo"],
                "title": record["title"],
                "body": render_body(record),
                "labels": labels,
                "severity": record["severity"],
                "area": record["area"],
                "seen_count": record.get("seen_count", 1),
                "first_seen": record["first_seen"],
                "rationale": record["rationale"],
                "proposal": record["proposal"],
                "evidence": record.get("evidence", []),
            }
        )
    json.dump(drafts, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


def cmd_render(args):
    with open(args.draft, encoding="utf-8") as fh:
        draft = json.load(fh)
    with open(args.body_out, "w", encoding="utf-8") as fh:
        fh.write(draft["body"])
        fh.write("\n")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-dir", default=os.environ.get("PIPELINE_STATE_DIR", "state")
    )
    sub = parser.add_subparsers(dest="command", required=True)

    drafts = sub.add_parser("drafts", help="issue drafts for pending findings")
    drafts.add_argument("--repo", required=True)
    drafts.add_argument("--limit", type=int, default=0)
    drafts.add_argument("--labels", default="")
    drafts.set_defaults(func=cmd_drafts)

    render = sub.add_parser("render", help="write a draft body to a file")
    render.add_argument("--draft", required=True)
    render.add_argument("--body-out", required=True)
    render.set_defaults(func=cmd_render)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
