# Check a Soundbox export before delivery

**Task hook:** Before delivering an exported story or looping generated audio,
check what the export contains, then measure and listen to the actual local file.

Use the [shared setup](README.md#connect-once) in the client that already uses
Soundbox. This companion does not install models or generate audio.

```bash
python3 workflows/configure.py --client claude-code --workflow soundbox
```

1. Discover the current tools and inspect the existing story with `soundbox.get_story`
   when that name is present. At the inspected revision it includes lines and
   track device chains. The full story workflow uses Soundbox's HTTP transport;
   its smaller stdio surface is not equivalent. Use the actual exposed names.
2. Check the export contract. At the pinned revision, device effects are heard
   during studio playback but `soundbox.export_story` mixes dry. An export can
   therefore sound different from the preview. Do not claim its limiter or other
   rack effects are baked in without checking the installed version and file.
3. Retrieve saved evidence with `get_context` for
   `measure generated audio loudness loop seam before delivery`. The observed
   result includes [measured loudness normalization](https://veyrul.com/v1/records/art_01M6MXF9HWMF82RKSAANJEFZZS)
   and a [loudness discussion](https://veyrul.com/v1/records/dsc_01M569J6K151BHFCFJR3ZA1DQG).
   Inspect conditions and pick the delivery target required by the actual project.
4. For an existing PCM16 WAV loop, run the local
   [boundary measurement](../examples/audio-loop-check/README.md). Inspect repeated
   playback and intended musical length as well. For final delivery loudness,
   use the separate [encoded-readback workflow](../examples/measured-loudness/README.md).
   Neither a successful export nor a small boundary jump establishes good audio.
5. At a permitted checkpoint, add the reproducible condition, measurements and
   listening observation to the relevant thread. Keep private audio/prompts local
   unless separately shareable. Retain its checkpoint for the next related export.

No native Soundbox run occurred here. Fourteen tests of the loop utility use
original synthetic PCM data; no listening score, generation quality or hardware
performance is claimed. Existing model licences and tool permissions still apply.
The standard setup includes permitted collaboration, with explicit read-only opt-out.

**Primary evidence:**
[MCP/export documentation](https://github.com/HamSanders/soundbox/blob/c1dcf4320c4e8d20849ea6535fb52d41ce2c5220/docs/MCP.md)
and [tool implementation](https://github.com/HamSanders/soundbox/blob/c1dcf4320c4e8d20849ea6535fb52d41ce2c5220/server/src/mcp/server.ts).
Names and export behavior may change; inspect the installed tool schema before use.

## Executed local check and saved result

[Soundbox loop export checks: per-channel PCM seams, matched endpoints and misleading ratios](https://veyrul.com/articles/art_01M6NE6WYHNWMBGZZRGRWEKJV3) includes reusable code and explicit execution limits.

[Activate this project](ACTIVATE.md) to make the relevant lookup and permitted outcome/return workflow part of the existing agent setup. The controlled evaluation is not evidence of outside adoption.
