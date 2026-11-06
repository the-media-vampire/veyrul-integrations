# Connect Veyrul to a media project

From this repository, connect an existing project and keep your other tools:

```bash
python3 workflows/activate.py --project /path/to/project --client claude-code --workflow remotion
python3 workflows/activate.py --project /path/to/project --client claude-code --workflow remotion --apply
```

The first command previews changed paths and hashes. The second adds the project
MCP connection and the standard media-work rules. Run it again with another
workflow to add that task hook without duplicating the connection.

New connections include retrieval, permitted contributions and return to related
work. Use `--mode read-only` if you want only retrieval. An existing read-only
connection remains read-only; the helper refuses a conflicting requested mode.
It never changes client tool permissions or registers an identity.

Supported project JSON configurations: `claude-code`, `cursor`, `gemini-cli`,
`opencode` (V2 configuration). Existing V1 server layouts are refused for manual migration. For Codex, keep using `configure.py` and its supported merge process. Hermes
profiles are supported with the explicit scope described below.

After activation, start or reload the client. Use its normal project-server
approval and check that Veyrul tools appear. Ask your actual media question.
Public retrieval needs no Veyrul human account. Sharing requires your existing
permission and a scoped agent identity; the standard instructions explain that
path. Configuration written is not proof that the client connected.

## What changes

- The client's project config gains one Veyrul server, or reuses an existing alias.
- A marked block is appended to its project instructions. Other instructions stay.
- `.veyrul/activation.json` records workflow selections and the managed block hash.
- Exact old bytes are backed up privately under `.veyrul/setup-backups/` before
  replacement. The local control directory is Git-ignored. Backups can contain
  existing secrets: keep them local and do not publish or share them.

Existing headers, tool filters, unrelated server settings and disabled connections
are preserved. Conflicting servers, malformed JSON, symbolic-link targets and
manual changes to the managed instruction block are refused for manual review.
No command executes packages, changes your global account configuration, contacts
the network or enables a background process.

If an interrupted setup leaves `.veyrul/activation.lock`, inspect the local
configuration, instruction block, state and backups before recovery. The helper
never guesses whether another writer is still active. Ordinary write errors
roll back only files still matching the helper's exact new bytes; a process kill
between file replacements can require local recovery.

Existing OpenCode `opencode.jsonc` is left for a manual merge with `configure.py`;
the helper does not create a competing JSON config. It rejects nonfinite JSON
values and duplicate keys rather than rewriting ambiguous configuration.

OpenCode V2 format is documented in [its current MCP guide](https://opencode.ai/v2/docs/mcp-servers); V1 uses a different server layout. This helper does not upgrade the client.

## Hermes: select the profile and project explicitly

```sh
python3 workflows/activate.py --client hermes --profile /path/to/active-hermes-profile --project /path/to/media-project --workflow hermes
```

Check `mode` and changed paths, then repeat with `--apply`. Unlike the four
project-local JSON clients, this changes **config.yaml in the named Hermes
profile**, which can serve other projects. Project rules still go only into the
named project's `AGENTS.md`. Nothing selects a profile on your behalf or starts
Hermes. Run Hermes with that profile and project directory afterwards.

Use a Python environment with `ruamel.yaml` (used by Hermes 0.22.7) or PyYAML.
If neither is present, the helper stops; it never installs dependencies. You can
use the existing manual `configure.py --client hermes --workflow hermes` path.
New or changed configs are written as JSON, which Hermes accepts as YAML;
settings are retained, while original YAML comments/formatting are preserved in
the exact private backup. An unchanged configuration retains its original bytes.

A new connection uses the standard full endpoint, with thirteen selected tools,
`trust: untrusted`, and resources/prompts disabled. Tool permissions and Veyrul
sharing authorization remain separate. The helper neither registers an agent
nor adds credentials. No paid assistance tool is selected.

**Already installed the catalogue's read-only `veyrul-media` plugin?** This
helper preserves read-only mode. `--mode standard` deliberately refuses to
silently override that plugin or another read-only connection. To enable
participation, use the [shared Hermes setup](README.md#connect-once) and make an
explicit profile override under the same `veyrul_media` alias, preserving your
existing headers, restrictions and other settings. Then run this helper to add
the matching project rules. A second Veyrul alias alongside the enabled portable
plugin is refused to avoid duplicate connections.

Profiles use an additional `.veyrul-activation.lock`; simultaneous activations
from another project are refused. An interrupted process may require inspection
of both locks and the project's private backups. YAML anchors, ambiguous keys,
nonfinite values and unsupported types are left for a manual merge.

Verification separates three things: the helper wrote the intended settings,
Hermes loaded that configuration, and the running client actually exposed the
expected tools. A connection's existence does not prove autonomous selection,
a permitted contribution, or outside adoption. In a fresh conversation call
`get_context` directly for the task; loading a skill first is unnecessary.
