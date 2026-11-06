# FILM frame-count regression check

A standalone, standard-library Python check of the output-count discrepancy in
Google Research FILM at commit `69f8708f08e62c2edf46a27616a4bfcf083e2076`.
It requires no model, GPU, NumPy, TensorFlow, image download, or Veyrul account.

Download the exact source and pass it to the check:

```sh
curl -fL https://raw.githubusercontent.com/google-research/frame-interpolation/69f8708f08e62c2edf46a27616a4bfcf083e2076/eval/util.py -o film-util.py
python3 check_count.py film-util.py
```

The check makes no network requests and writes no files. It refuses source bytes
unless their SHA-256 is
`aba55119d8c4af3f86b7482df5d5161dd46fff05791a902faec1a3edc7c63592`.
It extracts only the three reviewed generator functions, retaining their original
statements, and executes them with scalar midpoint, file-reader and progress
stand-ins. The source is [Apache-2.0 licensed](https://github.com/google-research/frame-interpolation/blob/69f8708f08e62c2edf46a27616a4bfcf083e2076/LICENSE).
This repository's original harness is MIT licensed; it does not embed that source.

Both memory and file generator paths are checked for 24 combinations:
`F={1,2,3,5,25,273}` and recursion depth `N={0,1,2,3}`. Each checks count,
first/last endpoints, strict ordering and agreement between the two paths.

| Inputs F | Depth N | Generator count | README formula |
|---:|---:|---:|---:|
| 3 | 0 | 3 | 4 |
| 3 | 1 | 5 | 6 |
| 273 | 0 | 273 | 544 |
| 273 | 1 | 545 | 816 |
| 273 | 2 | 1089 | 1360 |
| 273 | 3 | 2177 | 2448 |

The inspected generator gives `(F - 1) * 2**N + 1` for nonempty input.
The pinned README gives `(2**N + 1) * (F - 1)`. Shared endpoints are emitted
once. Increasing N does perform further recursive interpolation in this check;
the evidence does not show broken recursion or establish the README author's intent.

This checks generator control flow only. It does **not** test actual image
loading, interpolation quality, media timestamps, audio synchronization or any
RIFE wrapper. Empty inputs and malformed arguments are outside this probe.

Founder-affiliated Veyrul work, published in response to an outside request for
reproducible N=0/N=1 cases. Our earlier 24-case run was internal verification,
not an independent user result.

The [saved correction](https://veyrul.com/v1/records/rpl_01M6QFK49PPXQBRTHX50597MMS)
accompanies the affected Veyrul guides. If this applies to an existing media task,
report the exact source version and an observed outcome or counterexample;
there is no need to generate media just to test this harness.
