# Global caption intervals inside a Remotion Sequence

A clip starts at composition frame 24 and lasts 48 frames. The words are already
mapped to global composition frames. Inside that Sequence, `useCurrentFrame()`
uses its local clock: global 24 is local 0. Do not run source-media retiming again.

`clock.py` converts one half-open global interval to a clipped local interval,
using the absolute Sequence start (including parent offsets). It does not alter
sound, change speed, render footage or infer missing units.

```python
from clock import local_interval, visible
interval = local_interval(67, 76, sequence_global_start=24, duration=48)
assert interval == (43, 48)
assert visible(interval, 47)
assert not visible(interval, 48)
```

Use the same `[start, end)` comparison in the component mounted inside the Sequence.
Pass the absolute offset explicitly for nested Sequences. This example assumes
unit playback rate and a nonnegative Sequence start; rate changes, negative starts,
pre/post-mounting and arbitrary production media are outside its tested scope.

The founder-controlled test used Remotion 4.0.537: a 96-frame 24 fps composition,
one Sequence `[24,72)`, and four words. Thirteen actual rendered boundary stills
matched expected caption presence. The fourth word `[67,76)` was absent at frame
72. This establishes the bounded clock behavior; it is not a layout, artistic
quality or audio-sync benchmark. The independent local helper tests cover changed
offsets and clipped intervals; that does not extend the renderer evidence.

Primary documentation: [Sequence](https://www.remotion.dev/docs/sequence) and
[useCurrentFrame](https://www.remotion.dev/docs/use-current-frame).

Run `python3 -m unittest discover -s . -p 'test_*.py'` in this directory.
