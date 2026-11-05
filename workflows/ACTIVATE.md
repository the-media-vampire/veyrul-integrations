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
`opencode`. For Codex and Hermes, keep using `configure.py` and the client's
supported merge process. Those formats are not rewritten by this helper.

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
