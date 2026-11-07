# ACE-Step Studio: LoRA training reports backend does not support on Turing

Founder-affiliated Veyrul research · reviewed 2026-11-07.

The error text alone is too broad to identify a fix. The relevant upstream case names a particular training step and GPU generation.

The [Studio 3.8.5 release note](https://github.com/timoncool/ACE-Step-Studio/releases/tag/v3.8.5) reports a HOT-Step trainer update with an F32 fallback for ConvRot8 on RTX 20-series Turing cards, compute capability 7.5, after a “backend does not support” failure.

Before applying this finding, record the Studio/trainer version, GPU capability and failing operation. If the operation is different, this release note does not diagnose it. Confirm that the installed trainer actually includes the reported change; an application version string alone may not establish every component's state.

A minimal permitted training check should preserve the input/configuration and record completion or the exact remaining failure. No training is requested merely by reading this page. Success at this step does not establish acceptable speed, VRAM fit, trained-model quality or rights to use a dataset.

**Evidence:** publisher-reported fix; no training or hardware benchmark executed by Veyrul. [Veyrul failure atlas](https://veyrul.com/articles/art_01M6V2D44ND0QGWCJW3GWYSKXF).

[Related saved context](https://veyrul.com/v1/context?q=ACE-Step+Studio+Turing+RTX+20+LoRA+backend+does+not+support+ConvRot8&detail=compact&limit=3) · [All five investigations](README.md)
