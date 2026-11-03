#!/usr/bin/env python3
"""Compare pinned upstream and the patch on actual FFmpeg media, without modifying the checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path, help="video-editing-skill at the commit in UPSTREAM.json")
    parser.add_argument("output_dir", type=Path, help="new folder; an existing folder is refused")
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    pin = json.loads((here / "UPSTREAM.json").read_text())
    source = args.checkout.resolve() / "scripts"
    for name, expected in pin["files"].items():
        if sha(source / name) != expected:
            parser.error("upstream bytes do not match UPSTREAM.json: " + name)
    root = args.output_dir.resolve()
    root.mkdir(parents=True, exist_ok=False)
    for variant in ["upstream", "patched"]:
        folder = root / variant / "scripts"
        folder.mkdir(parents=True)
        for name in pin["files"]:
            shutil.copyfile(source / name, folder / name)
    subprocess.run(["git", "apply", "--check", str(here / "fix.patch")],
                   cwd=root / "patched", check=True, timeout=10)
    subprocess.run(["git", "apply", str(here / "fix.patch")],
                   cwd=root / "patched", check=True, timeout=10)
    subprocess.run(["bash", "-n", str(root / "patched/scripts/edit.sh")], check=True, timeout=10)
    fixture = root / "source.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-n", "-f", "lavfi", "-i",
                    "testsrc2=size=128x72:rate=24:duration=4", "-f", "lavfi", "-i",
                    "sine=frequency=440:sample_rate=48000:duration=4", "-c:v", "libx264",
                    "-preset", "ultrafast", "-g", "1", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    "-shortest", str(fixture)], check=True, timeout=30)
    original_hash = sha(fixture)
    results = []
    for variant in ["upstream", "patched"]:
        output = root / (variant + ".mp4")
        command = ["bash", str(root / variant / "scripts/edit.sh"), str(fixture),
                   "--trim-start", "0", "--trim-duration", "2", "--speed", "2", "--output", str(output)]
        executed = subprocess.run(command, text=True, capture_output=True, timeout=45)
        log = executed.stdout + executed.stderr
        (root / (variant + ".log")).write_text(log)
        result = {"variant": variant, "exit_code": executed.returncode,
                  "output_exists": output.exists(), "source_unchanged": sha(fixture) == original_hash}
        assert result["source_unchanged"]
        if variant == "upstream":
            assert executed.returncode != 0 and not output.exists()
            assert "cannot edit existing files in-place" in log
        else:
            assert executed.returncode == 0 and output.is_file()
            probe = json.loads(subprocess.check_output([
                "ffprobe", "-v", "error", "-show_entries",
                "stream=codec_type,duration,nb_frames:format=duration", "-of", "json", str(output)]))
            assert {x["codec_type"] for x in probe["streams"]} == {"audio", "video"}
            assert 0.9 <= float(probe["format"]["duration"]) <= 1.2
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(output),
                            "-f", "null", "-"], check=True, timeout=30)
            result["probe"] = probe
            result["full_decode_passed"] = True
        results.append(result)
    report = {"schema": "video-editing-chain-evaluation/1", "upstream": pin,
              "fixture": "original 4-second 128x72 test pattern and 440 Hz tone",
              "operations": ["trim to 2 seconds", "speed 2x"], "results": results,
              "ffmpeg": subprocess.check_output(["ffmpeg", "-version"], text=True).splitlines()[0],
              "limits": ["Fixes temporary-name collision only", "No Whisper/generation/API call",
                        "Existing trim and speed rounding is unchanged; output was 1.083333 seconds",
                        "No general caption alignment, overwrite policy or media-quality claim"]}
    (root / "EVALUATION.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
