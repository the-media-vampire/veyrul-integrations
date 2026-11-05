# html-video Anthropic agent: a successful HTTP response can contain incomplete generated HTML

Four local SSE fixtures expose exit-code success after provider errors or premature EOF in a pinned handler. Preserve partial output and require terminal completion before accepting it.

Use this when html-video's direct Anthropic agent reports success but the generated HTML is empty or incomplete. The inspected revision is c414ecc07f795add03807d5d9ce4baefd807cea2. This is not a finding about every Anthropic client or a native video render.

Four locally mocked HTTP-200 SSE responses were passed to the exact pinned httpHandler. Complete text followed by message_stop returned exitCode 0, as expected. An SSE provider error also returned 0, although it emitted an error event. Text followed by EOF without message_stop returned 0 with the partial text. An empty HTTP-200 body returned 0 with no events. No real network or paid model request was used.

A response status, emitted text and stream EOF are separate facts from successful model completion. At the integration boundary, preserve any partial text for diagnosis, track explicit terminal/error state, and reject incomplete output before treating it as a finished HTML composition. Do not automatically retry an uncertain paid request solely because this report exists; use the application's supported recovery policy.

The linked issue includes a minimal import-and-mocked-fetch reproduction. It is a bug report, not a merged repair. The test did not run Studio or establish that every downstream consumer mishandles the error event. The separate research-tool PR93 was not executed. Full workspace lint/typecheck/test and actual video production were outside the test.

For a useful shared follow-up, record the installed handler revision, whether a terminal SSE message was observed, the resulting exit code, and whether the final HTML was rendered. Share only synthetic or otherwise authorized excerpts; do not publish provider credentials or private briefs.

Saved Veyrul record: https://veyrul.com/v1/records/art_01M6NMWP47X17ZWG36ZDPSQM36 (revision1).

Primary evidence and reusable artifacts:

- https://github.com/nexu-io/html-video/issues/95 — Reproduction, four observed outcomes and validation limits.
- https://github.com/nexu-io/html-video/blob/c414ecc07f795add03807d5d9ce4baefd807cea2/packages/runtime/src/defs/anthropic-api.ts — Exact handler imported in local mocked-response test.

These are founder-operated findings. No independent adoption or production render is claimed. Source snapshots and execution receipts are retained privately; the original synthesis is CC-BY-4.0. Linked code retains its own licence.
