# A Hermes agent reuses saved caption code, then returns after an edit

This controlled run used the actual Hermes 0.22.7 CLI and Veyrul plugin with
the native Codex runtime. An operator supplied the optional project rule once.
Neither task message named Veyrul. The agent found the saved resource, inspected
it, and applied its pinned Python implementation unchanged. On the changed edit
it re-read the current record and reused that implementation.

The two outputs match 13 frozen caption intervals and both total durations.
This verifies numerical reuse and a related return under explicit opt-in.
It does not establish independent adoption, default selection, production video
quality, or better speed or cost than another agent.

## Reproduce the media task

Use an already configured Hermes client and the [Veyrul plugin](../../hermes-plugin/README.md).
Copy `AGENTS.md`, `words.json`, `cuts-initial.json` and `cuts-return.json` into a
new task directory. Review the project rule before adopting it. Do not give the
agent the expected outputs. Ask it to perform `TASK-INITIAL.txt`, then send
`TASK-RETURN.txt` into the same session. Keep both sets of inputs and outputs.
The required media work is timing data only; no generated footage is needed.

The saved resource is [record art_01M6FTHTXK218N2MSF2FERAST5](https://veyrul.com/articles/art_01M6FTHTXK218N2MSF2FERAST5),
revision 1 in this run. Its [MIT-licensed timing code](https://github.com/the-media-vampire/veyrul-integrations/blob/3cc67c39b5ad6769e2463b9bf915ae1f6eba6fd7/examples/edit-aware-word-timing/media_timeline.py)
uses exact cumulative durations and rounds absolute boundaries half up.
The agent-written `retime_captions.py` adapter expects that inspected file at
`vendor/edit-aware-word-timing-3cc67c3/media_timeline.py`. Verify the SHA-256 in
`VERIFICATION.json` before running it; it refuses to overwrite its output.
For example, `python3 -B retime_captions.py words.json cuts-initial.json my-initial.json`.
Read the saved code specification and limitations before execution. The agent's task is
to discover and inspect applicable resources; the link here explains our result.

Run `python3 check_outputs.py` beside the two supplied output files to verify
the published arithmetic. For your own run, check copies of your outputs against
the same frozen expected values. Repeated source segments must remain separate
caption occurrences. Frame-grid conversion, subtitle layout, audio sync and
rendered readability need their own production checks.

## Client setup and honest limits

The trial used an existing signed-in client, optional model auxiliaries disabled,
and a bounded anonymous MCP recorder. Hermes and Codex core were unmodified.
Global client settings and credentials were unchanged. An initial setup attempt
used CLI flags unsupported by Hermes's gateway route; the supported profile
budget setting and skill toolset resolved those launch errors. A preliminary
pair also loaded unrelated global workstation instructions; it was excluded
from the final isolated selection evidence and retained in the cost totals.

The unattended Codex callback refused `skill_view`. Direct read-only Veyrul
retrieval remained usable and the agent recovered. A normal interactive client
can approve the local skill read; operators can also use Hermes's supported
skill-preload option. Do not disable approval for unrelated tools. We do not
claim every client or approval configuration was tested.

Veyrul performed saved-knowledge retrieval, with no hosted adviser or generation
call. The operator's agent still consumed its existing provider allowance.
`VERIFICATION.json` includes all diagnostic model usage and service requests;
those token counts are not an invoice. The service's hosting/storage costs and
rate limits still apply. No speed or dollar-saving comparison was performed.
