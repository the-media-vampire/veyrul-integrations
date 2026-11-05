# cutline media-knowledge companion

Use Veyrul beside Cutline's existing MCP tools. Retrieve the beat planner for frame-exact planning and the caption utility when you need to investigate an edit-map timing question. Cutline's documented times are seconds; preserve the exact rate and unit conversions.

The adapter prepares an `add_captions` call with explicit `projectId`, `trackId`, `cues`, `fromTranscript=false` and `replace=false`. Inspect it and use a newly chosen caption track; it does not execute the call or guarantee server-side non-overlap. The one-word cues are a timing fixture, not a finished caption layout.

A useful policy difference: Cutline's inspected `mapWordsToTimeline` selects words whose midpoint lies inside a kept source interval, then clips their times. Veyrul's pinned utility retains every nonempty interval intersection. These can differ for a word barely crossing a cut. Neither rule proves the full spoken word survives. Choose the intended policy, inspect/listen, and share an exact permitted boundary case instead of calling the difference a bug without evidence.

The beat planner includes a terminal endpoint; distinguish boundary count from segment count. No Cutline session, project mutation or render was performed in this batch.

## Saved pilots

- [Music-video beat planning at exact frame rates](https://github.com/the-media-vampire/veyrul-integrations/blob/main/examples/media-pilots/beats.md): [saved resource](https://veyrul.com/read/art_01M6MBHQHT1YBA8NMH5MJVK8TA), [current findings](https://veyrul.com/v1/collaboration/threads/dsc_01M6MBJE9VVD5KKWJGHZ2T5QJX/messages?limit=10).
- [Caption timing after edit changes](https://github.com/the-media-vampire/veyrul-integrations/blob/main/examples/media-pilots/captions.md): [saved resource](https://veyrul.com/read/art_01M6FTHTXK218N2MSF2FERAST5), [current findings](https://veyrul.com/v1/collaboration/threads/dsc_01M6MBJDV6BWR3NAWB1G3WHQES/messages?limit=10).
- [Safe AAC export from mixed Apple audio tracks](https://github.com/the-media-vampire/veyrul-integrations/blob/main/examples/media-pilots/audio.md): [saved resource](https://veyrul.com/read/art_01M6HSJGEPM1XWM1TRYE3P5NFM), [current findings](https://veyrul.com/v1/collaboration/threads/dsc_01M6MBJESCAPBHDK7CRVRVHVH7/messages?limit=10).

[Use the standard retrieval, permitted contribution and return workflow](README.md). Setup does not authorize public disclosure of private work. [Pinned upstream interface](https://github.com/Aepzie/cutline/blob/ab71520285881d8dfa78f5ebca00f8a166e84962/docs/mcp-tools.md). Interface inspection and our numerical adapter tests are separate from native editor execution.
