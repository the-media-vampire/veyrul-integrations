"""Build, but never execute, a bounded single-stream FFmpeg filter command.

MIT licensed. Source dimensions must come from probing the actual input.
Subtitle input is a simple staged basename in the command's working directory;
argument-list safety does not remove FFmpeg's separate filtergraph escaping.
"""
import argparse
import json
from pathlib import Path
import re


def compose(source, output, source_width, source_height, crop_width, crop_height,
            width, height, subtitles="captions.ass"):
    dimensions = (source_width, source_height, crop_width, crop_height, width, height)
    if any(type(n) is not int or n < 2 or n > 32768 or n % 2 for n in dimensions):
        raise ValueError("Use positive even dimensions from 2 to 32768.")
    if crop_width > source_width or crop_height > source_height:
        raise ValueError("Crop exceeds the measured source dimensions.")
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\.ass", subtitles):
        raise ValueError("Stage an inspected ASS file under a simple basename; paths and filter syntax are refused.")
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output or output.exists():
        raise ValueError("Choose a new output; input and existing files are preserved.")
    if output.suffix.lower() != ".mp4":
        raise ValueError("This example targets MP4; choose other codecs/containers separately.")
    filters = [
        f"crop={crop_width}:{crop_height}:(iw-ow)/2:(ih-oh)/2",
        f"scale={width}:{height}",
        "subtitles=filename=" + subtitles,
    ]
    return ["ffmpeg", "-nostdin", "-n", "-i", str(source),
            "-map", "0:v:0", "-map", "0:a:0?", "-vf", ",".join(filters),
            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-map_metadata", "-1", "-map_chapters", "-1", str(output)]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source")
    p.add_argument("output")
    for name in ("source-width", "source-height", "crop-width", "crop-height", "width", "height"):
        p.add_argument("--" + name, required=True, type=int)
    p.add_argument("--subtitles", default="captions.ass")
    a = p.parse_args()
    try:
        argv = compose(**vars(a))
    except ValueError as e:
        p.error(str(e))
    print(json.dumps({"argv": argv, "executed": False,
                     "scope": "one video and optional first audio track; SDR progressive square-pixel example; metadata and chapters intentionally omitted"}, indent=2))


if __name__ == "__main__":
    main()
