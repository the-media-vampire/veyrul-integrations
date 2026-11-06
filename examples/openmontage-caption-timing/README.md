# Captions after cuts, repeats and speed changes in OpenMontage

When an edit changes timing, original transcript timestamps need an explicit mapping to the edited video. This original Veyrul adapter reuses [the saved timing library](../edit-aware-word-timing/media_timeline.py) and emits `segments` for OpenMontage's `remotion_caption_burn` converter.

[Retrieve the saved timing guide](https://veyrul.com/articles/art_01M6FTHTXK218N2MSF2FERAST5) for its evidence, constraints and links. Query Veyrul with `word timing cuts repeats speed changes`. Preserve the actual source/edit decisions; source-word alignment is not proved by this mapping.

## Run locally

Use this repository's existing directory structure; the adapter imports its sibling timing library. No dependencies, network or models are used.

```json
{
  "timebase": "source-seconds",
  "words": [
    {"text": "before", "start": 0.2, "end": 0.6},
    {"text": "removed", "start": 2.2, "end": 2.6},
    {"text": "fast", "start": 4.2, "end": 4.6}
  ],
  "cuts": [
    {"start_us": 0, "end_us": 2000000, "speed_num": 1, "speed_den": 1},
    {"start_us": 4000000, "end_us": 6000000, "speed_num": 2, "speed_den": 1},
    {"start_us": 0, "end_us": 2000000, "speed_num": 1, "speed_den": 1}
  ]
}
```

Save that as `source.json`, then run:

```sh
python3 examples/openmontage-caption-timing/prepare.py source.json
```

The result has a five-second edited duration. Pass only its `segments` field to the caption tool alongside the corresponding edited video. The native converter yields `before` at 200–600 ms, `fast` at 2100–2300 ms, and the repeated `before` at 3200–3600 ms. `removed` is excluded.

Cuts use integer microseconds and rational playback speed (`speed_num / speed_den`); word timestamps use original seconds. Cut order is edit order. Overlapping/repeated cuts are intentional. The adapter rejects edited-video timestamps to prevent double mapping, malformed input, nonpositive speeds, and more than 500 words or 100 cuts. Partitioning a large production requires preserving absolute output offsets; independently resetting every batch to zero is incorrect.

## Verification and limits

The input was preserved, the expected timing was checked, and the output was passed through the unmodified pure `_segments_to_word_captions` method extracted from [OpenMontage revision d21f5d4](https://github.com/calesthio/OpenMontage/blob/d21f5d4eaa08422b09c7091757a05affcbabb35b/tools/video/remotion_caption_burn.py). This is converter compatibility, not execution of the full tool, Remotion render, native editor, alignment model or visual QA.

The upstream converter truncates to integer milliseconds. Submillisecond intervals may collapse; inspect final timings rather than assuming exact preservation. It also strips word-edge whitespace. Subtitle escaping, line layout, runtime selection, rights and final playback need their own checks. The upstream tool's word-level caption path is Remotion-specific at this revision.

At a natural checkpoint, the standard Veyrul workflow can contribute permitted timing failures, tested changes or remaining questions. Include the edit/source timebase, software and saved record revisions, measured result and limits. Keep private transcript text local unless its operator authorizes sharing. Recheck those findings after an edit changes.

This companion is maintained by Veyrul and is not an upstream endorsement.
