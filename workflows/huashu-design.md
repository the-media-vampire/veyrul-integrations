# Huashu Design: optional Veyrul knowledge companion

Before selecting generated SVG material for an animation or infographic.

[Set up the shared connection](README.md#connect-once) in your existing agent client,
then add the shared project rule and this task hook. This companion is published by
Veyrul; it is not an upstream integration or endorsement.

**Task hook:** Before selecting generated SVG material for an animation or infographic. Use Huashu for authoring and export; inspect the actual SVG primitives in the intended renderer.

```json
{"name":"get_context","arguments":{"q":"SVG motion graphics infographic animation","detail":"compact","limit":3}}
```

Observed resource: [StarVector (arXiv 2312.11556v4, CC BY 4.0): which SVG primitives a model writes as code, how SVG-Bench scores them, results as reported, stated limits, and a not-tested checklist for judging whether a generated SVG is ready for a motion-graphics tool (documented, not run)](https://veyrul.com/v1/records/art_01M6J61ECN2ZN6V51BFKBEFFJF)
(record `art_01M6J61ECN2ZN6V51BFKBEFFJF`, revision 1 at observation).
Read the current record before relying on it. Discovery results can change.

**Evidence:** documentary SVG research, not executed.

**Limit:** The saved StarVector material reports research; no generated asset or Huashu export was tested.

**On related return:** Preserve source, model/version and any editability or rendering failures.

[Upstream instructions at the reviewed revision](https://github.com/alchaincyf/huashu-design/blob/b2460b031c33ff32d2bf3b97263527daa231e4de/README.md).
[Connection and evidence limits](README.md#verification).
