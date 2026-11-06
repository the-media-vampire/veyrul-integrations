# Separate colour conversion from colour tags

This original FFmpeg control followed Veyrul's saved [tagging-versus-conversion guide, revision 2](https://veyrul.com/articles/art_01M5MCCBZX67KQN6Q58571CHA2). The guide is documentary; the following small execution is separate founder-controlled evidence.

Inspect `check_matrix.py`, then run with already-installed FFmpeg/ffprobe:

```sh
python3 check_matrix.py new-colour-test-directory
```

A new output directory is required. Inputs and all outputs are retained. There are no model calls or downloads. The fixture uses three original 32×32 RGB24 solid-colour frames at 24 fps: `(145,95,243)`, red and grey. Each is converted to raw limited-range YUV444 using either BT.709 or, deliberately incorrectly, BT.601. Both raw streams are then encoded with libx264 CRF 0, interpreted and tagged as BT.709. Decode RGB samples and compare them with the originals.

Observed on FFmpeg 8.1:

| Path | Decoded purple / red / grey | Maximum 8-bit RGB error |
|---|---|---:|
| Correct BT.709 conversion | (145,95,243) / (255,1,0) / (128,128,128) | 1 |
| BT.601 conversion interpreted as BT.709 | (147,109,249) / (255,24,0) / (128,128,128) | 24 |

Both report the same BT.709 matrix, primaries and transfer tags, limited range, and `yuv444p`. Tags alone therefore do not prove that the stored samples underwent the intended conversion.

An initial one-stage filter/encode attempt did not create the intended mismatch (errors 1 and 2); it was rejected as a test design and retained privately. This two-stage fixture makes the intentional mismatch explicit. Its <=2 acceptance threshold is only for this fixture.

This is **not** a reproduction or fix of [Kinetograph #111](https://github.com/0xS4N4TG/kinetograph/issues/111), nor proof that its bug has this cause. No Kinetograph engine, H.265, player display, HDR, real footage, target editor or perceptual quality was tested. Use matched source/decoded frame samples and inspect the actual pipeline before drawing those conclusions.

Primary reference: [FFmpeg scale filter](https://ffmpeg.org/ffmpeg-filters.html#scale-1), and the help from your installed `ffmpeg -h filter=scale`. Original code is MIT-0; see the plugin's [licence](../../plugins/kinetograph/LICENSE).
