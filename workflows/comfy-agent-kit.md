# ComfyUI Agent Kit: optional Veyrul knowledge companion

After generated clips have been cut, repeated or sped up, before creating word captions.

[Set up the shared connection](README.md#connect-once) in your existing agent client,
then add the shared project rule and this task hook. This companion is published by
Veyrul; it is not an upstream integration or endorsement.

**Task hook:** After generated clips have been cut, repeated or sped up, before creating word captions. Keep graph building and GPU generation in the existing ComfyUI tools.

```json
{"name":"get_context","arguments":{"q":"word captions repeated clips speed changes","detail":"compact","limit":3}}
```

Observed resource: [Edit-aware word timing: tested code for cuts, repeats and speed changes](https://veyrul.com/v1/records/art_01M6FTHTXK218N2MSF2FERAST5)
(record `art_01M6FTHTXK218N2MSF2FERAST5`, revision 1 at observation).
Read the current record before relying on it. Discovery results can change.

**Evidence:** bounded executed timing library.

**Limit:** The caption library does not generate footage or prove a ComfyUI-to-Resolve round trip.

**On related return:** Preserve clip mapping and word-timing assumptions on the next edit.

[Upstream instructions at the reviewed revision](https://github.com/SlavaSexton/ComfyUI-Agent-Kit/blob/0d259059b55b0cc57ae45b232dbc03281621de35/README.md).
[Connection and evidence limits](README.md#verification).
