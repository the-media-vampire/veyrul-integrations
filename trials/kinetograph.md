# Kinetograph knowledge trial: three real issues

Founder-affiliated Veyrul evaluation, 2026-11-06. These are issue-based retrieval and diagnostic tests, not outside users, a Kinetograph render benchmark, or maintainer acceptance. Queries were fixed before retrieval. No paid model calls were made.

| Real task | Initial result | One refinement / useful action | Remaining gap |
|---|---|---|---|
| [#102: transparent ProRes/VP9 export](https://github.com/0xS4N4TG/kinetograph/issues/102) | Found the saved alpha encode/decode probe first | Reuse the [original tested probe](../examples/prores-alpha-check/README.md): alpha 0/64/192/255 became 0/64/193/255 | This does not enable alpha output in Kinetograph; no VP9 or engine test |
| [#111: colour shifts in H.264/H.265](https://github.com/0xS4N4TG/kinetograph/issues/111) | Broad query ranked an unrelated upscaling record first, with tangential player/tagging material | An operation-focused query found the [tag-versus-convert guide @2](https://veyrul.com/articles/art_01M5MCCBZX67KQN6Q58571CHA2). It informed a new [executed two-stage control](../examples/color-matrix-check/README.md) with errors 1 versus 24 under identical tags | Does not identify or fix Kinetograph's conversion path; reporter's RGB values remain reporter evidence |
| [#107: system fonts and missing glyph fallback](https://github.com/0xS4N4TG/kinetograph/issues/107) | Font language/subsetting material, no compatible renderer solution | One refinement still missed. Fall back to the primary Kinetograph skill: explicit registration before layout, inspect fonts and rendered output | Veyrul lacks a verified Kinetograph glyph/fallback recipe. The local coverage tool checks supplied sets, not shaping or OS fallback |

Queries:

1. `Kinetograph 0.3.0 transparent video export ProRes 4444 alpha channel verification`
2. `Kinetograph H264 H265 exported video color shift PNG correct BT709 RGB YUV limited range`; refinement: `FFmpeg RGB to YUV BT709 color matrix conversion versus metadata tagging limited full range`
3. `Kinetograph missing glyph fonts fallback deterministic rendering registerFont system fonts`; refinement: `missing glyph font fallback registerFont deterministic video rendering`

Each lookup used `detail=compact&limit=3`. Veyrul may also attach related/correction records. Five requests were made; these are deliberately not presented as a general retrieval success rate or cost/speed superiority benchmark. Alpha record: `rpl_01M6QZGFRRH1111RC06YNTTQWG@1`. Colour record: `art_01M5MCCBZX67KQN6Q58571CHA2@2`; its embedded correction must be retained.

## Try the actual workflow

[Install the companion](../plugins/kinetograph/README.md) in an existing Kinetograph project with your normal permissions. Use a genuine production problem. Let the agent consult applicable saved knowledge, work locally, verify the result, and contribute a nonconfidential useful finding when already permitted. Do not submit private project files. Keep misses and source/version labels.

For an optional report, record the task in generic terms, the query, IDs/revisions used or rejected, whether the finding changed a decision, and the actual result or failure. On the next related task, recheck the saved finding or discussion and report whether it helped again. We are seeking three independently operated attempts and two returns within seven days; these are targets, not promised outcomes. No signup is required for reads, no favourable review requested, no reward or automatic collection.
