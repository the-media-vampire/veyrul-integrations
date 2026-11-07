# ASS subtitles: a positive word interval becomes zero duration

Founder-affiliated Veyrul research · reviewed 2026-11-07.

A positive interval can become invalid when rounded onto a coarser time grid. In our checked example, **101–104 ms becomes 100–100 ms** under nearest-centisecond rounding. The pinned converter rejects that result.

The exercised code was [`subtitle_workflow.py` at 5496e6c](https://github.com/the-media-vampire/veyrul-integrations/blob/5496e6c05ff2135f6c60a8f7cb22637d34d092d2/examples/current-word-subtitles/subtitle_workflow.py), SHA-256 `cbe1b769d083905cffd8271a295ab8d6fb134413fff7957044c483f1dc48c231`. The failing fixture rounded the input before calling the converter; this is not a claim that the converter silently rounded arbitrary inputs itself.

Before conversion, establish the final audio timebase and complete word timings. After applying a documented quantization policy, check positive duration, order, bounds and overlap again. Automatically stretching every short word is not a validated repair: it can introduce overlaps or exceed the clip boundary. Resolve the intended display policy explicitly.

Ten founder-controlled static checks also found that adding external `audio_trim_ms` or unsupported `sentences` metadata left the generated ASS unchanged. Structurally accepted JSON therefore does not establish alignment to edited audio.

**Evidence:** executed deterministic code checks, not transcription accuracy, rendered legibility or a universal ASS rule. [Full correction and context](https://veyrul.com/replies/rpl_01M6TVE4ZYHWK5D4FVKFS9ES21).

[Related saved context](https://veyrul.com/v1/context?q=ASS+timestamp+rounding+positive+word+duration+subtitles&detail=compact&limit=3) · [All five investigations](README.md)
