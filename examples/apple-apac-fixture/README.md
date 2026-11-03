# A genuine Apple APAC fixture for mixed-track qualification

Create a small MOV containing H.264 video, stereo AAC and **genuinely encoded
Apple APAC** audio. This provides reproducible codec evidence for the open
[mixed-track qualification discussion](https://github.com/openclaw/openclaw/pull/189740).
It does not change that project's fallback policy or establish device support.

The APAC payload comes from Apple's installed `afconvert` encoder. The native
muxer passes its original compressed samples into an AVFoundation MOV writer;
it never relabels AAC bytes as APAC. A second native reader decodes the APAC
track and checks its PCM against the CAF reference. Both fixtures are generated
from tones and a test pattern, with no private recording or third-party footage.

## Run locally

Use this repository's `examples/apple-apac-fixture` and adjacent
`examples/ffmpeg-safe-media` folders together:

```bash
python3 examples/apple-apac-fixture/verify.py ./apac-fixture-01
```

Requires macOS with an Apple APAC encoder/decoder, existing Apple command-line
tools (`clang` and SDK), Python 3.9+, and FFmpeg/ffprobe with H.264/AAC support.
Observed on macOS 26.3 (25D125), Apple clang 21 and Homebrew FFmpeg 8.1. Other
macOS versions are not qualified. The helper uses synchronous AVFoundation
track reads that compile with deprecation warnings on this SDK.

No installation, network request, account, API key or model call occurs during
the test. It creates a **new** output directory, compiles two small native
helpers there and retains every fixture, partial output and diagnostic. An
existing output directory is refused. Each subprocess is limited to 60 seconds;
native loops also have finite deadlines. Use the tiny supplied inputs; this is
not a general transcoder for arbitrary user files.

## What was measured

Each fixture is a two-second, 128×72, 24fps SDR test pattern. Both audio tracks
are stereo tones at 48kHz. One file orders tracks as H.264/AAC/APAC; the second
orders them as H.264/APAC/AAC, so choosing the audio by its position alone is
not sufficient.

| Check | Observed result for both variants |
|---|---|
| Native writer output | Three actual tracks: H.264, AAC and APAC. |
| APAC encoded payloads | All 96 packet payloads match the original Apple-encoded CAF. |
| Native APAC decode from generated MOV | 96,000 stereo frames; exact PCM match to the native CAF decode. |
| FFmpeg `-map 0 -c copy` to another MOV | Exit 0, three tracks and the same 96 APAC packet payloads, **but native APAC decoding failed** (`!stt`, AVFoundation -11800). The probed APAC duration changed from 2.000 to 2.005 seconds. Root cause is not established here. |
| Explicit AAC-only derivative | 48 H.264 and 95 AAC packet payloads preserved, video/audio decode succeeds, source unchanged. AAC is selected from observed absolute stream index 1 or 2. |
| Existing destination | Native muxer refuses it and retains the original bytes. |

The copied packets alone did not establish a playable APAC output. This adds a
different test to the earlier [CAF-to-empty-MOV observation](../ffmpeg-safe-media/apple-apac.md).
Read [TESTED.json](TESTED.json) for commands, exact versions, hashes and outcomes.
Whole MOV hashes can vary between runs because the native writer adds container
metadata; the check compares payloads and decoded PCM, not an expected whole-file
hash from another run.

The exact `readIsobmffTrackIds` function from OpenClaw draft
`19bda08ee197aabf097c23c9070547605241c1fa` was also run against both files. It
reported all three track IDs. This checks only that pure inventory function;
we did not run the full OpenClaw worker, Mediabunny, consent UI or browser export
pipeline. The upstream implementation is linked in [SOURCES.json](SOURCES.json)
and is not vendored here.

## Limits that stay open

This is purpose-generated Apple-coded media, **not a physical iPhone recording**.
It has stereo APAC, not a four-channel FOA recording, and omits Audio Mix metadata,
alternate-track associations, rotation/HDR variants and head-tracked playback.
It does not settle spatial fidelity, acceptable track loss, browser/device
qualification or the maintainer's merge/release gates. The failed FFmpeg remux
is not a failure of OpenClaw's separate browser implementation.

An AAC-only output deliberately omits APAC. Preserve the source and disclose
that loss; do not present it as preservation of the complete recording. This
experiment does not authorize a fallback in another application.

## How saved knowledge helped

The initial lookup returned Veyrul's
[APAC guide and original CAF generator](https://veyrul.com/articles/art_01M6HSJGEPM1XWM1TRYE3P5NFM).
The downloaded generator's bytes were checked against public revision
`ab4ce0addb1601d361823d9c2ca972e6790f112a` and reused unchanged. A later MCP lookup
returned the [audio-selection guide](https://veyrul.com/articles/art_01M6HSJFVPNNN0PTAKK1XGKF7B),
whose inspect-before-mapping guidance was applied to the reversed-order case.
The native MOV mux/decode helpers and their new finding were developed here.

These are Main/founder-controlled engineering checks, not independently operated
agents or evidence of autonomous selection, adoption or cost savings. The code
works locally independently of Veyrul. If useful on a real task, keep permitted
version/outcome notes and use the [existing contribution instructions](../contributions.md)
to share a supported finding; sharing remains optional and separately authorized.

Original code and prose are [MIT](LICENSE). Apple tools, FFmpeg and upstream
projects retain their own licences. No model weights, SDK headers or captured
third-party media are included in the public package.
