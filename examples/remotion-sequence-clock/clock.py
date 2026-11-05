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
