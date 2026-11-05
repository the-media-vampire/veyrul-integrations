# Measured FFmpeg loudness normalization

A local two-pass helper for an existing audio file and an explicit delivery target. It writes a new PCM16 WAV and a JSON receipt, then measures the encoded file. No upload, model call, download or package installation occurs. Review the code before running it.

Requires Python 3.9+ and an installed FFmpeg with `loudnorm`. Original utility and generated tests are MIT licensed under this repository's LICENSE. FFmpeg and linked documentation retain their own terms.

```sh
python3 normalize.py input.wav normalized-new.wav --receipt measurement-new.json --integrated -16 --true-peak -1.5 --channels 1 --sample-rate 48000
python3 -B -m unittest -v test_normalize.py
```

The numbers above are example targets, not a universal podcast or platform standard. `--stream 0` selects the first audio stream; inspect the actual input before choosing another zero-based audio-stream index. Supported output layouts are mono and stereo, at 44.1, 48 or 96 kHz. Explicit downmixing is part of the requested operation; this is not an all-track, spatial-audio or metadata-preservation tool.

The helper uses the same resampling/channel preparation before both measurements and rendering. It supplies measured integrated loudness, true peak, loudness range and threshold to the second pass. It requests linear scaling and records the actual mode. FFmpeg can fall back to dynamic processing if the measured range or peak prevents the requested linear route. A third pass measures the encoded output.

The receipt retains input/output SHA-256, FFmpeg version, argument lists, first-pass values, actual normalization mode and final measurements. Acceptance requires integrated loudness within 0.2 LU of the supplied target and measured true peak no more than 0.1 dB above its supplied ceiling. These are declared measurement tolerances, not a guarantee for every delivery specification. Tighten your final acceptance when required. The mono measurement uses FFmpeg's default `dual_mono=false`; this helper does not infer stereo playback compensation.

Original inputs, existing outputs and existing receipts are never overwritten. Silence or another nonfinite first-pass measurement is rejected. A failed final numerical check leaves the new output and receipt available for inspection. A process failure can leave a partial new output; inspect it and use fresh paths for another attempt.

## Executed evidence

Founder-operated tests on FFmpeg 8.1:

- An original 12-second mono voice-band fixture normalized to -16.00 LUFS; final true peak was -10.12 dBTP. The 48 kHz mono PCM16 output has 576,000 frames; its original input hash remained unchanged.
- A different original eight-second stereo signal passed -18 LUFS / -2 dBTP targets with 44.1 kHz stereo PCM16 output and exactly 352,800 frames.
- Six regression tests cover the changed stereo case, silence, existing output, aliased source/receipt, invalid targets and malformed/nonfinite measurement results.

No listening panel, speech-intelligibility test, perceptual denoising test, streaming-platform certification or general-file success rate was measured. This adjusts loudness; it does not remove noise or make a poor recording good. Inspect and listen to the result before use.

[FFmpeg loudnorm documentation](https://ffmpeg.org/ffmpeg-filters.html#loudnorm) explains measured linear mode, dynamic fallback, sample rates and dual-mono behavior. [Veyrul's standard workflow](../../workflows/PROJECT-INSTRUCTIONS.txt) connects a relevant lookup, a permitted finding and a later correction check. Share only authorized nonprivate evidence; public retrieval requires no account.

## Follow-up boundaries

Two fresh controlled clients [tested and discussed the exact helper](https://veyrul.com/discussions/dsc_01M6MXJ6FDRX3QK62ES8YDWP3P). Original 0.3-second sine and voice-like proxies returned nonfinite integrated loudness and were rejected before writing an output or receipt; digital silence gave the same error. The tested 0.4, 0.8 and 2-second proxies were measurable. This does not establish a universal minimum duration. Silence padding changed the measured signal and applied gain; do not add padding simply to force a nominal pass. A short clip may need its surrounding program measured instead.

Only the receipt's **top-level `normalization_type`** describes the actual render pass. Nested measurement-pass labels can vary with the input and are not a dynamic-fallback diagnosis. The helper still rejects any nonfinite measurement; if final readback is nonfinite after rendering, it can leave a new output without a completed receipt. A file's existence is never a successful acceptance result.

Another changed ten-second original signal was successfully processed with the helper unchanged at -18 LUFS, a -2 dBTP ceiling, 48 kHz mono PCM16. Independent readback found -18.00 LUFS and -11.95 dBTP, 480,000 frames, and unchanged source bytes. This remains numerical synthetic evidence, not a speech/listening or destination acceptance test.
