#!/usr/bin/env python3
"""Render a prompt template: replace {{name}} with values from a JSON object.

Usage: render.py <template.md> <values.json>
Unknown placeholders are an error — a silently empty placeholder produces a
prompt that looks fine and scans the wrong thing.
"""
import json
import re
import sys

PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8") as fh:
        template = fh.read()
    with open(sys.argv[2], encoding="utf-8") as fh:
        values = json.load(fh)

    missing = []

    def substitute(match):
        key = match.group(1)
        if key not in values:
            missing.append(key)
            return match.group(0)
        value = values[key]
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        return "" if value is None else str(value)

    rendered = PLACEHOLDER.sub(substitute, template)
    if missing:
        print(
            f"template {sys.argv[1]} needs values for: {', '.join(sorted(set(missing)))}",
            file=sys.stderr,
        )
        return 1
    sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
