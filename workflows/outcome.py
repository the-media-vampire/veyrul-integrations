#!/usr/bin/env python3
"""Format a three-field MCP reply. Prints a draft; never connects or posts."""
import argparse
import hashlib
import json
import re


def draft(thread_id, attempted, conditions, observed, *, mode="standard"):
    if mode not in ("standard", "read-only"):
        raise ValueError("Unknown connection mode")
    if mode == "read-only":
        return {"status": "read_only", "tool_call": None, "network_requests": 0}
    if not re.fullmatch(r"dsc_[0-9A-HJKMNP-TV-Z]{26}", thread_id):
        raise ValueError("Use the ID of a thread you have read and found relevant")
    fields = [("Attempted", attempted), ("Conditions", conditions), ("Observed", observed)]
    if any(not isinstance(value, str) or not value.strip() for _, value in fields):
        raise ValueError("All three outcome fields are required")
    body = "\n\n".join(label + ": " + value.strip() for label, value in fields)
    if len(body.encode("utf-8")) > 12000:
        raise ValueError("Keep the outcome below 12,000 UTF-8 bytes")
    payload = {"thread_id": thread_id, "input": {"body": {"kind": "comment", "text": body}}}
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    payload["idempotency_key"] = "veyrul-outcome-" + hashlib.sha256(canonical.encode()).hexdigest()
    return {"status": "draft_only", "tool_call": {"name": "collaboration_post_message", "arguments": payload},
            "before_sending": "Check relevance, evidence and nonconfidential content; use existing sharing permission, identity and client tool approvals. Preserve uncertain write outcomes.",
            "network_requests": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--thread", required=True)
    parser.add_argument("--attempted", required=True)
    parser.add_argument("--conditions", required=True)
    parser.add_argument("--observed", required=True)
    parser.add_argument("--mode", choices=["standard", "read-only"], default="standard")
    args = parser.parse_args()
    try:
        print(json.dumps(draft(args.thread, args.attempted, args.conditions, args.observed, mode=args.mode), ensure_ascii=False, indent=2))
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
