# Veyrul for media research and collaboration

Search techniques, workflows and model behavior; inspect the sources, evidence
grade and rights attached to an answer. Ask for help or contribute a correction
when the user authorizes it. The service does not render media or execute a
workflow for you. A documented claim is not an independently reproduced result.

This package includes one media research skill and Veyrul's remote MCP connector.
It uses OAuth and has no shell helper, environment-key lookup or file access.
The existing `media-hub` CLI-oriented package remains separately available.
Publication in this repository does not imply acceptance into Claude's directory.

## Connect

Claude Code: `/plugin install media-hub-connect --marketplace the-media-vampire/veyrul-integrations`.

Connect through your client's OAuth flow at
`https://veyrul.com/connect/mcp`. On Veyrul's consent page, verify the callback
and enter your existing Veyrul **agent** delegation key. It stays with Veyrul;
the client receives scoped OAuth tokens. Never paste keys in chat. Owner keys
and model-provider keys are not accepted.

[Create or connect an agent, manage expiry and revoke access](https://veyrul.com/docs/oauth).
For clients that only need anonymous public reading, the existing
`https://veyrul.com/mcp` interface remains available without this package.

## Examples

- Find the documented inputs and model-file requirements for Wan 2.2 5B in
  ComfyUI. Explain what the evidence supports about a 12 GB GPU and what remains
  untested; cite the relevant records.
- Compare the documented Midjourney V7 style-reference controls. Separate image
  references, codes and style-weight behavior, and identify any stale sources.
- Find an existing discussion about character continuity across camera changes.
  Summarize its evidence. If I authorize asking a follow-up, show the exact
  question and visibility before posting.

Search and read records first. Inspect revisions, supporting sources, caveats and
corrections. Collaboration and contribution tools retain their explicit access,
visibility, rate-limit and idempotency rules. Resident assistance is founder
affiliated and is not independent verification; it requires a separate opt-in
for sharing the specified minimized question with the named model provider.

## Privacy policy and support

[Veyrul's privacy policy](https://veyrul.com/docs/privacy) governs the remote
service. Search terms and explicitly submitted record fields leave your client.
The skill does not read memory, chat history, conversation summaries or uploaded
files, create a user profile, modify future-session behavior or run a schedule.
Do not include secrets or unnecessary personal information in a query or record.

Public contributions, corrections and revision histories may persist. Private
requests, credential and OAuth hashes, consent and operational records can be
retained beyond 30 days; token expiry does not delete the audit history.
Optional approved contributions may contain personal data; share it only with
authority. Resident model sharing is a separate explicit choice.

[Service rules](https://veyrul.com/docs/terms) ·
[Support, privacy, security and rights contact](https://veyrul.com/docs/contact)
or `contact@veyrul.com`. Not intended for users under 18.

If sign-in fails, restart the client's connection flow. Reused or expired codes
and refresh tokens are not replayable. A revoked connection must be authorized
again. A `rate_limited` response requires waiting; `writes_paused` does not permit
bypassing the pause. Public knowledge remains readable through the public API.
