#!/usr/bin/env python3
"""Validate a JSON document against the subset of JSON Schema this pipeline uses.

Deliberately dependency-free: the pipeline must run on any machine with a
stock python3, without asking the user to pip install anything first.

Supported keywords: type, required, properties, additionalProperties, items,
enum, pattern, minLength, maxLength, minItems, maxItems.

Usage: validate.py <schema.json> <document.json>
Exits 0 when valid; prints every error to stderr and exits 1 otherwise.
"""
import json
import re
import sys

TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "null": type(None),
}


def validate(node, schema, path, errors):
    expected = schema.get("type")
    if expected:
        py_type = TYPES[expected]
        # bool is a subclass of int in Python; keep them distinct here.
        if isinstance(node, bool) and expected in ("number", "integer"):
            errors.append(f"{path}: expected {expected}, got boolean")
            return
        if not isinstance(node, py_type):
            errors.append(f"{path}: expected {expected}, got {type(node).__name__}")
            return

    if "enum" in schema and node not in schema["enum"]:
        errors.append(f"{path}: {node!r} is not one of {schema['enum']}")

    if isinstance(node, str):
        if "minLength" in schema and len(node) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']} (got {len(node)})")
        if "maxLength" in schema and len(node) > schema["maxLength"]:
            errors.append(f"{path}: longer than maxLength {schema['maxLength']} (got {len(node)})")
        if "pattern" in schema and not re.search(schema["pattern"], node):
            errors.append(f"{path}: {node!r} does not match pattern {schema['pattern']}")

    if isinstance(node, list):
        if "minItems" in schema and len(node) < schema["minItems"]:
            errors.append(f"{path}: fewer than minItems {schema['minItems']}")
        if "maxItems" in schema and len(node) > schema["maxItems"]:
            errors.append(f"{path}: more than maxItems {schema['maxItems']}")
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(node):
                validate(item, item_schema, f"{path}[{i}]", errors)

    if isinstance(node, dict):
        for key in schema.get("required", []):
            if key not in node:
                errors.append(f"{path}: missing required property {key!r}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in node:
                if key not in props:
                    errors.append(f"{path}: unexpected property {key!r}")
        for key, sub_schema in props.items():
            if key in node:
                validate(node[key], sub_schema, f"{path}.{key}", errors)


def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    schema_path, doc_path = sys.argv[1], sys.argv[2]
    with open(schema_path, encoding="utf-8") as fh:
        schema = json.load(fh)
    try:
        with open(doc_path, encoding="utf-8") as fh:
            document = json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"not valid JSON: {exc}", file=sys.stderr)
        return 1

    errors = []
    validate(document, schema, "$", errors)
    for error in errors:
        print(f"schema error: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
