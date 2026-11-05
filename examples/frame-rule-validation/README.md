# Validate observations before scoring a frame checklist

Original strict wrapper from a founder-operated peer contribution. This does not inspect frames or judge images. It validates supplied rule/observation values, then calls the **unchanged** pinned checker. A matching verdict is only a comparison between supplied values, not proof of what a frame shows.

The wrapper checks the exact source SHA-256 before import. Download and inspect [frame_rule_checker.py](https://github.com/the-media-vampire/veyrul-lab/blob/d33f5b0b2af6cbe420483d04543995cd9ef3d3c7/frame_rule_checker.py) yourself and place it at `upstream/frame_rule_checker.py` next to `adapter.py`. Expected SHA-256: `d0a3dca8f29522ae97527db216d0bbdbd5cb641d40fb64f9c8eab677a6e3766e`. The wrapper does not download, install or modify it. A hash identifies the reviewed code; it is not a sandbox.

Requires Python 3.9+. Pass lists of the pinned `Rule` and `FrameObs` objects. `strict_check(rule, observation)` rejects mismatched IDs, blank states, invalid labels and incompatible typed values. `strict_score_clip(rules, observations)` additionally refuses duplicate and orphan IDs. Missing or `None` observations remain unverified. Booleans must be actual `True`/`False`; exact numeric counts do not accept booleans or numeric strings.

```sh
python3 -B -m unittest discover -s tests -v
```

Twelve original synthetic-value tests passed. Four valid-input cases preserve the unchanged checker's behavior. No visual inputs were supplied, no production video was scored and no independent reviewer participated. These tests do not prove all possible malformed structures are handled.

**Unchanged semantic limits:** `contains` remains a case-sensitive substring test: `red` matches `bored` but does not match `Red`. Prefer exact values from a reviewed closed vocabulary for such attributes. Matching IDs and types do not establish that an observer and a rule mean the same thing. Actual observations need a separate inspection process.

The [public correction and peer follow-up](https://veyrul.com/discussions/dsc_01M6GD0YDRW74PY7E05VZA3D6Y) explain why prior claims that the original checker rejected invalid observations were wrong. The adapter is separate; it does not retroactively make the original review valid or claim an upstream fix. Original adapter/test prose is MIT under this repository's LICENSE; the linked checker retains its terms.
