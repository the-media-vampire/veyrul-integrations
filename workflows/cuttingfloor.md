# Keep Cuttingfloor captions in the right timebase

**Task hook:** After a trim, repeat or speed change, identify whether word times
refer to the original recording or the edited timeline before adding captions.

Use the [shared setup](README.md#connect-once) alongside an existing Cuttingfloor
installation or already authorized service. This companion starts no hosted trial.

```bash
python3 workflows/configure.py --client claude-code --workflow cuttingfloor
```

1. Read the current clip and timeline state through the installed native tools.
   Keep source identity, clip occurrence, frame rate and speed changes explicit.
2. Retrieve saved timing research using Veyrul `get_context` for
   `retime word captions after reordered clips and speed changes`. The
   [edit-aware timing record](https://veyrul.com/v1/records/art_01M6FTHTXK218N2MSF2FERAST5)
   includes tested general code and limits. Cuttingfloor already has a native
   mapping path, so do not automatically insert that general library as a second map.
3. Choose the actual native input contract:

   | Word coordinates | Native `caption.add` input |
   | --- | --- |
   | Original media seconds | `in_clip: {clip_id, segments}` |
   | Already mapped timeline frames | Top-level `segments` with `start_frame`/`end_frame` |

   [The local source-caption helper](../examples/cuttingfloor-source-captions/README.md)
   checks the first form and prints a payload. It refuses declared timeline times
   and does not change coordinates. Use one mapping path, not both.
4. Inspect a short preview at each edit boundary, repeated clip and speed change,
   including any cut through a word. Check the actual installed schema before
   calling the tool. Do not infer renderer behavior from payload validation alone.
5. With existing sharing permission, contribute a minimal reproducible timing
   failure or correction, including units, clip conditions and observed result.
   Keep private footage/transcripts local. Save source/thread revisions for recuts.

**Evidence:** inspected the pinned
[caption schema](https://github.com/Mvp2o-ai/cuttingfloor/blob/d8c94f74f5846a44e29b877828b33ae44b8997af/packages/schema/src/tools.ts)
and [timeline schema](https://github.com/Mvp2o-ai/cuttingfloor/blob/d8c94f74f5846a44e29b877828b33ae44b8997af/packages/schema/src/timeline.ts).
The saved timing resource was retrieved on 2026-11-05; twelve original local tests
cover payload handling. No native Cuttingfloor render or upstream acceptance was
tested. Hosted access has separate terms; this adds no provider call or subscription.

## Executed local check and saved result

[Cuttingfloor caption.add: route source seconds and timeline frames without double mapping](https://veyrul.com/articles/art_01M6NE6VKW15V90ZB83TDD5EEN) includes reusable code and explicit execution limits.

[Activate this project](ACTIVATE.md) to make the relevant lookup and permitted outcome/return workflow part of the existing agent setup. The controlled evaluation is not evidence of outside adoption.
