# Keep captions aligned after a Remotion edit

A small, optional production example: retrieve a useful timing resource from
Veyrul, use its reviewed code locally, and carry the result into a second edit.
It cuts, speeds up and repeats original silent diagnostic footage, with visible
word captions. The preparation and rendering steps work offline once dependencies
and the selected toolkit are present.

Veyrul supplies saved knowledge and resources. Your agent chooses the method
and runs Remotion. This example adds no hosted agent or media-generation service.

## Use with your agent

Install the optional companion in a project you control:

```bash
npx skills@1.5.22 add the-media-vampire/veyrul-integrations --skill veyrul-remotion-context
```

Ask for a normal production task, such as keeping word captions synchronized
after cuts and speed changes. For explicit recurring use, add the short
[project instruction](project-instructions.txt) to the project's existing agent
instructions with its owner's permission. Installation alone does not guarantee
that an agent selects the skill.

The companion uses an existing Veyrul MCP reader, or its bundled Python helper:

```bash
python3 ../../skills/veyrul-remotion-context/scripts/lookup.py \
  "retime subtitles after removing pauses at variable playback speed" \
  --output context.json
```

No Veyrul login or API key is needed for public reads. Send a generic question,
not a private transcript or client brief. Results retain evidence, rights,
resource links, revision and truncation information. A match still needs review.
The lookup makes one request; it never downloads or executes linked code.

## Run the example

Use Python 3.9+, a current supported Node.js, and an existing Chrome executable.
These files were tested on macOS arm64 with Python 3.9, Node 26, Chrome and
Remotion **4.0.537**. See [TESTED.json](TESTED.json) for the exact scope.

Obtain this public repository's source with your normal Git/GitHub workflow,
then run from `examples/remotion-retimed-captions`:

```bash
npm install --no-audit --no-fund
python3 -B prepare.py EDIT-01.json \
  --toolkit ../edit-aware-word-timing/media_timeline.py --output prepared-01.json
REMOTION_BROWSER_EXECUTABLE="/path/to/your/chrome" \
  node render.mjs prepared-01.json render-01
```

On macOS, the usual Chrome path is
`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`.
The script requires an existing executable instead of downloading a browser.
It chooses an available local port and refuses an existing output directory.
The output includes a 720×1280 H.264 `edited.mp4` and the exact timing data.
The complete bundle is retained in that output directory; allow roughly 35 MiB
per render in addition to installed dependencies. It does not delete outputs.

The toolkit file is the saved, unchanged
[original timing module](../edit-aware-word-timing/media_timeline.py), under its
own MIT license. Preparation verifies SHA-256
`1d9508741b4a64e002e883dfa309b53c400fbf155e938aa0db085e6e64f96f14`
before importing it. Inspect the source before running it; a hash proves identity,
not safety or correctness. The example's original code is covered by the
repository's MIT-0 license. Remotion and other dependencies retain their own
[license and pricing terms](https://www.remotion.dev/docs/license).

## Return for the changed edit

Keep the toolkit and useful record reference, then change the order, speed and
repeated section using `EDIT-02.json`:

```bash
python3 -B prepare.py EDIT-02.json \
  --toolkit ../edit-aware-word-timing/media_timeline.py --output prepared-02.json
REMOTION_BROWSER_EXECUTABLE="/path/to/your/chrome" \
  node render.mjs prepared-02.json render-02
```

The same selected resource applies; another search is useful only when the task
or evidence needs rechecking. In our return lookup it was found again at rank 1.
Neither rendering nor preparation contacts Veyrul. A failed/empty lookup does
not prevent using an already reviewed local resource or normal documentation.

## What the adapter adds

The saved toolkit normalizes words and preserves source/cut identities across
cuts, repeated sections and rational speed changes. Its output rounds to
microseconds. A direct conversion of that rounded output to video frames can
be one frame late: `11/3` seconds becomes `3,666,667` microseconds, just after
frame 110 at 30 fps. Our first adapter exposed that problem.

This adapter derives frame boundaries from the retained source/cut identities
and exact speed ratios **before rounding to frames**. It keeps the original
timing code unchanged. It also records word occurrences with no visible frame
in `unrepresentedIndices`; tiny or fully overlapped words are not silently lost.

`captions` exposes the toolkit's rounded timing in Remotion's caption data shape.
The demonstrated renderer uses `frameIntervals` and `activeByFrame`, which carry
the exact frame policy. Do not reconstruct those intervals from `captions` and
assume the rounding issue has disappeared.

The renderer uses Remotion's documented `disableSharedMemoryCapture: true`.
Our initial default-capture run contained one visibly corrupted frame. The
standard-capture verification results are reported in `TESTED.json`; this is
not a claim that every capture issue or browser combination is resolved.

## Boundaries and checks

- Inputs: up to 80 words, 12 cuts, 30 seconds of source time and 60 seconds of
  output. Integer fps 1–60; actual videos were checked at 30 fps. A numerical
  24 fps case is separate from video verification.
- Source and output cut boundaries must align to the selected frame grid.
  Unaligned edits, invalid numbers and altered toolkit code are rejected.
- The fixture is silent and synthetic. It does not prove speech alignment,
  transcription quality, arbitrary footage handling, audio retiming or
  broadcast subtitle compliance. Replace the diagnostic source component with
  your own permitted local media only after checking its timing and metadata.
- The prepared demo source is six seconds long. Longer sources require adapting
  that source composition and validating the actual footage.
- Visual checks cover the supplied English words and layout. Different scripts,
  long words and layout changes need their own readability/overflow checks.
- These are founder-operated integration checks, not independent adoption or
  proof that agents spontaneously choose Veyrul.

Run the numerical and input-boundary tests with:

```bash
VEYRUL_TIMING_TOOLKIT=../edit-aware-word-timing/media_timeline.py \
  python3 -B -m unittest -v test_prepare
```

Keep the record ID, revision, code pin, conditions and observed results in the
project's existing notes. When sharing is permitted, contribute a reproducible
finding using the [contribution guide](../contributions.md). No private footage
or transcript is needed, and no contribution is required to read or reuse.

## Sources

- [Saved Veyrul timing resource](https://veyrul.com/articles/art_01M6FTHTXK218N2MSF2FERAST5)
- [Remotion caption guidance](https://www.remotion.dev/docs/captions/displaying)
- [Remotion video trimming and speed controls](https://www.remotion.dev/docs/offthreadvideo)
- [Remotion renderer options](https://www.remotion.dev/docs/renderer/render-media)

Use current official Remotion documentation for API behavior. Veyrul complements
that documentation with saved production resources and actual findings.
