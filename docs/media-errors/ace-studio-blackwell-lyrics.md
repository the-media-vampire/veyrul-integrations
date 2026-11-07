# ACE-Step Studio: lyrics degrade later on Blackwell GPUs

Founder-affiliated Veyrul research · reviewed 2026-11-07.

Match the application, engine and GPU before treating late-song lyric degradation as a prompt problem.

The [Studio 3.8.4 release note](https://github.com/timoncool/ACE-Step-Studio/releases/tag/v3.8.4) attributes a regression introduced with 3.8.0 to numerically incorrect CUDA flash attention on Blackwell cards, compute capability 10.0 and above. The publisher reports automatically disabling that path on affected cards in 3.8.4.

This is a Studio/backend-specific upstream report. It is not evidence that all unintelligible lyrics share that cause, that standalone ACE-Step versions behave identically, or that the change improves every GPU.

A useful incident note records the exact Studio build, backend and GPU capability, and whether the problem appears at the beginning or later. Preserve an existing problematic output. If a before/after generation is authorized, keep comparable settings and record uncertainty from generation variability; a different attractive song is not a controlled reproduction.

**Evidence:** release notes inspected; we did not install Studio, generate music or independently reproduce this fix. [Veyrul failure atlas](https://veyrul.com/articles/art_01M6V2D44ND0QGWCJW3GWYSKXF).

[Related saved context](https://veyrul.com/v1/context?q=ACE-Step+Studio+Blackwell+lyrics+unintelligible+flash+attention+3.8.4&detail=compact&limit=3) · [All five investigations](README.md)
