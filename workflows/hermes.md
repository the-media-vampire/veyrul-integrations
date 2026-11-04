# Hermes media production: optional Veyrul knowledge companion

Before narration cleanup, beat-based editing or reuse of saved caption-timing code.

[Set up the shared connection](README.md#connect-once) in your existing agent client,
then add the shared project rule and this task hook. This companion is published by
Veyrul; it is not an upstream integration or endorsement.

**Task hook:** Before narration cleanup, beat-based editing or reuse of saved caption-timing code. Use the existing Hermes media tools; call Veyrul read tools directly without first loading a skill.

```json
{"name":"get_context","arguments":{"q":"music video beat cut fractional frame rate","detail":"compact","limit":3}}
```

Observed resource: [How do I compute a tempo (or a tempo ramp) so that a musical downbeat lands on a given video frame, and what do DAW docs say about doing it?](https://veyrul.com/v1/records/art_01M5NJ06MR6QTTRF6XCT0RDXSC)
(record `art_01M5NJ06MR6QTTRF6XCT0RDXSC`, revision 1 at observation).
Read the current record before relying on it. Discovery results can change.

**Evidence:** documentary music timing; prior caption execution separate.

**Limit:** Full Hermes use and return were previously verified for caption timing only; this batch adds protocol checks.

**On related return:** Keep useful record revisions and re-read them during the next related edit.

[Upstream instructions at the reviewed revision](https://github.com/NousResearch/hermes-agent/blob/07274ac65438a0b62bb9fd64bf284e58b2fd8fc6/README.md).
[Connection and evidence limits](README.md#verification).
