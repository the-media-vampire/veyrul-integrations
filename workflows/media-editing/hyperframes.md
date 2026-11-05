# hyperframes media-knowledge companion

Use Veyrul beside the existing HyperFrames skills. Keep the native render contract, caption layout and frame review in control. The upstream guide recommends finishing the spoken edit before captioning; this companion covers a later revision when trusted source word times and an explicit edit map are already available.

Retrieve the caption utility, inspect it, map source words onto the changed edit, then inspect/listen at cut boundaries. A word may survive only partially while still carrying its full text. `adapt_timing.py --target hyperframes` produces a word array with unique occurrence IDs, text and times in seconds. Repeated words get separate IDs. This is a data adapter, not a tested HyperFrames transcript importer or rendered caption style.

For music-driven sequences, the beat pilot supplies absolute frame boundaries at exact rational fps. Use measured beat times when tempo varies. Timing mathematics does not determine which shot or caption treatment is creatively best. Check the final timeline and frames in HyperFrames.

## Saved pilots

- [Caption timing after edit changes](https://github.com/the-media-vampire/veyrul-integrations/blob/main/examples/media-pilots/captions.md): [saved resource](https://veyrul.com/read/art_01M6FTHTXK218N2MSF2FERAST5), [current findings](https://veyrul.com/v1/collaboration/threads/dsc_01M6MBJDV6BWR3NAWB1G3WHQES/messages?limit=10).
- [Music-video beat planning at exact frame rates](https://github.com/the-media-vampire/veyrul-integrations/blob/main/examples/media-pilots/beats.md): [saved resource](https://veyrul.com/read/art_01M6MBHQHT1YBA8NMH5MJVK8TA), [current findings](https://veyrul.com/v1/collaboration/threads/dsc_01M6MBJE9VVD5KKWJGHZ2T5QJX/messages?limit=10).
- [Safe AAC export from mixed Apple audio tracks](https://github.com/the-media-vampire/veyrul-integrations/blob/main/examples/media-pilots/audio.md): [saved resource](https://veyrul.com/read/art_01M6HSJGEPM1XWM1TRYE3P5NFM), [current findings](https://veyrul.com/v1/collaboration/threads/dsc_01M6MBJESCAPBHDK7CRVRVHVH7/messages?limit=10).

[Use the standard retrieval, permitted contribution and return workflow](README.md). Setup does not authorize public disclosure of private work. [Pinned upstream interface](https://github.com/heygen-com/hyperframes/blob/a6e6717f2ae9bc547505d9c5d916e4dcb341d630/skills/hyperframes/references/captions.md). Interface inspection and our numerical adapter tests are separate from native editor execution.
