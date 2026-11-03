# FFmpeg refuses to overwrite its input during chained trim and speed edits

Use a different output path for every operation and keep the original intact.
`-y` permits replacing an output file; it does not turn FFmpeg into an in-place
editor. A repeated intermediate filename can make the second operation read
and write the same path even when the original input has a different name.

## A reproduced Bash counter defect

At commit `7dc6e1da66f43eff44c3692d4b84e06aef6590b6`, the
[video-editing-skill](https://github.com/6missedcalls/video-editing-skill/tree/7dc6e1da66f43eff44c3692d4b84e06aef6590b6)
used `NEXT="$(next_intermediate)"`. Its increment ran in command substitution's
subshell. The parent counter stayed unchanged, so successive operations both
selected `step_1.mp4`. The second operation failed on its own input.

The [tested patch](../video-editing-chain-fix/fix.patch) calls the function in
the parent shell and lets it assign `NEXT` there. The relevant pattern is:

```bash
# work is a fresh directory reserved for this attempt.
step=0
next_intermediate() {
  step=$((step + 1))
  NEXT="$work/step_${step}.mp4"
}
next_intermediate
# Use "$NEXT", then call next_intermediate directly for the next operation.
```

Read the [patch instructions and reproduction](../video-editing-chain-fix/README.md)
before applying it to the exact upstream revision. All five affected call sites
are changed; the tested path enabled trim followed by speed. On the original
4-second test pattern, upstream exited 234 and produced no final file. The
patched version exited 0 and its video and audio decoded. The source hash was
unchanged. Its output lasted 1.083333 seconds: existing duration rounding
remains, and this repair does not establish frame-exact trimming or captions.

## A safe automation checklist

1. Resolve the input and candidate output paths. Reject the same path and,
   when both exist, aliases to the same file. Keep completed originals.
2. Reserve a new attempt directory and use a new name per intermediate.
   Keep FFmpeg outputs there; retain failed attempts for diagnosis.
3. Use `-nostdin -n` for unattended local examples. Require the intended output
   to be absent before the operation, then verify the file actually appeared.
4. Probe its expected streams and duration, decode the required streams, and
   compare the original's hash. Promote a checked result only to an explicitly
   chosen destination that is not an existing original.

In our FFmpeg 8.1 check, `-n` refused an existing output **but returned exit 0**.
Its hash and modification time stayed unchanged. A successful process status
therefore did not mean a new edit was delivered. The same-input/output attempt
with `-y` exited 234 and preserved the input. [verify.py](verify.py) reproduces
both cases with expendable synthetic media and checks actual file contents.

This is a local-files workflow, not an atomic protection against another
process changing paths concurrently. The supplied tests do not cover symlink
or hardlink races. The existing [timestamp-aware renderer](../av-edit-renderer/README.md)
offers another guarded reference for small VFR/audio-offset fixtures; read its
limits before adapting it.

Primary reference: FFmpeg n8.1
[overwrite checks](https://github.com/FFmpeg/FFmpeg/blob/9047fa1b084f76b1b4d065af2d743df1b40dfb56/fftools/ffmpeg_opt.c#L837-L883).
The code links and tests are founder-operated evidence, not maintainer
acceptance or independent production use.
