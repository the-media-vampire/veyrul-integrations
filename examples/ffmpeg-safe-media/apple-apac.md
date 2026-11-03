# Apple APAC with FFmpeg: recognition, copy and decoding are different

Do not treat `ffmpeg -decoders` listing `apac` as Apple spatial-audio support.
On the tested FFmpeg 8.1 build, that decoder is **Marian's A-pac audio**, a
different format. An Apple `apac` sample entry requires its own compatibility
check. Keep the original iPhone MOV or other source before making derivatives.

## A real Apple-encoded test, with a deliberately limited scope

On macOS 26.3, Apple's `afconvert` encoded our original two-second stereo tones
as Apple APAC in a CAF container. We checked its actual `apac` format field.
Apple decoded it back to 96,000 stereo frames at 48 kHz. No sample-entry tag
was fabricated. [probe_apple_apac.py](probe_apple_apac.py) recreates the fixture,
runs the commands and retains every result; [EVALUATION.json](EVALUATION.json)
records the version and hashes.

| Operation on this CAF fixture | FFmpeg 8.1 observation |
|---|---|
| Inspect/demux | ffprobe identified an audio stream and read 96 packets, but reported unknown codec and no codec_name. |
| Decode APAC | Failed with no decoder found; exit 234. |
| Transcode APAC directly to AAC | Failed at decoding; exit 234. |
| Copy APAC to CAF | Header creation failed; exit 183. |
| Copy APAC to MOV | Exit 0, but only a 185-byte MOV with **zero streams and zero audio packets**. Apple could not decode it. This was not successful preservation. |
| Apple decode to PCM, then FFmpeg encode AAC | Produced a two-second stereo AAC file that decoded successfully. This was a derivative, not APAC or spatial-metadata preservation. |

The last row used these commands on the generated **stereo CAF**, each with a
new output path:

```bash
afconvert -f WAVE -d LEI16 apple-apac.caf native-decoded.wav
ffmpeg -nostdin -n -i native-decoded.wav -map 0:a:0 -c:a aac -b:a 128k fallback.m4a
```

The initial attempt to encode directly into an M4A container failed on this
machine; CAF encoding succeeded. Registered encoder names alone were therefore
not sufficient evidence for a particular container operation either.

## What this establishes for an iPhone MOV question

It establishes that checking a name or exit code is insufficient, and provides
an actual unsupported-decode case plus a tested native-decoding fallback.
It does **not** establish whether every iPhone APAC MOV can be remuxed, edited,
decoded or played spatially. We did not have an iPhone MOV fixture and did not
validate head tracking, alternate-track associations or spatial metadata.

Apple describes recordings that pair a stereo AAC track with an APAC spatial
track. If an inspected recording provides a suitable AAC alternative, the
[explicit stream-selection recipe](audio-stream-selection.md) can make an
ordinary derivative while retaining the original. Choosing AAC deliberately
omits APAC; a video-only export also omits audio. Neither is preservation of
the complete recording. If APAC preservation is required, compare expected
tracks, packet payloads and metadata and test playback with an Apple-capable
reader before accepting an export. Unknown results stay unknown.

## Version-pinned source evidence

- FFmpeg n8.1, commit `9047fa1b084f76b1b4d065af2d743df1b40dfb56`:
  [codec descriptor](https://github.com/FFmpeg/FFmpeg/blob/9047fa1b084f76b1b4d065af2d743df1b40dfb56/libavcodec/codec_desc.c#L3501-L3506)
  and [decoder](https://github.com/FFmpeg/FFmpeg/blob/9047fa1b084f76b1b4d065af2d743df1b40dfb56/libavcodec/apac.c)
  identify Marian's A-pac. The local binary tests above used Homebrew FFmpeg 8.1.
- Inspected development revision `200a98d5ba4a6c792517d3ea464a5392737b4e33`
  contains a separate
  [apple_apac descriptor](https://github.com/FFmpeg/FFmpeg/blob/200a98d5ba4a6c792517d3ea464a5392737b4e33/libavcodec/codec_desc.c#L3601-L3605)
  and [MOV tag](https://github.com/FFmpeg/FFmpeg/blob/200a98d5ba4a6c792517d3ea464a5392737b4e33/libavformat/isom_tags.c#L309),
  also in the MOV muxer's tag list. Its
  [codec registration file](https://github.com/FFmpeg/FFmpeg/blob/200a98d5ba4a6c792517d3ea464a5392737b4e33/libavcodec/allcodecs.c)
  lists the Marian decoder, not a separate Apple APAC decoder. This is source
  inspection, not an executed build or proof of working spatial preservation.
- Apple: [Enhance your app's audio recording capabilities](https://developer.apple.com/videos/play/wwdc2025/251/),
  the Spatial Audio capturing chapter beginning at 5:11, describes the two-track
  AAC/APAC structure and metadata requirements.

These are founder-operated engineering observations. Original inputs and failed
outputs were kept. No proprietary footage, paid model call or universal codec
compatibility claim is involved.
