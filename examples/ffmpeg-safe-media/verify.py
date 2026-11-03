#!/usr/bin/env python3
"""Original, bounded AAC stream-copy and output-preservation regression.
Requires Python 3.9+, FFmpeg/ffprobe with libx264 and AAC. No network calls.
Creates a NEW directory and retains all fixtures, output and diagnostics.
"""
import hashlib
import json
import math
import struct
import subprocess
import sys
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: python3 verify.py NEW_OUTPUT_DIRECTORY')
    root = Path(sys.argv[1]).resolve()
    root.mkdir(parents=True, exist_ok=False)
    calls = []

    def run(label, args, success=True):
        result = subprocess.run(args, capture_output=True, timeout=30)
        (root / (label + '.stdout')).write_bytes(result.stdout)
        (root / (label + '.stderr')).write_bytes(result.stderr)
        calls.append({'label': label, 'command': args, 'exit': result.returncode})
        if success and result.returncode != 0:
            raise RuntimeError(f'{label} failed; retained diagnostics in {root}')
        return result

    def packets(label, path, stream):
        result = run(label, ['ffprobe', '-v', 'error', '-select_streams', stream,
                     '-show_packets', '-show_data_hash', 'sha256', '-show_entries',
                     'packet=data_hash', '-of', 'json', str(path)])
        return [p['data_hash'] for p in json.loads(result.stdout)['packets']]

    source = root / 'input.mp4'
    selected = root / 'second-audio.mp4'
    run('version', ['ffmpeg', '-version'])
    run('fixture', ['ffmpeg', '-v', 'error', '-nostdin', '-n',
        '-f', 'lavfi', '-i', 'testsrc2=size=128x72:rate=24:duration=3',
        '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000:duration=3',
        '-f', 'lavfi', '-i', 'sine=frequency=880:sample_rate=48000:duration=3',
        '-map', '0:v:0', '-map', '1:a:0', '-map', '2:a:0',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-threads', '1',
        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '96k', str(source)])
    original_hash = digest(source)
    probe = json.loads(run('input-probe', ['ffprobe', '-v', 'error', '-show_streams',
                                         '-of', 'json', str(source)]).stdout)
    assert [s['codec_type'] for s in probe['streams']] == ['video', 'audio', 'audio']
    cmd = ['ffmpeg', '-v', 'error', '-nostdin', '-n', '-i', str(source),
           '-map', '0:v:0', '-map', '0:a:1', '-c', 'copy', str(selected)]
    run('select-second-audio', cmd)
    out_probe = json.loads(run('output-probe', ['ffprobe', '-v', 'error',
        '-show_streams', '-of', 'json', str(selected)]).stdout)
    assert [s['codec_name'] for s in out_probe['streams']] == ['h264', 'aac']
    before_video = packets('input-video-packets', source, 'v:0')
    after_video = packets('output-video-packets', selected, 'v:0')
    before_audio = packets('input-second-audio-packets', source, 'a:1')
    after_audio = packets('output-audio-packets', selected, 'a:0')
    assert before_video and before_video == after_video
    assert before_audio and before_audio == after_audio
    run('decode-selected', ['ffmpeg', '-v', 'error', '-nostdin', '-i', str(selected),
                           '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'])
    pcm = run('selected-pcm', ['ffmpeg', '-v', 'error', '-nostdin', '-i', str(selected),
        '-map', '0:a:0', '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '1', '-f', 's16le', '-']).stdout
    samples = struct.unpack('<' + 'h' * (len(pcm) // 2), pcm)[24000:48000]
    def power(hz):
        re = sum(x * math.cos(2 * math.pi * hz * i / 48000) for i,x in enumerate(samples))
        im = sum(x * math.sin(2 * math.pi * hz * i / 48000) for i,x in enumerate(samples))
        return re * re + im * im
    ratio = power(880) / max(power(440), 1)
    assert ratio > 100, 'wrong_audio_tone'
    selected_hash = digest(selected)
    selected_mtime = selected.stat().st_mtime_ns
    repeated = run('existing-output-refused', cmd, success=False)
    # FFmpeg 8.1 can return 0 after -n refuses an existing path. Check evidence.
    assert b'already exists' in repeated.stderr and digest(selected) == selected_hash
    assert selected.stat().st_mtime_ns == selected_mtime
    in_place = run('same-input-output-refused', ['ffmpeg', '-v', 'error', '-nostdin',
        '-y', '-i', str(source), '-map', '0:v:0', '-map', '0:a:1', '-c', 'copy', str(source)], success=False)
    assert in_place.returncode != 0 and digest(source) == original_hash
    assert b'same as Input' in in_place.stderr
    result = {'status': 'passed_in_stated_scope', 'source_sha256': original_hash,
        'source_unchanged': True, 'selected_sha256': selected_hash,
        'video_packets_equal': len(before_video), 'audio_packets_equal': len(before_audio),
        'selected_audio_880_to_440_power_ratio': ratio, 'decoded_all_selected_streams': True,
        'existing_output_refused_and_unchanged': True, 'same_path_refused_and_source_unchanged': True,
        'existing_output_refusal_exit': repeated.returncode, 'same_path_refusal_exit': in_place.returncode,
        'scope': 'Original 3-second 128x72 H.264 and two mono AAC tones; no spatial metadata, hardlink race or arbitrary production-media test.',
        'calls': calls}
    (root / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'calls'}, indent=2))


if __name__ == '__main__':
    main()
