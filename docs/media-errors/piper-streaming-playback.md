# Piper streaming: sentence chunks do not prove continuous playback

Founder-affiliated Veyrul research · reviewed 2026-11-07.

An iterator can yield valid synthesized chunks while its consuming player still truncates speech or mishandles the gap between sentences. Changing the TTS interface alone does not establish a playback fix.

At OHF Piper revision `10880972db9e0aca101fed350eadf8f49deefe9f`, the [Python API example](https://github.com/OHF-Voice/piper1-gpl/blob/10880972db9e0aca101fed350eadf8f49deefe9f/docs/API_PYTHON.md) consumes `audio_int16_bytes` with each chunk's sample rate, width and channel metadata. The [implementation](https://github.com/OHF-Voice/piper1-gpl/blob/10880972db9e0aca101fed350eadf8f49deefe9f/src/piper/voice.py#L354) processes sentence audio before yielding its chunk. Preserve the actual voice metadata rather than hardcoding a rate.

For an authorized local investigation, separate three observations: whether synthesis has finished, whether the player's queue has drained, and whether a real interruption occurred. A delayed next sentence with no microphone activity is a different case from a user interrupting during the delay. Do not disable interruption handling as a presumed cure.

**Evidence:** source inspection only. No Piper installation, speech generation, latency measurement or Hermes reproduction was performed. Package versions and voice-model rights must be checked separately. [Saved Veyrul source analysis](https://veyrul.com/replies/rpl_01M6S9EFV5919ADJSB85VQSY5J).

[Related saved context](https://veyrul.com/v1/context?q=Piper+TTS+streaming+sentence+chunks+PCM+playback+truncation&detail=compact&limit=3) · [All five investigations](README.md)
