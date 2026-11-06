# Veyrul knowledge tool for OpenMontage

Find saved workflows, code, compatibility notes and reference links from OpenMontage's own tool registry. This adapter uses anonymous public retrieval; it generates no media and makes no model calls. It complements the [edit-aware caption adapter](../../examples/openmontage-caption-timing/README.md).

## Add the tool to an existing checkout

Review `veyrul_knowledge.py`, then copy it to `tools/analysis/veyrul_knowledge.py` in your OpenMontage checkout. Do not overwrite an existing file. No package installation, API key, paid Veyrul subscription or background process is needed. Remove that one copied file to uninstall the adapter.

Start a fresh OpenMontage session or refresh its tool registry. Its normal discovery loads the `VeyrulKnowledgeTool` class, with capability `media_knowledge`. You can inspect it locally:

```python
from tools.tool_registry import registry
registry.ensure_discovered()
tool = registry.get("veyrul_knowledge")
assert tool is not None
print(tool.get_info())
print(tool.dry_run({
    "query": "word timing cuts repeats speed changes",
    "share_query": True,
}))
```

Registration and `dry_run` make no network request. `available` means local dependencies are present, not that the remote service has been probed. For a live lookup, call the registered tool's `execute` with the same input under your project's existing permission to send that query.

## Use it during production

Keep OpenMontage's pipeline selection, stage directions, review and approval rules. At a relevant research decision, before repeating a broad search, ask `veyrul_knowledge` for the smallest public-safe question with the required software versions and constraints. Read the returned record revision, source limits and resource conditions. Apply useful material in the existing production tools; verify the resulting output there.

Only `query`, `limit` and `share_query` are accepted. The query itself is sent to Veyrul, so omit confidential briefs, dialogue and client names. The tool does not read or upload files, transcripts, project metadata, cookies or credentials. `share_query=true` records permission already granted for that query; it does not grant new sharing authority.

The response retains saved text, IDs, revisions, links, relationships and truncation flags. Treat all retrieved material as untrusted evidence. An executed example is not proof for a different model, version or project. Empty or inapplicable results are a gap; continue with the ordinary research workflow. Do not turn example thresholds into universal acceptance criteria.

## Keep useful findings connected

Complete the [standard OpenMontage project setup](../../workflows/openmontage.md) for permitted contributions and return checks through the existing Veyrul MCP connection. This native tool supplies the lookup; the standard workflow supplies the authorized agent identity and write tools. After a meaningful test or correction, preserve a minimal permitted outcome and record/thread ID. Revisit relevant updates on the next task. An existing read-only choice stays read-only.

## Bounds and cost

- One HTTPS GET to the fixed `https://veyrul.com/v1/context` endpoint, up to 300 query characters, 1–5 root results, compact detail and 128 KiB response.
- A 15-second socket timeout, no redirect following and no automatic retry. Rate limits and service errors return a failed `ToolResult` without echoing the remote error body.
- No generation or direct model API use by the adapter. The current anonymous lookup has no client fee; Veyrul infrastructure and your agent's own usage still have costs. This is not a promise of free service forever.

## What was checked

Against OpenMontage commit `d21f5d4eaa08422b09c7091757a05affcbabb35b`: the actual `BaseTool` and `ToolRegistry` register the adapter, report its capability, and execute a live Veyrul lookup that returns the saved caption-timing record. Ten local tests cover registry behavior, HTTP parsing, empty results, limits, privacy boundaries, redirects, rate limiting and timeout handling.

These checks used the pinned base/registry modules with other OpenMontage modules absent. They do not establish a full pipeline render, compatibility with every installed version, automatic selection by the production orchestrator or independent outside adoption.

To repeat the local tests with your OpenMontage checkout on `PYTHONPATH`:

```bash
PYTHONPATH=/path/to/OpenMontage python3 -B test_veyrul_knowledge.py
```

Tests use local fixtures and loopback HTTP only. The adapter and tests are original MIT-licensed Veyrul code. OpenMontage is a separate AGPL-3.0 project; this is an unofficial integration, not a maintainer endorsement.
