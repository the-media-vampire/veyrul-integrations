#!/usr/bin/env python3
"""Read compact public Veyrul context. Python 3.9+, standard library only."""
import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MAX_BYTES = 262144


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Unexpected redirect; no alternate endpoint was contacted")


def lookup(query, internal_check=False):
    if not 1 <= len(query.strip()) <= 500:
        raise ValueError("Use a generic query of 1 to 500 characters")
    params = urllib.parse.urlencode({"q": query.strip(), "detail": "compact", "limit": "3"})
    headers = {"Accept": "application/json", "User-Agent": "Veyrul-Remotion-Context/0.1"}
    if internal_check:
        headers.update({"User-Agent": "Veyrul-Internal-Distribution-Check/1", "X-Veyrul-Segment": "synthetic"})
    request = urllib.request.Request("https://veyrul.com/v1/context?" + params, headers=headers, method="GET")
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(request, timeout=12) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Response exceeded the 256 KiB limit")
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema") != "context/v1" or not isinstance(value.get("records"), list):
        raise ValueError("Unexpected context response; use primary documentation")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Generic media question; do not include private project content")
    parser.add_argument("--output", type=Path, help="Write to a new JSON file instead of stdout")
    parser.add_argument("--internal-check", action="store_true", help="Mark developer verification traffic as synthetic")
    args = parser.parse_args()
    if args.output and (args.output.exists() or args.output.is_symlink()):
        parser.error("Output already exists; choose a new file")
    try:
        value = lookup(args.query, args.internal_check)
        text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as target:
                target.write(text)
        else:
            print(text, end="")
    except (OSError, ValueError, urllib.error.URLError) as error:
        print("Lookup unavailable: {}. No automatic retry; continue with your normal sources.".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
