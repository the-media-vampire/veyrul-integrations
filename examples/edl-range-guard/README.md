# Guard EDL ranges before caption timing

Original separate validation example from a founder-operated Veyrul collaboration. It is not an installed video-use integration or a merged upstream patch. The helper rejects reversed, empty, nonfinite, boolean and string time bounds before they can subtract from or poison cumulative caption offsets. It returns both a copied EDL and rejected ranges with reasons.

Use `clean, rejected = sanitize_edl(edl)` and inspect every rejection. **Both segment extraction and caption generation must use the same `clean` EDL.** Calling `build_master_srt_validated` only for captions can desynchronize an unmodified render pipeline. The example assumes the existing video-use dictionary/list shape; it is not a complete EDL schema validator or a speed-retiming library. It does not validate source duration, source IDs or media rights. Do not silently drop intended edits in production.

The observed target was [video-use render.py at 080dda497d7e8157b31c0090bed95651924f03eb](https://github.com/the-media-vampire/video-use/blob/080dda497d7e8157b31c0090bed95651924f03eb/helpers/render.py), SHA-256 `13290b75a8a56caaa3c57c19c8960c27d55d027e651bd9f8a9429ca9ada3fcec`. Its unchanged caption builder was exercised with original word fixtures. A reversed range moved all subsequent captions backward; NaN and infinity could cause exceptions. Valid EDL output stayed byte-identical through this guard. Rendering, transcription and FFmpeg extraction were not run.

Read the [finding and peer follow-up](https://veyrul.com/discussions/dsc_01M6MBJDV6BWR3NAWB1G3WHQES), including the separate limitation around sub-millisecond SRT rounding. The conversation is a controlled founder-operated study, not outside adoption or independent review. The upstream [word-boundary PR](https://github.com/browser-use/video-use/pull/235) does not itself contain this range guard.

Python 3.9+, standard library only. Original adapter and test below are MIT under this repository's LICENSE; linked upstream retains its own license. Run `python3 -B -m unittest -v test_edl_guard.py` here. Those deterministic tests cover the guard, not finished-media quality.
