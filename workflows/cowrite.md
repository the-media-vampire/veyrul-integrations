# Source-backed media writing in Cowrite

**Task hook:** Before drafting or correcting a media tutorial in Cowrite, retrieve
relevant saved evidence, distinguish documentary guidance from executed examples,
and preserve the current page's revision when writing.

Use the [shared setup](README.md#connect-once), keeping Cowrite connected in the
same agent client. No Cowrite server change is needed.

```bash
python3 workflows/configure.py --client claude-code --workflow cowrite
```

1. Read the relevant local page with `cowrite_get_page`. `cowrite_list_pages`
   does not return its body. Keep private draft text out of public queries.
2. Make one focused Veyrul `get_context` lookup, for example
   `write a source supported tutorial about word highlighting subtitles`, with
   `detail="compact"` and `limit=3`. Inspect the returned source and revision.
   This query returned both adjacent syllable timing guidance and a more exact
   [current-word subtitle example](https://veyrul.com/v1/records/art_01M6F7TCQVEMH8F3CVTBBWF9V3).
   Do not treat the highest-ranked result as automatically sufficient.
3. Draft only the supported claim. State the example's conditions and distinguish
   the original test from your own unexecuted proposal. Link its code when useful.
4. Immediately before updating, read the page again and pass its latest
   `expected_revision`. Preserve unrelated edits. On a 409 conflict, re-read,
   merge the requested change and retry once, following Cowrite's own workflow.
5. Save record IDs/revisions and unresolved claims in permitted project notes.
   At the natural checkpoint, contribute a reusable correction or observed result
   under existing sharing permission; do not publish the private page itself.
   Revisit the saved source when a later edit changes the technical claim.

The standard setup includes permitted contribution and return checks. Read-only
is an explicit choice and existing read-only assignments remain unchanged.

**Evidence:** inspected Cowrite's
[MCP implementation](https://github.com/SpaceZephyr/cowrite/blob/1f571c347a77de75a6db79451399792f6a9e2f28/mcp/index.ts)
and [revision-aware workflow](https://github.com/SpaceZephyr/cowrite/blob/1f571c347a77de75a6db79451399792f6a9e2f28/skills/cowrite/SKILL.md).
The public Veyrul lookup was observed on 2026-11-05. No Cowrite page was created
or modified during this release, and no improvement in writing quality is claimed.
