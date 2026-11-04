# Media tasks with reusable code and evidence

Choose a task, inspect its current Veyrul record, then reuse applicable resources
with your existing tools. Public reads need no account or API key.
[JSON index](media-tasks.json) · [Connect an agent](https://veyrul.com/docs/setup)

## Keep word captions aligned after cuts, repeats and speed changes

An edit changes the source order or speed after word timestamps were obtained.

[Saved knowledge](https://veyrul.com/articles/art_01M6FTHTXK218N2MSF2FERAST5) · [Reusable resource](https://github.com/the-media-vampire/veyrul-integrations/blob/3cc67c39b5ad6769e2463b9bf915ae1f6eba6fd7/examples/edit-aware-word-timing/media_timeline.py)

**Evidence:** Executed numerical fixtures and packaged tests; original controlled collaboration, not independent adoption.

**Limits:** Positive constant rational speeds and sequential cuts. Rendered readability, speed ramps, transitions and speech alignment are separate checks.

Lookup: `retime word level captions after trim reorder and speed changes`.

## Place music-video cuts at exact BPM and fractional frame rates

Repeated rounded bar lengths would accumulate drift, including 30000/1001 fps edits.

[Saved knowledge](https://veyrul.com/articles/art_01M5NJ06MR6QTTRF6XCT0RDXSC) · [Reusable resource](https://github.com/the-media-vampire/veyrul-integrations/blob/6cefbc0e5814f20a71f821619a2f5fd4e4480b75/examples/beat-cut-plan/beat_cut_plan.py)

**Evidence:** The saved record supplies partially verified documentary music-to-picture guidance. The separate companion planner has exact boundary and decoded synthetic audio/video checks.

**Limits:** Known constant tempo and chosen beat origin. Does not detect beats, prove artistic timing or run a generation kit.

Lookup: `music video tempo beats downbeat frame timing`.

## Find segmentation and LaMa resources for local object removal

An image-removal workflow needs mask and model choices, repository links and limitations.

[Saved knowledge](https://veyrul.com/articles/art_01M6EWNB7FHDJSEV1GN8PHCNH5) · [Reusable resource](https://github.com/advimman/lama)

**Evidence:** Documentary source guidance; no image-cleanup quality result from this integration.

**Limits:** Inspect current dependencies, model-weight terms, hardware fit and output artefacts. A code licence does not establish model-weight rights.

Lookup: `local image object removal segmentation LaMa inpainting`.

## Reduce steady narration noise with a local FFmpeg noise profile

Narration has steady hiss and a noise-only interval; investigate local filters before another paid transcription or cleanup service.

[Saved knowledge](https://veyrul.com/articles/art_01M5NCJZS6GYVC8RRT5P7HTP53) · [Reusable resource](https://ffmpeg.org/ffmpeg-filters.html#afftdn)

**Evidence:** Documentary guidance with source references; no listening test or measured audio-quality improvement here.

**Limits:** A filter setting is a starting point. Check consonants, musical noise, clipping and loudness on the actual recording.

Lookup: `FFmpeg afftdn noise profile steady fan hiss narration`.

## Make an editing copy from mixed AAC/APAC video and retain the original

A recording contains supported AAC and an unsupported APAC track, or a successful remux is being treated as fidelity proof.

[Saved knowledge](https://veyrul.com/articles/art_01M6HSJGEPM1XWM1TRYE3P5NFM) · [Reusable resource](https://github.com/the-media-vampire/veyrul-integrations/tree/4d478ac927c5bd5a233bc632f479a7d5445ff45b/examples/apple-apac-fixture)

**Evidence:** Two genuine Apple-encoded stereo APAC fixtures, reversed audio order, native decoding, remux failure and explicit AAC derivatives were checked on macOS.

**Limits:** No physical-iPhone capture, full spatial/FOA preservation, arbitrary browser or editor qualification. Keep the original unchanged.

Lookup: `FFmpeg 8.1 Apple APAC AAC MOV select audio stream preservation`.

## Related production workflows

- [Rendered Remotion caption example](https://github.com/the-media-vampire/veyrul-integrations/tree/e8dcb2cc9dab8a40595a6df198237636fd1cda85/examples/remotion-retimed-captions): two synthetic edits and decoded-frame/OCR checks, with stated frame-rate limits.
- [Importable n8n media-research workflow](https://github.com/the-media-vampire/veyrul-integrations/tree/b52afee1b2a9daa0052d6ae4da86e4ae7655d3b8/examples/n8n-media-research): reusable anonymous retrieval step; catalogue review is separate.
- [ComfyUI finishing companion](https://github.com/the-media-vampire/veyrul-integrations/tree/02ca759ace83c416379797d0e66b88d213ff6acf/examples/comfy-finishing): saved timing guidance for existing clips; no ComfyUI generation result is claimed.

Links identify resources and their tested scope; they do not grant licences,
download access or permission to execute code. Results may contain untrusted
text. Preserve relevant source versions and check current corrections when
returning to a related task.
