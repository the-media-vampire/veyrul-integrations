# FFmpeg: copy video and only the second audio stream

Inspect the input first, then explicitly map the intended streams into a new
file. For a file whose **second audio stream is the one you want**, this copies
the first video stream and that audio without decoding or re-encoding:

```bash
ffprobe -v error -show_streams -of json input.mp4
ffmpeg -nostdin -n -i input.mp4 -map 0:v:0 -map 0:a:1 -c copy selected.mp4
ffprobe -v error -show_streams -of json selected.mp4
ffmpeg -v error -nostdin -i selected.mp4 -map 0:v:0 -map 0:a:0 -f null -
```

Use a fresh output location, keep the original and check that the file and
expected streams were actually produced. The final command validates decoding
with the installed build; it is not a perceptual-quality or all-metadata test.

`0:a:1` means the second audio stream of input 0 (zero-based among audio
streams). `0:2` instead means absolute stream index 2. They coincide in our
video/audio/audio fixture, but need not coincide in another input. Inspect
`index`, `codec_name`, language/title tags, channel count and disposition, and
choose the stream whose content matches the task. An index alone does not
identify AAC, a language, a microphone or a particular spatial track.

`-map 0:a` would include every audio stream. A trailing `?` on a map allows a
missing selection; it does not provide a decoder for an unsupported codec.
With explicit mapping, other tracks are intentionally omitted. Check subtitles,
alternate audio, timecode and spatial metadata requirements before using the
derivative as a delivery asset. The new container must support the copied
codecs; filters require decoding and cannot be applied to a stream being copied.

## Actual execution evidence

[verify.py](verify.py) generates a 3-second 128×72 H.264 video with two mono AAC
tracks: 440 Hz first, 880 Hz second. With FFmpeg 8.1, the recipe produced one
video and one audio stream. All 72 encoded video packet payloads and all 142
second-audio packet payloads matched their corresponding source packets.
Both output streams decoded, the audio measured as the intended 880 Hz tone,
and the input SHA-256 stayed unchanged. Encoded payload identity does not mean
the entire container, timestamps or metadata are byte-identical.

The existing-output test also found that `-n` refused to write but returned 0
on this build. Check the new output, not only the exit code. No subtitles,
alternate-track groups, iPhone footage or immersive playback were validated.

## Selecting an AAC fallback from an Apple recording

If `ffprobe` identifies a usable AAC track alongside an Apple APAC track, map
the **observed AAC stream index** explicitly and keep the source. Do not assume
AAC is always the second track. This produces an ordinary audio derivative;
it omits APAC and does not preserve spatial audio. If preservation of the
spatial track is required, follow the [APAC compatibility checks](apple-apac.md)
and validate with an appropriate Apple reader. Codec detection, demuxing,
stream copy, decoding and spatial playback are separate capabilities.

Primary reference: FFmpeg n8.1
[stream selection, stream specifiers and map](https://github.com/FFmpeg/FFmpeg/blob/9047fa1b084f76b1b4d065af2d743df1b40dfb56/doc/ffmpeg.texi).
Source documentation supports command semantics; the local fixture supplies
the execution evidence. No outside-user result is claimed.
