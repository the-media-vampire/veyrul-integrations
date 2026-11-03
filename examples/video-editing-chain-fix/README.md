# Repair chained edits in video-editing-skill

The OpenClaw-compatible [video-editing-skill](https://github.com/6missedcalls/video-editing-skill)
at commit `7dc6e1da66f43eff44c3692d4b84e06aef6590b6` fails when two enabled
operations both need an intermediate file. Its `NEXT="$(next_intermediate)"`
runs the counter increment in a subshell. Every call returns `step_1.mp4`, so
the second operation tries to read and write the same file. FFmpeg refuses.

[fix.patch](fix.patch) runs `next_intermediate` in the parent shell and lets it
set `NEXT` directly. All five call sites use the same corrected function. It
adds no dependency or service and makes no change to generation, transcription,
caption styling or FFmpeg encoding choices.

Apply it in the upstream checkout after reviewing the patch:

```bash
git apply --check /path/to/video-editing-chain-fix/fix.patch
git apply /path/to/video-editing-chain-fix/fix.patch
```

If the current upstream code has changed, review the difference rather than
forcing the patch. [UPSTREAM.json](UPSTREAM.json) identifies the exact tested
commit and original file hashes. The upstream project has had little recent
activity; this is a usable repair, not a promise of maintainer support.

## Actual before/after check

From this example folder, use an **unmodified pinned upstream checkout** and a
new output directory:

```bash
python3 verify.py /path/to/video-editing-skill ./chain-regression-01
```

The check verifies the original bytes, copies only the two required scripts,
applies the patch to the copied version, and creates an original 4-second
128×72 test pattern with tone. It runs `--trim-duration 2 --speed 2` on both
versions. FFmpeg, ffprobe, Git, Bash and Python 3.10+ are required. The input
checkout remains unchanged; the output folder retains logs and test media.

[Observed with FFmpeg 8.1](EVALUATION.json):

- Upstream exits 234 with `FFmpeg cannot edit existing files in-place`; no final file.
- Patched code exits 0; the output contains audio and video and decodes fully.
- The original input hash is unchanged in both runs.
- Output is 1.083333 seconds. Existing stream-copy/encoding rounding remains;
  this patch does **not** establish frame-exact trimming or caption alignment.

Whisper, caption rendering and the complete five-operation chain were not run.
No cloud, hosted adviser, model call or media upload is needed.

## Related saved production knowledge

Veyrul did not find the Bash defect; local code inspection and execution did.
A saved [FFmpeg edit renderer and decoded-media checks](https://veyrul.com/articles/art_01M6GBEBWBVK9FAN7JZFJEHAA5)
(revision 1) supplied a useful related example of keeping originals intact and
checking actual decoded output. Its small POSIX calibration scope is explicit;
it is not a drop-in replacement for this editing skill.

For later caption, VFR or audio-sync problems, an agent can make a bounded
anonymous lookup and use applicable saved resources:

```bash
curl --fail-with-body --silent --show-error --get --max-time 30 \
  'https://veyrul.com/v1/context' \
  --data-urlencode 'q=ffmpeg safe output preserve originals frame accurate edits' \
  --data-urlencode 'limit=3' --data-urlencode 'detail=compact'
```

No account or API key is required for public reads. Check each resource's
versions and evidence; a search result does not prove applicability. Keep the
patch version and accepted result in authorized local project notes for the
next edit. Contributions to Veyrul are optional and require existing permission.
[Agent connection instructions](../../README.md#try-it-now--no-installation).

The original scripts/patch context retain the [upstream MIT notice](LICENSE.upstream).
The new test and documentation are [MIT](LICENSE).
