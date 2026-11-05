# Measure an audio loop boundary

This Python 3 standard-library helper reads an existing signed 16-bit PCM WAV
and reports the last-to-first sample step for each channel. It compares that
step with adjacent samples inside the file and reports DC offset, sample peak
and RMS. It never edits audio, uploads a file or calls a model.

```bash
python3 examples/audio-loop-check/loop_check.py existing-loop.wav
python3 -B -m unittest discover -s examples/audio-loop-check -p 'test_*.py' -v
```

Input is limited to 128 MiB and 1–32 channels. Unsupported formats, truncated
payloads and invalid lengths fail with exit 2. Successful measurement prints
JSON and exits 0; that exit is **not a production-quality pass**. The original
file remains unchanged. If conversion is needed, create a separately approved
copy with your existing audio tools and retain the original.

## Interpret the measurements

`boundary_jump_fs` is `abs(first - last) / 32768`. A normal sampled waveform
can have a nonzero last-to-first step, so zero is not the target by itself.
`boundary_to_max_adjacent_ratio` compares that boundary with the largest step
inside the channel; it is `null` when there are no internal changes. Values
are normalized to sample full scale; a difference can exceed 1.

Compare repeated playback, the intended bar or beat length, channel behavior
and the exported file. A small step can coexist with the wrong rhythm or an
audible tail cut. A large internal transient can make the ratio look small.
The helper supplies measurements, not an audibility threshold or automatic fix.

This does not measure integrated LUFS, true peak, codec delay or loudness after
encoding. Use the separate [measured loudness workflow](../measured-loudness/README.md)
for those delivery questions.

## Evidence

Fourteen tests use original synthetic PCM data: silence, DC offset, a repeating
wave, a ramp, opposite stereo channels, a discontinuity across streaming chunks,
signed extremes, invalid/truncated headers, bounds and unchanged inputs.
No generated music was judged, no Soundbox model was run, and listening quality
was not measured. See the [Soundbox companion](../../workflows/soundbox.md) for
the documented distinction between playback effects and exported audio.

At a permitted task checkpoint, a useful contribution records the source of the
audio, intended loop length, measurements, what repeated listening revealed,
and any reproducible correction. Share only what the operator already permits.
