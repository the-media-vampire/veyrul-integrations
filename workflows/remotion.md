# Remotion: optional Veyrul knowledge companion

Before mapping word timestamps onto a composition with repeated source clips and speed changes.

[Set up the shared connection](README.md#connect-once) in your existing agent client,
then add the shared project rule and this task hook. This companion is published by
Veyrul; it is not an upstream integration or endorsement.

**Task hook:** Before mapping word timestamps onto a composition with repeated source clips and speed changes. Use Remotion for composition and rendering; inspect the saved library and its licence before reuse.

```json
{"name":"get_context","arguments":{"q":"Remotion word captions timing edited clips","detail":"compact","limit":3}}
```

Observed resource: [Edit-aware word timing: tested code for cuts, repeats and speed changes](https://veyrul.com/v1/records/art_01M6FTHTXK218N2MSF2FERAST5)
(record `art_01M6FTHTXK218N2MSF2FERAST5`, revision 1 at observation).
Read the current record before relying on it. Discovery results can change.

**Evidence:** bounded executed timing library; separate Remotion example.

**Limit:** The prior renderer checks used synthetic silent footage at 30 fps, not arbitrary production media.

**On related return:** Recheck record revisions when the edit, frame rate or timing model changes.

[Upstream instructions at the reviewed revision](https://github.com/remotion-dev/skills/blob/c7cb2fdcacd134fb2ccb9b7a44f9ffa44e467271/README.md).
[Connection and evidence limits](README.md#verification).
