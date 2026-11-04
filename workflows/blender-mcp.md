# Blender MCP: optional Veyrul knowledge companion

Before choosing an AI-generated animated asset format for a Blender pipeline.

[Set up the shared connection](README.md#connect-once) in your existing agent client,
then add the shared project rule and this task hook. This companion is published by
Veyrul; it is not an upstream integration or endorsement.

**Task hook:** Before choosing an AI-generated animated asset format for a Blender pipeline. Use Blender MCP for scene inspection and execution, with the existing operator permissions.

```json
{"name":"get_context","arguments":{"q":"Blender glTF export materials animation","detail":"compact","limit":3}}
```

Observed resource: [Can I get an animated file I can open in Blender, Unreal or Unity (mesh sequence, PLY sequence, glTF, Alembic) out of these text/image/video-to-4D systems, and what did the authors actually release?](https://veyrul.com/v1/records/art_01M5NBF1B58NQCAH2Y0206A6Z0)
(record `art_01M5NBF1B58NQCAH2Y0206A6Z0`, revision 1 at observation).
Read the current record before relying on it. Discovery results can change.

**Evidence:** partial coverage: documentary asset-format evidence.

**Limit:** The initial broad glTF-export query returned adjacent evidence, not a verified Blender exporter workflow. Check current Blender documentation.

**On related return:** Retain the source format, dependencies and import observations for the next asset.

[Upstream instructions at the reviewed revision](https://github.com/ahujasid/mcp-for-blender/blob/992233bb258975a05eec8b5691465c50c2831e34/README.md).
[Connection and evidence limits](README.md#verification).
