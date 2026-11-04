# Media workflow companions

Use saved media knowledge inside the agent and production workflow you already use.
One direct MCP connection serves all ten companions below. No Veyrul account,
API key, skill loader or new model service is required for reading.

## Pick the production decision

| Existing workflow | Lookup point |
| --- | --- |
| [ComfyUI Agent Kit](comfy-agent-kit.md) | After generated clips have been cut, repeated or sped up, before creating word captions. |
| [Comfy product skills](comfy-skills.md) | Before choosing a VACE inpainting template or changing frame-count and resolution constraints. |
| [Remotion](remotion.md) | Before mapping word timestamps onto a composition with repeated source clips and speed changes. |
| [Blender MCP](blender-mcp.md) | Before choosing an AI-generated animated asset format for a Blender pipeline. |
| [Blender Agent Skills](blender-skills.md) | When deciding whether a rig-generation tool also supplies animation retargeting. |
| [LottieFiles Motion Design](motion-design.md) | When a chosen motion direction needs playback, renderer or platform-compatibility evidence. |
| [Hallmark](hallmark.md) | When preparing an authorized image asset for a design and deciding whether local background removal is appropriate. |
| [Huashu Design](huashu-design.md) | Before selecting generated SVG material for an animation or infographic. |
| [REAPER MCP](reaper.md) | Before choosing a local narration-cleanup method, then compare the processed copy in the existing session. |
| [Hermes media production](hermes.md) | Before narration cleanup, beat-based editing or reuse of saved caption-timing code. |

## Connect once

Keep the existing production tools connected. Merge one client snippet below into
its existing project configuration; preserve other servers and settings. If you
already have a Veyrul connection, reuse it instead of adding a duplicate.
Approve the intended project/server using that client's normal trust UI, then
start a fresh session or refresh MCP discovery. Client permissions still apply.

Add [the project rule](PROJECT-INSTRUCTIONS.txt) and your chosen companion's
**Task hook** to the client's existing project instructions after reviewing them.
The rule gives a trigger and a return checkpoint; it never starts a background job.
The server also provides lookup and return guidance through MCP initialization.

A repository checkout includes an optional Python 3 helper that prints the exact
snippet and task rule. It makes no network request, writes no file and changes no
configuration:

```bash
python3 workflows/configure.py --client claude-code --workflow reaper
```

Use `--list` for all workflow IDs or `--format json` for a machine-readable setup
plan. The helper prints only Veyrul's addition; merge it, never overwrite your
current config or project instructions.

### codex

Merge into `.codex/config.toml`; add the reviewed rule to `AGENTS.md`.

```toml
[mcp_servers.veyrul_media]
url = "https://veyrul.com/mcp/read"
enabled_tools = ["get_context", "get_record", "search", "list_records", "get_changes"]
startup_timeout_sec = 20
tool_timeout_sec = 30
```

[Official configuration reference](https://learn.chatgpt.com/docs/extend/mcp).

### claude-code

Merge into `.mcp.json`; add the reviewed rule to `CLAUDE.md`.

```json
{
  "mcpServers": {
    "veyrul_media": {
      "type": "http",
      "url": "https://veyrul.com/mcp/read"
    }
  }
}
```

[Official configuration reference](https://code.claude.com/docs/en/mcp).

### cursor

Merge into `.cursor/mcp.json`; add the reviewed rule to `AGENTS.md`.

```json
{
  "mcpServers": {
    "veyrul_media": {
      "url": "https://veyrul.com/mcp/read"
    }
  }
}
```

[Official configuration reference](https://cursor.com/docs/mcp).

### gemini-cli

Merge into `.gemini/settings.json`; add the reviewed rule to `GEMINI.md`.

```json
{
  "mcpServers": {
    "veyrul_media": {
      "httpUrl": "https://veyrul.com/mcp/read",
      "timeout": 30000,
      "trust": false,
      "includeTools": [
        "get_context",
        "get_record",
        "search",
        "list_records",
        "get_changes"
      ]
    }
  }
}
```

[Official configuration reference](https://geminicli.com/docs/tools/mcp-server/).

### Hermes

Use the [portable Hermes plugin](../hermes-plugin/README.md), then add the same
project rule and desired task hook. Call `veyrul_media.get_context` directly;
loading the optional skill is not a prerequisite. The plugin retains the client's
normal permissions and does not edit project instructions.

## First use and return

1. Confirm the five read tools: `get_context`, `get_record`, `search`,
   `list_records`, `get_changes`. Tool prefixes vary by client.
2. Use the companion's example only for a relevant real task. Reject mismatched
   results; inspect execution status, source version and resource rights.
3. Reuse an applicable resource with your existing tools and permissions.
4. Keep a useful record ID/revision and what it supported in permitted project
   notes. On a later related task, reread that record before reuse.
5. When already authorized to share, follow the separate
   [contribution setup](../examples/contributions.md) to preserve an observed
   result or correction. Reading never requires contribution.

If the optional skill helper asks for approval in an unattended session, use
approved direct read tools. This removes the helper dependency; it does not
change or bypass the client's permission policy. If the read connection itself
is blocked, use permitted primary sources and finish the task.

## Privacy and cost

Queries and record IDs go to Veyrul with ordinary request metadata. Keep private
briefs, source assets, transcripts and credentials out. [Privacy](https://veyrul.com/docs/privacy).
This package makes no model, generation or hosted adviser calls. Your existing
agent provider usage and production-tool costs still apply. Public reads are
subject to service availability and rate limits. External resources have their
own licences and access conditions.

## Verification

The live read endpoint, five read-only tools, server guidance, ten topic queries
and a current-record reread were checked on 2026-11-04. Client snippets follow
the linked official documentation and parse locally. That is not a full run of
all four clients or all ten production applications. See [VERIFICATION.json](VERIFICATION.json).

Most retrieved resources are documentary. Captions have separate
[executed examples](../examples/remotion-retimed-captions/README.md) and an
[actual Hermes use/return trial](../examples/hermes-media-return/README.md).
Blender exporter coverage was partial; its companion explicitly continues with
current primary documentation. Saved evidence is not a quality, latency or cost
advantage claim. These are Veyrul-maintained opt-in companions; upstream
acceptance and independent usage remain separate.

[Machine-readable workflow index](manifest.json).
