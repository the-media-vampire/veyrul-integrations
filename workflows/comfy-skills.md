# Comfy product skills: optional Veyrul knowledge companion

Before choosing a VACE inpainting template or changing frame-count and resolution constraints.

[Set up the shared connection](README.md#connect-once) in your existing agent client,
then add the shared project rule and this task hook. This companion is published by
Veyrul; it is not an upstream integration or endorsement.

**Task hook:** Before choosing a VACE inpainting template or changing frame-count and resolution constraints. Check the installed nodes, model files, hardware and current Comfy documentation.

```json
{"name":"get_context","arguments":{"q":"ComfyUI VACE video inpainting workflow","detail":"compact","limit":3}}
```

Observed resource: [What constraints does ComfyUI's Wan2.1 VACE guide state for frame count, batch size, resolution and run time when doing reference, control, inpaint or first/last-frame video?](https://veyrul.com/v1/records/art_01M5NPXF51QJG43ZPXCCZG2T9D)
(record `art_01M5NPXF51QJG43ZPXCCZG2T9D`, revision 1 at observation).
Read the current record before relying on it. Discovery results can change.

**Evidence:** documentary guidance, not executed.

**Limit:** Saved documentation does not establish successful GPU execution or visual quality.

**On related return:** Re-read the exact template and constraints after a model or node update.

[Upstream instructions at the reviewed revision](https://github.com/Comfy-Org/comfy-skills/blob/b0fc74c0fc83709c5538df578615f876d4ed52d6/README.md).
[Connection and evidence limits](README.md#verification).
