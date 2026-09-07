#!/usr/bin/env python3
"""Read pipeline/config/repos.yaml and emit the resolved repo list as JSON.

Uses PyYAML when it is installed; otherwise falls back to a small parser that
understands exactly the subset of YAML this config file uses (two-level block
mappings, a block sequence of mappings, scalars, and inline [a, b] lists).
The fallback exists so the pipeline runs on a stock python3 with no pip step.

Usage:
  config.py <repos.yaml>                 # all repos, JSON array on stdout
  config.py <repos.yaml> --repo owner/x  # just that one (exit 1 if unknown)
"""
import json
import sys

SCALAR_DEFAULTS = {"true": True, "false": False, "null": None, "~": None}


def _scalar(raw):
    text = raw.strip()
    if not text:
        return ""
    if text[0] in "\"'" and text[-1] == text[0] and len(text) > 1:
        return text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        return [_scalar(part) for part in inner.split(",")] if inner else []
    lowered = text.lower()
    if lowered in SCALAR_DEFAULTS:
        return SCALAR_DEFAULTS[lowered]
    try:
        return int(text)
    except ValueError:
        return text


def _strip_comment(line):
    out, quote = [], None
    for ch in line:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _lines(text):
    out = []
    for raw in text.splitlines():
        line = _strip_comment(raw)
        if line.strip():
            out.append((len(line) - len(line.lstrip(" ")), line.strip()))
    return out


def _parse_block(lines, i, indent):
    """Parse one block (mapping or sequence) starting at lines[i]."""
    if i >= len(lines):
        return None, i

    if lines[i][1].startswith("- "):
        items = []
        while i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
            inline = lines[i][1][2:].strip()
            sub = [(indent + 2, inline)] if inline else []
            i += 1
            while i < len(lines) and lines[i][0] > indent:
                sub.append(lines[i])
                i += 1
            items.append(_parse_block(sub, 0, sub[0][0])[0] if sub else None)
        return items, i

    mapping = {}
    while i < len(lines) and lines[i][0] == indent and not lines[i][1].startswith("- "):
        body = lines[i][1]
        if ":" not in body:
            raise ValueError(f"expected 'key: value', got {body!r}")
        key, _, raw = body.partition(":")
        key, raw = key.strip(), raw.strip()
        i += 1
        if raw in ("|", "|-", "|+", ">", ">-", ">+"):
            block = []
            while i < len(lines) and lines[i][0] > indent:
                block.append(lines[i][1])
                i += 1
            joiner = "\n" if raw.startswith("|") else " "
            mapping[key] = joiner.join(block)
            continue
        if raw:
            mapping[key] = _scalar(raw)
            continue
        # A key with no inline value opens a nested block. A block sequence may
        # sit at the same indent as its key, so accept that too.
        sub = []
        while i < len(lines) and (
            lines[i][0] > indent
            or (lines[i][0] == indent and lines[i][1].startswith("- "))
        ):
            sub.append(lines[i])
            i += 1
        mapping[key] = _parse_block(sub, 0, sub[0][0])[0] if sub else None
    return mapping, i


def _mini_yaml(text):
    """Parse the restricted YAML shape used by repos.yaml."""
    lines = _lines(text)
    if not lines:
        return {}
    value, _ = _parse_block(lines, 0, lines[0][0])
    return value or {}


def load(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    try:
        import yaml  # noqa: PLC0415 - optional dependency by design
    except ImportError:
        return _mini_yaml(text)
    return yaml.safe_load(text) or {}


def resolve(config):
    defaults = config.get("defaults") or {}
    resolved = []
    for entry in config.get("repos") or []:
        if not isinstance(entry, dict) or "repo" not in entry:
            raise ValueError(f"each repos[] entry needs a 'repo: owner/name' key, got {entry!r}")
        merged = dict(defaults)
        merged.update({k: v for k, v in entry.items() if v is not None})
        if merged["repo"].count("/") != 1:
            raise ValueError(f"repo must be owner/name, got {merged['repo']!r}")
        merged.setdefault("path", "")
        merged.setdefault("focus", "")
        merged.setdefault("labels", [])
        merged.setdefault("max_issues_per_run", 3)
        resolved.append(merged)
    return resolved


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__, file=sys.stderr)
        return 2
    path = args[0]
    wanted = None
    if "--repo" in args:
        wanted = args[args.index("--repo") + 1]
    try:
        repos = resolve(load(path))
    except (ValueError, KeyError) as exc:
        print(f"config error in {path}: {exc}", file=sys.stderr)
        return 2
    if wanted:
        repos = [r for r in repos if r["repo"] == wanted]
        if not repos:
            print(f"config error: {wanted} is not listed in {path}", file=sys.stderr)
            return 1
    json.dump(repos, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
