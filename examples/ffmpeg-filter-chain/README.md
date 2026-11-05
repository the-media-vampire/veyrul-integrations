# Compose one FFmpeg video filter chain

When separate wrapper stages each append `-vf` for the same output stream, the options do not compose: the last matching option wins. Build one ordered chain instead. FFmpeg's `-vf` is an alias for `-filter:v`; comma-separated filters form a connected chain. Multiple inputs, branching and several outputs need a deliberate complex graph.

For a measured 1920×1080 source, the intended order is:

```text
crop=1080:1080:(iw-ow)/2:(ih-oh)/2,scale=720:720,subtitles=filename=captions.ass
```

Cropping happens before resizing; captions are laid out against the resized output. Inspect the ASS script's resolution, fonts and styling before rendering.

The [standard-library command builder](compose_filters.py) emits a JSON argument list and **does not execute FFmpeg**:

```sh
python3 compose_filters.py input.mov output-new.mp4 --source-width 1920 --source-height 1080 --crop-width 1080 --crop-height 1080 --width 720 --height 720
python3 -B test_compose.py
```

The example selects the first video and optional first audio stream, encodes H.264/AAC, and intentionally omits source metadata and chapters. Choose and verify a different mapping or metadata policy when the task requires it. Do not use this default for spatial audio, all-track preservation, HDR mastering, interlaced content or non-square-pixel inputs. No codec, subtitle renderer or font availability is promised.

Pass the resulting list to a subprocess without a shell only after inspection and authorization. Shell avoidance does not eliminate FFmpeg filtergraph escaping. This small example therefore accepts only a simple `.ass` basename; stage an authorized copy under that name in the command's working directory. Arbitrary subtitle paths and filter expressions are refused. Input and output paths are resolved separately; `-n` refuses existing outputs. Read the actual source dimensions first.

## Evidence and limits

Three deterministic test groups exercise exact order, changed dimensions, path-as-one-argument behavior, overwrite refusal, impossible crops and filter-syntax rejection. The builder was run; no production video or visual comparison was rendered. The first check exposed a test expectation about macOS `/var` path normalization; its corrected expectation uses the resolved path. Input preservation and error cases pass.

Primary source inspection is pinned to FFmpeg 8.1:

- [Option matching and `-vf` alias](https://github.com/FFmpeg/FFmpeg/blob/9047fa1b084f76b1b4d065af2d743df1b40dfb56/fftools/ffmpeg_opt.c)
- [Simple filtergraph and stream selection documentation](https://github.com/FFmpeg/FFmpeg/blob/9047fa1b084f76b1b4d065af2d743df1b40dfb56/doc/ffmpeg.texi)
- [Filterchain syntax, escaping, crop, scale and subtitles](https://github.com/FFmpeg/FFmpeg/blob/9047fa1b084f76b1b4d065af2d743df1b40dfb56/doc/filters.texi)

Use the [media pilots](../media-pilots/README.md) for caption timing, beat grids and audio handoff. Inspect saved sources, report only permitted observed results, and reread corrections on the next related task. This is founder-operated engineering evidence, not independent user adoption.
