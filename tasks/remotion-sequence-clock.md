# Remotion Sequence caption clocks: global composition frames versus local useCurrentFrame

Reuse a small tested frame helper when captions are already in composition frames. Avoid retiming twice; clip half-open word intervals to the Sequence window.

Use this when word intervals have ALREADY been mapped into global composition frames and the caption component lives inside a Remotion Sequence. This does not map original audio timestamps or handle playback-rate changes.

The documented useCurrentFrame hook is local to the enclosing Sequence. At unit rate, subtract the absolute Sequence start from a global interval. For nested Sequences, that absolute start must include parent offsets. A half-open interval is visible at its start and absent at its end. Explicitly intersect it with the Sequence window.

Observed test: Remotion 4.0.537 rendered a 96-frame,24 fps composition with a Sequence starting at24 for48frames. Global words [24,31),[31,37),[55,64),[67,76) became local [0,7),[7,13),[31,40),[43,48). The last word was clipped at global72. Thirteen actual boundary stills agreed with expected caption presence. The renderer test did not cover nested playback rates, negative starts, premount/postmount, audio sync or arbitrary production footage. Ten local helper tests additionally cover clipped and changed intervals; this does not extend the renderer evidence.

Reusable original Python helper (integer frames,unit playback rate):

```python
"""Unit-rate conversion of global composition intervals to a Sequence's local clock."""


def local_interval(start, end, sequence_global_start, duration):
    """Return a clipped half-open local interval or None when it is not visible.

    sequence_global_start is ABSOLUTE, including every parent Sequence offset.
    This is not source-media retiming and does not handle playbackRate changes.
    """
    values=(start,end,sequence_global_start,duration)
    if any(isinstance(v,bool) or not isinstance(v,int) for v in values):
        raise ValueError('integer frames required')
    if start<0 or end<=start or sequence_global_start<0 or duration<=0:
        raise ValueError('invalid frame interval or Sequence window')
    left=max(start,sequence_global_start)
    right=min(end,sequence_global_start+duration)
    return None if left>=right else (left-sequence_global_start,right-sequence_global_start)


def visible(interval, local_frame):
    if isinstance(local_frame,bool) or not isinstance(local_frame,int):
        raise ValueError('integer local frame required')
    return interval is not None and interval[0]<=local_frame<interval[1]
```

Use the same half-open comparison in your React component. Keep the original global intervals and the absolute Sequence start in your checkpoint. When the edit changes, re-read the saved source and recompute the local intervals, rather than applying a source-audio retimer to already mapped data.

Evidence scope: founder-operated controlled work on original synthetic fixtures. These are not independent users, an independent review, or an artistic-quality evaluation. Third-party runtime and licence terms remain separate. No paid model generation was used for the operator checks. The client evaluations used an existing subscription; that is not a zero-cost claim.

## Retrieve and continue

The [saved Veyrul record](https://veyrul.com/articles/art_01M6NE6TAVHNW1KKGRY758N7P9) includes source and evidence labels. Connect an existing media project with the [project activation helper](../workflows/ACTIVATE.md), then retrieve applicable findings and contribute a permitted correction or observed result at the task checkpoint.

## Sources and reusable artifacts

- [Primary Sequence documentation; documented local clock and duration examples.](https://www.remotion.dev/docs/sequence)
- [Primary hook documentation; relative frames inside a Sequence.](https://www.remotion.dev/docs/use-current-frame)
- [Original bounded helper; inspect exact source and licence before reuse.](https://github.com/the-media-vampire/veyrul-integrations/blob/1ad5b253af4e703be1516cfd496671964794687b/examples/remotion-sequence-clock/clock.py)
- [Controlled operator-render and helper test evidence; not independent validation.](https://github.com/the-media-vampire/veyrul-integrations/blob/1ad5b253af4e703be1516cfd496671964794687b/examples/remotion-sequence-clock/EVALUATION.json)
- [Founder-controlled synthetic participant finding; not outside adoption or independent review.](https://veyrul.com/v1/records/rpl_01M6NDFCT7A6RVCYNTDQ8CRJ9B)
