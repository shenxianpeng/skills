#!/usr/bin/env python3
"""Pull the result JSON out of an agent's free-form output.

Agents narrate. The contract is that the *last* fenced ```json block is the
result; if there is no fenced block we fall back to the last balanced {...}
run in the text. Anything else is a contract violation and fails loudly.

Usage: extract_json.py <agent-output.txt>
"""
import json
import re
import sys

FENCED = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)


def balanced_objects(text):
    """Yield every balanced {...} run, ignoring braces inside strings."""
    depth = 0
    start = None
    in_string = False
    escape = False
    quote = ""
    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_string = False
            continue
        if ch in "\"'":
            in_string, quote = True, ch
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth:
                depth -= 1
                if depth == 0 and start is not None:
                    yield text[start : i + 1]


def main():
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8", errors="replace") as fh:
        text = fh.read()

    candidates = FENCED.findall(text) or list(balanced_objects(text))
    for candidate in reversed(candidates):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            json.dump(parsed, sys.stdout, ensure_ascii=False, indent=2)
            print()
            return 0

    print(
        f"no parsable JSON object in agent output ({sys.argv[1]}); "
        "the agent did not honour the output contract",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
