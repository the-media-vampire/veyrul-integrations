# Finish ComfyUI clips with saved media knowledge

An optional companion for an agent that already drives ComfyUI. Keep the existing
ComfyUI tools for generation and graph validation. Use this when the resulting
clips need caption timing, current-word subtitles or audio/frame-timing diagnosis.
It retrieves saved work and runs original code locally. No generation service,
hosted adviser, account or Veyrul API key is required.

This is a Veyrul-maintained companion, not an official ComfyUI or
[ComfyUI-Agent-Kit](https://github.com/SlavaSexton/ComfyUI-Agent-Kit) integration.
Installing it does not change those projects or their configuration.

## Add the optional skill

From the project where your agent does media work:

```sh
npx skills@1.5.22 add the-media-vampire/veyrul-integrations --skill veyrul-comfy-finish
```

Choose your agent when prompted. This uses the same installer as the main Veyrul
skill, requiring Node.js 22.20 or later. Review
[SKILL.md](../../skills/veyrul-comfy-finish/SKILL.md) first. It can use an existing
Veyrul MCP connection or its Python 3.9+ standard-library HTTP helper. No new
MCP configuration, background process or package is needed by that helper.
Installing a skill makes it available; the client still decides when to use it.

Try a task such as: "The clips are finished. I reordered two sections and repeated
the last one at 2x speed. Keep my existing word timestamps aligned without
transcribing again." Provide the actual edit list and existing word timings to
your own agent. A knowledge query can describe the problem without sending them.

## Three specific starting points

| Task | Saved work | Scope |
| --- | --- | --- |
| Retiming words through cuts, repeats and speed changes | [Timing library](../edit-aware-word-timing/README.md) and [Veyrul record](https://veyrul.com/articles/art_01M6FTHTXK218N2MSF2FERAST5) | Offline Python, standard library. Computes timing data from existing words and explicit cuts. |
| Highlighting only the spoken word | [ASS generator](../current-word-subtitles/README.md) and [Veyrul record](https://veyrul.com/articles/art_01M6F7TCQVEMH8F3CVTBBWF9V3) | Sorted, nonoverlapping 10 ms word timings. Serialization checked; actual rendering and font fit remain to check. |
| Understanding VFR frames and relative audio starts | [Reference and fixtures](../av-edit-renderer/README.md) and [Veyrul record](https://veyrul.com/articles/art_01M6GBEBWBVK9FAN7JZFJEHAA5) | POSIX 128x72 calibration example. Not a general exporter and not native Windows support. |

The public lookup returned each stated resource for the corresponding generic
query on 2026-11-03. That verifies access and relevance to these narrow tasks,
not finished-video quality. The source examples disclose their controlled-test
origin and exact limits. The two caption schemas are different: connecting them
requires an explicit checked conversion, particularly for overlaps and rounding.

## Reproduce a useful cut/repeat case

From a reviewed copy of this repository, run:

```sh
python3 -B examples/comfy-finishing/check_demo.py
```

The script uses the existing `examples/edit-aware-word-timing/media_timeline.py`,
reads [EDIT.json](EDIT.json), and prints the result. It writes no files, contacts
no service, and makes no model call. Source words are moved into this order:

1. Source 2.0-3.0 seconds at normal speed.
2. Source 0.0-1.0 seconds at normal speed.
3. Source 2.0-3.0 seconds again at 2x speed.

The expected timeline is 2.5 seconds. `Blue` moves to 0.20-0.50 seconds, then
appears again at 2.10-2.25 seconds. All six word intervals are checked against
manually derived expected values. This is an executable timing example, not a
ComfyUI render, transcription or subtitle-rendering demonstration.

The actual public helper can be run without MCP:

```sh
python3 skills/veyrul-comfy-finish/scripts/lookup.py \
  "keep word timestamps aligned after cuts repeats and speed changes"
```

It sends only that query, makes one bounded anonymous GET and returns compact
records plus resource links. `--output new-result.json` preserves the result in
a new file. Existing files are refused. On errors or insufficient evidence,
continue with your normal tools and primary documentation.

## Keep useful work connected

Save the relevant record ID/revision and exact code revision in permitted project
notes. Recheck them on a related later task. With existing sharing permission and
an authenticated agent connection, a minimal failure report or verified correction
can help the next agent; see [contribution setup](../contributions.md). Nothing
requires sharing customer footage or private transcripts.

No Veyrul subscription is required for these public reads. Your agent provider,
local rendering software and infrastructure retain their own costs and terms.
The companion's new files use this repository's MIT-0 license. The referenced
timing and subtitle implementations retain their accompanying MIT licenses.

## If a broad lookup returns generation recipes

Keep the source tool and the requested operation distinct. For **existing clips**,
try a focused query such as `FFmpeg edit renderer existing clips portrait subtitles
audio offsets`, preserving the real timing, aspect-ratio and export constraints.
In a founder-controlled check on 2026-11-06 this recovered the saved VFR/edit
reference after a broad ComfyUI query returned generation templates. It did not
supply a complete portrait/subtitle production recipe; continue researching only
the missing details. Use the shared rule's two-refinement limit, not an open-ended
query loop. For generation constraints, retain the exact model/node names.

For transparency delivery, the new [ProRes alpha probe](../prores-alpha-check/README.md)
provides a small executable export check. It does not create a missing alpha mask
or establish that a ComfyUI graph or destination editor will preserve it.
