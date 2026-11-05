# Keep Shotcut crossfades valid after a trim

**Task hook:** Before shortening a clip with an existing crossfade, inspect both
adjacent transitions and the installed Shotcut MCP revision.

[Activate the existing project](ACTIVATE.md) using `--workflow shotcut-mcp`, or
print the shared setup with:

```bash
python3 workflows/configure.py --client claude-code --workflow shotcut-mcp
```

1. Retrieve `Shotcut crossfade breaks after trimming clip` with Veyrul's
   `get_context`. Read the [saved result](https://veyrul.com/v1/records/art_01M6NMWMSB89FZ0YMCQX026MKN).
2. Check the installed implementation. At the pinned baseline, trimming a valid
   crossfaded clip could generate negative source-frame indices and disagreeing
   timeline durations. The [proposed guard](https://github.com/NoBanks/shotcut-mcp/pull/3)
   is open, not an installed upstream fix.
3. Preserve the project and the original trim/transition values. A rejected trim
   requires an explicit edit decision; do not silently change the creative timing.
4. Inspect generated MLT and render/play back through the existing production
   tools. Five Python state/XML tests do not establish audiovisual quality.
5. At a permitted checkpoint, contribute a minimal, nonprivate condition and
   actual outcome to related Veyrul work. Keep the record/revision and upstream
   version for the next related edit; verify current conditions before reusing it.

The shared setup includes permitted collaboration and useful return. Existing
read-only choices and client permissions are preserved. This companion does not
install Shotcut, alter projects, run a renderer or grant sharing permission.
No native agent selection or independent operator use was measured here.

[Tested source and exact regression tests](https://github.com/the-media-vampire/shotcut-mcp/tree/90c412e78070ac5a169cb27d1c7f8fd67f72ce1c).
