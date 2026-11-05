"""Read-only DTCG 2025.10 dimension/duration/cubicBezier handoff check.

This is a bounded subset check, not a full schema validator or a converter.
No network requests, installations, imports into design tools or file writes.
"""
import argparse
import json
import math
from pathlib import Path
import re

MAX_BYTES = 1048576
MAX_NODES = 10000
MAX_DEPTH = 32
TYPES = {"dimension", "duration", "cubicBezier"}
REFERENCE = re.compile(r"^\{([^{}]+)\}$")


def number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def check(document):
    if not isinstance(document, dict):
        raise ValueError("root_must_be_object")
    # Do not misclassify legal reference/extension mechanisms as malformed
    # scalar values. This small checker deliberately does not resolve them.
    pending, inspected, unsupported = [(document, 0)], 0, set()
    while pending:
        node, depth = pending.pop()
        inspected += 1
        if inspected > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError("document_bound")
        if isinstance(node, dict):
            unsupported.update(key for key in ("$ref", "$extends") if key in node)
            pending.extend((value, depth + 1) for value in node.values() if isinstance(value, (dict, list)))
        elif isinstance(node, list):
            pending.extend((value, depth + 1) for value in node if isinstance(value, (dict, list)))
    if unsupported:
        return {"status": "unsupported_features", "full_conformance": False,
                "checked": 0, "unchecked_types": [], "issues": [],
                "unsupported_features": sorted(unsupported),
                "scope": "Only direct values and brace-form typed aliases; no $ref or $extends resolution"}
    tokens, issues, unchecked = {}, [], set()
    visited = 0

    def walk(node, path=(), inherited=None, depth=0):
        nonlocal visited
        visited += 1
        if visited > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError("document_bound")
        if not isinstance(node, dict):
            return
        kind = node.get("$type", inherited)
        if kind is not None and not isinstance(kind, str):
            raise ValueError("type_must_be_string")
        if "$value" in node:
            tokens[".".join(path)] = (kind, node["$value"])
            return
        for key, child in node.items():
            if not key.startswith("$"):
                walk(child, path + (key,), kind, depth + 1)

    walk(document)

    def resolve(path, kind, seen):
        for _ in range(MAX_DEPTH):
            if path in seen:
                raise ValueError("reference_cycle")
            if path not in tokens:
                raise ValueError("reference_missing")
            seen.add(path)
            actual, value = tokens[path]
            if actual != kind:
                raise ValueError("reference_type_mismatch")
            ref = REFERENCE.fullmatch(value) if isinstance(value, str) else None
            if not ref:
                return value
            path = ref.group(1)
        raise ValueError("reference_bound")

    checked = 0
    for path, (kind, _) in tokens.items():
        if kind not in TYPES:
            unchecked.add(str(kind) if kind is not None else "missing_type")
            continue
        checked += 1
        try:
            value = resolve(path, kind, set())
        except ValueError as exc:
            issues.append({"path": path, "code": str(exc)})
            continue
        if kind in ("dimension", "duration"):
            units = ("px", "rem") if kind == "dimension" else ("ms", "s")
            valid = isinstance(value, dict) and number(value.get("value")) and value.get("unit") in units
            if not valid:
                issues.append({"path": path, "code": kind + "_requires_value_unit_object"})
        else:
            valid = isinstance(value, list) and len(value) == 4 and all(number(x) for x in value)
            if not valid:
                issues.append({"path": path, "code": "cubicBezier_requires_four_numbers"})
            elif not (0 <= value[0] <= 1 and 0 <= value[2] <= 1):
                issues.append({"path": path, "code": "cubicBezier_x_out_of_range"})
    return {
        "status": "subset_failed" if issues else "subset_passed" if checked else "no_supported_tokens",
        "scope": "DTCG 2025.10 dimension, duration, cubicBezier and their same-document brace-form typed aliases",
        "full_conformance": False,
        "checked": checked,
        "unchecked_types": sorted(unchecked),
        "issues": issues,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tokens", type=Path)
    args = parser.parse_args()
    try:
        with args.tokens.open("rb") as source:
            raw = source.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("file_bound")
        document = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")))
        result = check(document)
    except (OSError, ValueError, RecursionError):
        print(json.dumps({"status": "input_refused", "full_conformance": False}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "subset_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
