# FFmpeg: preserve originals and select the intended audio

Three saved guides with runnable, local evidence:

- [Safe chained editing and the repeated step_1.mp4 bug](safe-editing.md)
- [Copy video and only the second audio stream](audio-stream-selection.md)
- [Apple APAC: codec-name trap, actual compatibility tests and limits](apple-apac.md)

The two scripts create new directories containing small, original synthetic
media. They retain inputs, failed outputs and diagnostics; they make no network
or model calls. Review the code before running it with your existing tools.

```bash
python3 verify.py ./stream-check-01
# macOS with afconvert only:
python3 probe_apple_apac.py ./apac-check-01
```

Python 3.9+, FFmpeg and ffprobe are required. `verify.py` also needs an FFmpeg
build with libx264 and AAC encoding. The APAC probe needs Apple's installed
`afconvert`; other operating systems are not covered by that script. Existing
output directories are refused. Each subprocess has a 30-second timeout.

[EVALUATION.json](EVALUATION.json) records measured results on macOS 26.3 with
Homebrew FFmpeg 8.1. These are founder-operated engineering checks, not an
independent benchmark, iPhone spatial-playback validation or a promise about
all FFmpeg versions. Failed expectations during development were retained in
the private QA archive; published observations describe the final checked code.

The code and original guide prose are [MIT](LICENSE). FFmpeg, Apple tools and
linked upstream projects retain their own licences. No third-party footage is
included. Agents can retrieve these findings through Veyrul and run the code
locally; no hosted creative adviser or generation service is required.
