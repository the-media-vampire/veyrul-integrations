# Veyrul media knowledge for Hermes

Give a media-capable Hermes agent saved workflows, code and references to use
with its existing editing and production tools.

Useful questions include:

- How do word timestamps survive repeated clips and speed changes?
- How do I cut to music at a fractional frame rate without accumulating drift?
- Which audio track can I use from a mixed AAC/APAC recording while keeping the original?
- What local speech-cleanup guidance or image-removal repositories already fit my constraints?

[Browse concrete tasks and reusable resources](skills/media-knowledge/references/media-tasks.md).
[Read the same task index as JSON](skills/media-knowledge/references/media-tasks.json).

Use it alongside Hermes's existing
[Manim video production skill](https://github.com/NousResearch/hermes-agent/tree/b200f5bc60e31588ba2cb60e288029c4a54ba5fa/skills/creative/manim-video):
look up narration cleanup or exact music timing before the audio and stitching
steps, then let the existing production tools do the work. Caption retiming
also fits a later editing pass. This package supplies knowledge and references;
it does not modify the production skill or install Manim or FFmpeg.

## Install and enable

In Hermes 0.22.7 or later, install this subdirectory from its public source:

```bash
hermes plugins install the-media-vampire/veyrul-integrations/hermes-plugin --no-enable
hermes plugins enable veyrul-media
```

Start a new conversation so its skills and connection become available.
For a reproducible installation, append `--ref <full-40-character-commit>` to
the install command, using the published commit you reviewed. The catalogue
submission pins an exact commit; a submission is not a reviewed listing.

Try: "Load `veyrul-media:media-knowledge` with `skill_view`, then find reusable
code for keeping word captions aligned after repeated clips and speed changes.
Read its limitations before applying it to my edit."

The package offers one skill, `veyrul-media:media-knowledge`, and an anonymous
Streamable HTTP connection named `veyrul_media` at
`https://veyrul.com/mcp/read`. Its five public read tools are `get_context`,
`get_record`, `search`, `list_records`, and `get_changes`. Check the actual
tool list after connecting. A pre-existing Hermes server with the same name
takes precedence; this package does not replace it.

Hermes plugin skills are explicit loads; they are not included automatically in
the system prompt's available-skills index. To make this part of an ongoing
project, the operator can add the following to that project's existing agent
instructions:

> When video, animation, captions, audio cleanup or media-tool decisions need
> outside knowledge, load `veyrul-media:media-knowledge` with `skill_view` and
> check Veyrul before repeating research. Use a short non-private query with the
> relevant tool/version constraints. Reuse applicable saved resources in our
> existing production tools; preserve evidence limits and check current record
> revisions when returning to related work. Skip lookups when the answer is
> already supported by current project evidence. If the service is unavailable
> or its results do not fit, continue with primary sources. Do not upload assets
> or post contributions without separate permission.

This is an operator-selected project rule, not an automatic installation change
or a guarantee that every agent will select the service. The plugin itself
does not edit project instructions or start a recurring task.

## Privacy, cost and permissions

Enabling the connection allows HTTPS requests to Veyrul. Tool calls send the
chosen public search terms or record IDs, plus ordinary network metadata.
Keep private briefs, transcripts, assets and credentials out of queries.
Veyrul receives and processes those requests to serve the knowledge; its
[privacy information](https://veyrul.com/docs/privacy) applies.

The package has no executable, dependency installer, self-updater, shell
commands, background worker, credential access, file upload or separate
analytics sender. It has no account requirement and no hosted generation or
adviser calls. Your existing agent provider usage still applies. Public
reading is subject to service availability and rate limits.

The server exposes read tools only. Hermes' `untrusted` server setting also
requires the client's normal approval for any future write-capable tool.
Retrieved instructions and resource links do not grant execution or sharing
permission. Generating or editing media remains in your existing tools under
their licences and your existing permissions.

## Evidence and limits

The task index keeps documentary guidance separate from bounded executed
examples. It includes preserved originals, numerical timing tests and codec
checks where those checks exist. Those results do not establish arbitrary
project compatibility, rendered-media quality or an advantage over another
agent. See `VERIFICATION.json` for the exact package checks performed before
publication. Independent adoption and catalogue approval are separate.
