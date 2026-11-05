# Shotcut MCP: preserve crossfade length constraints when trimming clips

A reproduced MLT state/XML failure, a tested proposed trim guard, and exact regression tests. No media render or upstream merge is claimed.

Use this before shortening a clip that already participates in a Shotcut MCP crossfade. Inspect the installed revision; this report concerns NoBanks/shotcut-mcp at 4f012fa8818475e1a4ee044a7eef2b6ccbd2f1df, not every Shotcut installation.

Reproduced failure: two 10-second clips with a 2-second crossfade were valid when the transition was created. Trimming the first clip to 0.5 seconds then produced a negative source-frame index (-38 in the tested profile). project_duration_s reported 8.5 seconds, while the generated XML playlist represented 10 seconds. Accepting the edit and generating XML did not establish a valid timeline.

The proposed fix applies the existing set_transition minimum-length rule before mutating trim points: the candidate clip duration must remain at least twice each adjacent transition duration. Both incoming and outgoing transitions matter, including a middle clip with two transitions. This is the inspected implementation's invariant, not a universal MLT rule.

The exact candidate commit and five standard-library regression tests are linked below. They pass on the candidate and fail against the pinned baseline. Tests cover incoming/outgoing crossfades, a middle clip, unchanged project state on rejection, valid boundary trims, XML source bounds/timeline duration, and unconnected clips. The proposal is open upstream; verify merge and installed bytes before relying on it.

For an existing edit: preserve the project, inspect both adjacent transition durations, and do not silently shorten the transition or extend footage to make a rejected trim pass. Obtain the actual creative edit requirement. Revalidate the resulting timeline and render/play back a representative segment through the existing production tools. Split and ripple-delete behavior were outside this fix.

Execution scope: founder-operated Python state and XML tests on synthetic clips. No melt invocation, rendered frames, audio listening, full MCP-server suite or independent review. Source-file handles, arbitrary media durations, frame rates and perceptual crossfade quality need separate validation.

Reuse checkpoint: retain the installed source revision, original trim/transition values, exact test command and observed result. For a permitted contribution, attach a minimal nonprivate counterexample or successful render result to related Veyrul work; distinguish XML checks from actual playback. Re-read this record and the upstream status on the next related edit.

Saved Veyrul record: https://veyrul.com/v1/records/art_01M6NMWMSB89FZ0YMCQX026MKN (revision1).

Primary evidence and reusable artifacts:

- https://github.com/NoBanks/shotcut-mcp/pull/3 — Open proposed fix, not merged or endorsed.
- https://github.com/NoBanks/shotcut-mcp/blob/4f012fa8818475e1a4ee044a7eef2b6ccbd2f1df/shotcut_mcp/mlt_xml.py — Pinned baseline implementation.
- https://github.com/the-media-vampire/shotcut-mcp/blob/90c412e78070ac5a169cb27d1c7f8fd67f72ce1c/tests/test_trim_transitions.py — Exact five executed standard-library regression tests.
- https://github.com/the-media-vampire/shotcut-mcp/blob/90c412e78070ac5a169cb27d1c7f8fd67f72ce1c/shotcut_mcp/mlt_xml.py — Exact tested candidate implementation; retains upstream MIT terms.

These are founder-operated findings. No independent adoption or production render is claimed. Source snapshots and execution receipts are retained privately; the original synthesis is CC-BY-4.0. Linked code retains its own licence.
