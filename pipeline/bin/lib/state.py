#!/usr/bin/env python3
"""Durable state for the pipeline: findings, fingerprints, and issue links.

State is what makes a daily run compound instead of repeating itself. Every
finding gets a stable fingerprint, so a repeat scan recognises what it already
reported (bumping `seen_count`) and only surfaces genuinely new gaps.

Subcommands:
  merge        --repo R --findings F   fold a scan result into state
  pending      --repo R                findings not yet turned into issues
  titles       --repo R                what is already known, for the prompt
  record-issue --repo R --fingerprint FP --issue URL
  status                               one line per repo, for humans

All subcommands take --state-dir (default: $PIPELINE_STATE_DIR or ./state).
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys

STATUS_NEW = "new"
STATUS_ISSUED = "issued"


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slug(repo):
    return repo.replace("/", "__")


def normalize_title(title):
    """Fold cosmetic rewording so the same gap keeps one fingerprint."""
    text = title.lower().strip()
    text = re.sub(r"[^a-z0-9一-鿿]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fingerprint(repo, title, area):
    payload = f"{repo}|{normalize_title(title)}|{area}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def repo_dir(state_dir, repo):
    path = os.path.join(state_dir, slug(repo))
    os.makedirs(path, exist_ok=True)
    return path


def load_findings(state_dir, repo):
    path = os.path.join(repo_dir(state_dir, repo), "findings.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_findings(state_dir, repo, records):
    path = os.path.join(repo_dir(state_dir, repo), "findings.json")
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def cmd_merge(args):
    with open(args.findings, encoding="utf-8") as fh:
        scan = json.load(fh)

    repo = args.repo or scan.get("repo")
    if not repo:
        print("merge: no repo given and none in the findings file", file=sys.stderr)
        return 2
    if scan.get("repo") and scan["repo"] != repo:
        print(
            f"merge: findings claim repo {scan['repo']!r} but this run scanned {repo!r}",
            file=sys.stderr,
        )
        return 1

    records = load_findings(args.state_dir, repo)
    stamp = now()
    new_count = 0

    for finding in scan.get("findings", []):
        fp = fingerprint(repo, finding["title"], finding["area"])
        existing = records.get(fp)
        if existing:
            existing["last_seen"] = stamp
            existing["seen_count"] = existing.get("seen_count", 1) + 1
            # Keep the freshest wording; the gap is the same, the phrasing may
            # have improved.
            existing["rationale"] = finding["rationale"]
            existing["proposal"] = finding["proposal"]
            existing["evidence"] = finding.get("evidence", [])
            continue
        records[fp] = {
            "fingerprint": fp,
            "repo": repo,
            "title": finding["title"],
            "area": finding["area"],
            "severity": finding["severity"],
            "rationale": finding["rationale"],
            "proposal": finding["proposal"],
            "evidence": finding.get("evidence", []),
            "labels": finding.get("labels", []),
            "first_seen": stamp,
            "last_seen": stamp,
            "seen_count": 1,
            "status": STATUS_NEW,
            "issue_url": "",
        }
        new_count += 1

    save_findings(args.state_dir, repo, records)
    pending = [r for r in records.values() if r["status"] == STATUS_NEW]
    summary = {
        "repo": repo,
        "new": new_count,
        "pending": len(pending),
        "total": len(records),
        "scanned_at": stamp,
    }
    json.dump(summary, sys.stdout, ensure_ascii=False)
    print()
    return 0


def _sort_key(record):
    order = {"high": 0, "medium": 1, "low": 2}
    return (order.get(record["severity"], 3), -record.get("seen_count", 1), record["title"])


def cmd_pending(args):
    records = load_findings(args.state_dir, args.repo)
    pending = sorted(
        (r for r in records.values() if r["status"] == STATUS_NEW), key=_sort_key
    )
    if args.limit:
        pending = pending[: args.limit]
    json.dump(pending, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


def cmd_titles(args):
    """Markdown bullet list of what we already know, for the scan prompt."""
    records = load_findings(args.state_dir, args.repo)
    if not records:
        print("(nothing reported yet — this is the first scan of this repository)")
        return 0
    for record in sorted(records.values(), key=_sort_key):
        marker = record["issue_url"] or record["status"]
        print(f"- {record['title']} [{record['area']}/{record['severity']}, {marker}]")
    return 0


def cmd_record_issue(args):
    records = load_findings(args.state_dir, args.repo)
    record = records.get(args.fingerprint)
    if not record:
        print(f"record-issue: unknown fingerprint {args.fingerprint}", file=sys.stderr)
        return 1
    record["status"] = STATUS_ISSUED
    record["issue_url"] = args.issue
    record["issued_at"] = now()
    save_findings(args.state_dir, args.repo, records)
    return 0


def cmd_status(args):
    if not os.path.isdir(args.state_dir):
        print("no state yet — run a scan first")
        return 0
    rows = []
    for entry in sorted(os.listdir(args.state_dir)):
        path = os.path.join(args.state_dir, entry, "findings.json")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            records = json.load(fh)
        if not records:
            continue
        values = list(records.values())
        rows.append(
            {
                "repo": values[0]["repo"],
                "total": len(values),
                "pending": sum(1 for r in values if r["status"] == STATUS_NEW),
                "issued": sum(1 for r in values if r["status"] == STATUS_ISSUED),
                "last_seen": max(r["last_seen"] for r in values),
            }
        )
    if not rows:
        print("no state yet — run a scan first")
        return 0
    if args.json:
        json.dump(rows, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 0
    width = max(len(r["repo"]) for r in rows)
    print(f"{'REPO'.ljust(width)}  TOTAL  PENDING  ISSUED  LAST SCAN")
    for row in rows:
        print(
            f"{row['repo'].ljust(width)}  {row['total']:>5}  {row['pending']:>7}  "
            f"{row['issued']:>6}  {row['last_seen']}"
        )
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-dir",
        default=os.environ.get("PIPELINE_STATE_DIR", "state"),
        help="where findings are kept (default: $PIPELINE_STATE_DIR or ./state)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    merge = sub.add_parser("merge", help="fold a scan result into state")
    merge.add_argument("--repo")
    merge.add_argument("--findings", required=True)
    merge.set_defaults(func=cmd_merge)

    pending = sub.add_parser("pending", help="findings not yet turned into issues")
    pending.add_argument("--repo", required=True)
    pending.add_argument("--limit", type=int, default=0)
    pending.set_defaults(func=cmd_pending)

    titles = sub.add_parser("titles", help="markdown list of known findings")
    titles.add_argument("--repo", required=True)
    titles.set_defaults(func=cmd_titles)

    record = sub.add_parser("record-issue", help="link a finding to the issue it became")
    record.add_argument("--repo", required=True)
    record.add_argument("--fingerprint", required=True)
    record.add_argument("--issue", required=True)
    record.set_defaults(func=cmd_record_issue)

    status = sub.add_parser("status", help="one line per repo")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
