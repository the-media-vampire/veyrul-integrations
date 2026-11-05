# Check design tokens before handing them to another tool

An extractor can return useful CSS without returning the token format expected by
your destination. Check the declared format version and the receiving tool before
importing a website's design or motion tokens.

This Python 3 helper reads a local JSON file and checks **only dimension, duration,
cubicBezier, and their typed same-document aliases** against the DTCG 2025.10
value shapes. It makes no network request and changes no file.

```bash
python3 examples/design-token-handoff/check_tokens.py path/to/tokens.json
python3 -m unittest discover -s examples/design-token-handoff -p 'test_*.py'
```

Exit 0 means the supported subset passed, 1 means a subset failure or no supported
tokens, and 2 means the input was refused. The JSON result always says
`full_conformance: false`. Color, typography, shadows, extension fields, and
destination-specific support are not validated. Do not treat this as a complete
schema validator or import approval.

These examples use the current value shapes:

```json
{
  "space": {"$type": "dimension", "$value": {"value": 8, "unit": "px"}},
  "time": {"$type": "duration", "$value": {"value": 150, "unit": "ms"}},
  "spring": {"$type": "cubicBezier", "$value": [0.34, 1.56, 0.64, 1]}
}
```

The curve's y-coordinate overshoot is allowed. The first and third coordinates
must be between 0 and 1. CSS strings such as `"8px"`, `"150ms"`, `"ease"`, and
`"cubic-bezier(...)"` are not these typed values. A named CSS easing needs its
defined curve; a spring simulation needs a documented approximation. The checker
does not invent either conversion. See the
[DTCG 2025.10 community specification](https://www.designtokens.org/tr/2025.10/format/).

## Evidence and limits

At design-extract revision
[`6050fdb`](https://github.com/Manavarya09/design-extract/tree/6050fdb470d87c14f3db42a07ba782ca93286c75),
executing the two inspected pure formatter functions on synthetic input produced
CSS strings for the types above. Copy the companion `reproduce.mjs` into that pinned repository's root and run
`node reproduce.mjs` with Node 22.22.2 to print that case. No package install,
website crawl, Figma import, or browser render was performed for this finding.
Other consumers may support older formats; check which format they actually use.

The checker is bounded to 1 MiB, 10,000 visited nodes, 32 nesting levels and 32
alias links. It preserves the original input. After a corrected export passes,
test a small copy in the destination and inspect spacing and motion visually.
Share an outcome only when authorized, including exporter version, format
version, destination, exact error or result, and remaining limits.
