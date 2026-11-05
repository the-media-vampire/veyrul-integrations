# Preserve source-time captions for Cuttingfloor

After a recut, word timestamps may still refer to the original recording.
Cuttingfloor's pinned `caption.add` schema has an `in_clip` form that takes
original media seconds and maps them through the native clip. Its other
`segments` form takes timeline frames. Mapping the source words yourself and
then passing them to `in_clip` applies the timing change twice.

This helper validates **explicitly declared original source seconds** and prints
an `in_clip` payload. It performs no timing conversion, sends no tool call and
does not modify the source JSON or timeline.

```bash
python3 examples/cuttingfloor-source-captions/caption_input.py source-words.json
python3 -B -m unittest discover -s examples/cuttingfloor-source-captions -p 'test_*.py' -v
```

Example input, with placeholder IDs to replace with current native IDs:

```json
{
  "timebase": "source-seconds",
  "clip_id": "REPLACE_WITH_NATIVE_CLIP_ID",
  "track_id": "REPLACE_WITH_CAPTION_TRACK_ID",
  "segments": [{
    "start": 10, "end": 11, "text": "Stay here",
    "words": [
      {"start": 10, "end": 10.4, "text": "Stay"},
      {"start": 10.6, "end": 11, "text": "here"}
    ]
  }]
}
```

If the recording's 10–11 second interval plays at timeline 2–2.5 seconds,
the `in_clip` input still contains 10–11. Let Cuttingfloor place it. This is
a unit illustration, not a rendered acceptance result.

Inspect the printed `arguments` and the current discovered tool schema before
calling `caption.add` through the existing client. Tool prefixes may differ.
For repeated source clips, prepare each intended clip occurrence separately.
If your words are already in timeline coordinates, use the native timeline-frame
form instead; this helper intentionally refuses that input.

The helper accepts 1–5000 ordered, nonoverlapping segments and at most 500 words
per segment. It rejects nonfinite/negative times, booleans as times, out-of-range
or overlapping words, unknown fields, duplicate JSON keys and inputs over 2 MiB.
It implements a strict subset of the tool schema and does not support styling,
span metadata, SRT/VTT or additional offsets. Source silence between words is
preserved. It cannot verify that a supplied timebase label or clip ID is true.

## Inspect the result in the editor

Check a word at every cut, repeat and speed change, including partially cut
words. The native schema promises to omit moments that do not play; a valid
payload does not establish how a particular render handles every boundary.
Capture a short permitted preview with existing tools before committing a long
export. Do not apply a second general retiming library to `in_clip` input.

[Pinned primary schema](https://github.com/Mvp2o-ai/cuttingfloor/blob/d8c94f74f5846a44e29b877828b33ae44b8997af/packages/schema/src/tools.ts)
was inspected. Twelve local tests verify payload behavior and rejection cases.
The Cuttingfloor application, hosted service and renderer were not run for this
release. The [companion](../../workflows/cuttingfloor.md) links saved timing
research and the standard permitted contribution/return workflow.

## Inputs already mapped onto the timeline

`route_input.py` accepts the same bounded input object with an explicit
`timebase`: `source-seconds` selects `in_clip`, while `timeline-frames` selects
top-level `segments`. Timeline numbers must be integers. Values are preserved;
only native field names change. A supplied clip ID is not sent in the timeline
form, because timeline captions are not bound to that clip.

```bash
python3 route_input.py proposed-captions.json
```

It refuses unknown units, overlapping intervals, words outside their segment,
nonfinite values and fractional timeline frames. These are conservative local
checks; the inspected native schema does not enforce every one. It does not
inspect the installed timeline, edit clips, execute `caption.add`, render, or
prove caption placement. Confirm the input's declared coordinate system and
current installed tool schema before sending its printed payload.
