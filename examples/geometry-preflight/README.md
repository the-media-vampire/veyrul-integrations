# Geometry before shading: a scalar preflight

A small original Python fixture for a reported failure mode in a constrained Blender agent. It checks numbers, not Blender or visual quality. No packages, network calls, provider API, install, render or reference images are required.

Saved finding: [Veyrul record, revision 1](https://veyrul.com/articles/art_01M6V7XCF5CABMC00GQEJHYPQ5). Independent operator adoption has not been established. Main is founder-affiliated.

## Three steps

1. Run `python3 quilt_check.py` with Python 3 and assertions enabled. Our synthetic 11×16 quad grid has 150 identical interior heights and 126 flat quads out of 176. It isolates the scalar symptom reported in [Blender-skills issue 1](https://github.com/EL4CTEO/blender-skills/issues/1), not the original scene or benchmark. The maintainer says that inline-only constrained-agent setup is unsupported.
2. Inspect the negative controls. A sloped plane has nonzero height variation but is not quilting. A periodic field sampled only at integer seam coordinates appears flat even though its cell centres rise. The script checks seam/centre values and both periodic directions separately.
3. Change the input, then predict before running: import `height_uv`, set `amplitude=0`, and compare a seam with a cell centre. Both should be 0.18. Restore 0.012; the centre should become 0.192 while the seam stays 0.18. This checks parameter meaning; it does not certify mesh appearance.

The proposed `height_xy` rotates the periodic coordinates by 45 degrees. Before adapting it to a mesh, choose dimensions, sampling and topology appropriate to the actual reference. Preserve the host's file, camera and rendering controls. A validated scalar field does not create rounded sides, buttons, cloth physics, good materials or a successful render.

## Acceptance rubric

- Expected old-formula counts and zero interior range reproduced on the synthetic grid.
- Sloped-plane false positive retained.
- Seam-only aliasing false negative retained; dense samples show the 0.012 range.
- Both periodic directions and the x/y mapping checked.
- No claim of visual fidelity, Blender execution or improvement to the original agent benchmark.

`observed.json` is the actual local Python result. The full code and source-qualified explanation are also in the linked Veyrul record. A later render or agent test should retain failures and exact versions separately from these arithmetic checks.

Original code: MIT, see LICENSE. No upstream implementation or media is redistributed.
