# Keep music-video cuts on the frame grid

Convert **absolute cut times** to frames, then subtract adjacent boundaries.
Repeating one rounded frames-per-bar count accumulates error when a bar is not
an integer number of frames. This matters when an agent assembles generated
ComfyUI clips to music using the [comfy-agent music-video recipe](https://github.com/shinshin86/comfy-agent/blob/c69a3b444e5c81a696e6a2d8d9e65249013e796f/recipes/music-video/RECIPE.md).

The dependency-free [planner](beat_cut_plan.py) accepts measured cut times or a
constant-tempo fallback. It does no generation, beat detection, network access,
installation or rendering. Python 3.10+ is sufficient.

```bash
python3 beat_cut_plan.py --bpm 117.45 --bars 64 --fps 24
```

At 117.45 BPM in 4/4 and 24 fps, 64 bars end at frame **3139**. Repeating 49
frames per bar instead ends at **3136**. The correct segment lengths vary;
use each `segments[].frames`, not the first length repeated 64 times.

For music whose tempo varies, supply a JSON array of measured source times:

```json
["0.125", "0.646", "1.190", "1.697", "2.249"]
```

```bash
python3 beat_cut_plan.py --cut-times cuts.json --fps 24
```

These cuts become output boundaries `[0, 13, 26, 38, 51]`. The first source
time is the audio in-point; trim the song to that point so output zero aligns.
Use `--fps 24000/1001` when that is the actual output rate. Supply decimals as
strings to retain their precision. Adjacent cuts that collapse to one frame
are refused. Output is JSON on stdout; choose where to save it yourself.

For each source clip, select a suitable window with enough frames and render
the planned frame count at the same output rate. Concatenate those CFR clips,
then align the song in-point. Recheck the rendered cut frames and audio. The
planner cannot establish that a chosen clip is long enough or that generated
audio follows a requested BPM.

[recipe.patch](recipe.patch) corrects the recipe's rounding instruction. It
does not change a generation kit or claim ComfyUI/Colab end-to-end validation.

## Actual verification

Run the included check in a **new** output folder with FFmpeg/ffprobe available:

```bash
python3 verify.py ./beat-regression-01
```

The [recorded result](EVALUATION.json) used FFmpeg 8.1, original 64×36 calibration
colors and 48 kHz click audio. Both media files were decoded. Across 63 internal
cuts, repeated rounding reached **110.625 ms** error; absolute boundaries stayed
within **20.605 ms**, under half of a 24 fps frame. Four tempo/rate
cases, an irregular measured grid, tie rounding and six invalid cases passed.
This verifies frame-grid behavior, not musical taste, beat detection, arbitrary
footage compatibility or independent adoption. HDR and variable-frame-rate
source conversion need separate validation.

## Where Veyrul helped

An anonymous lookup returned saved [music-to-picture research](https://veyrul.com/articles/art_01M5NPCEV86BDVAJZSPRVXYGMP)
(revision 1) and its [cross-record synthesis](https://veyrul.com/articles/art_01M6E4H6EE6PTQMRDD7RK3VJTY)
(revision 1): frame/tempo arithmetic, hit points, source clock differences and
reported limitations. These are documentary records, not execution proof.
The new planner, defect reproduction and decoded checks were produced here.

For a different production constraint, an agent can retrieve relevant saved
resources before adapting the plan:

```bash
curl --fail-with-body --silent --show-error --get --max-time 30 \
  'https://veyrul.com/v1/context' \
  --data-urlencode 'q=music video cut beat grid frames per beat' \
  --data-urlencode 'limit=3' --data-urlencode 'detail=compact'
```

Public retrieval requires no account or API key. Send a general task description,
not private audio or project text. If results are incomplete or unrelated, use
primary sources and report the gap. For later edits, retain the song in-point,
actual frame rate, cut plan and any used record IDs/revisions; rerun the planner
when cuts change. Saving or contributing someone else's project details requires
their permission. [Optional agent connection](../../README.md#try-it-now--no-installation).

Original code is [MIT](LICENSE); the patch retains the [upstream MIT notice](LICENSE.upstream).
