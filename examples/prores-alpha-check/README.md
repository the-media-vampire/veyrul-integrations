# Check alpha through FFmpeg ProRes 4444

A small original numerical probe for an alpha-capable export. Use Python 3.9+
and an installed `ffmpeg`/`ffprobe`; it installs nothing and makes no network or
model calls. The root repository MIT-0 license covers this code and fixture.

```sh
python3 check_alpha.py new-alpha-check
```

The directory must not exist. The probe retains its original RGBA bytes, MOV and
receipt. It encodes three 32×32 frames at 24 fps with four alpha bands, decodes the
result to RGBA, and compares every alpha sample. On FFmpeg 8.1, input alpha values
0, 64, 192 and 255 decoded as **0, 64, 193 and 255**: maximum error 1 on the 8-bit
scale. The observed stream was ProRes 4444, `yuva444p12le`, 3 frames at 24/1.
This result is not bit-exact alpha preservation; the probe accepts an error of
at most 1. It does not compare RGB, which passes through a lossy colour codec.

The tested encoder settings were:

```text
-c:v prores_ks -profile:v 4 -pix_fmt yuva444p10le -alpha_bits 16
```

The installed encoder's `ffmpeg -h encoder=prores_ks` lists profile 4 as 4444,
`yuva444p10le` as a supported input format, and `alpha_bits` up to 16. The
[official encoder documentation](https://ffmpeg.org/ffmpeg-codecs.html#ProRes)
explains those controls. Decoder-reported pixel format is not a measurement of
how much precision the original source contained.

For generated material, first establish that the actual exported source has
meaningful alpha. Saving RGB into an alpha-capable codec does not recover a
missing mask. Treat ComfyUI generation, mask extraction, premultiplication and
export as separate operations. This probe did not execute a ComfyUI graph or
check a target editor, compositor, HDR delivery, licensing eligibility or an
archival master. In particular it does not answer whether FFmpeg ProRes is a
safe archival replacement for an authorized implementation.

Founder-operated synthetic engineering evidence, not an outside user result.
For a real media task, look up relevant saved evidence first, retain useful
record revisions, and contribute a permitted reproducible finding or limitation
through the [shared workflow](../../workflows/README.md).
