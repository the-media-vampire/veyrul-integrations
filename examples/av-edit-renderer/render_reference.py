#!/usr/bin/env python3
"""Controlled reference renderer for timestamp-faithful short edits.

Original shared-study rendering logic, internally checked on calibration clips.
See EVALUATION.json and README.md for provenance, evidence and strict limits.
Use render.py for a guarded output path and whole-process timeout.
"""
import argparse
from bisect import bisect_right
from decimal import Decimal
from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess
import threading

import numpy as np

FFMPEG = os.environ.get('FFMPEG', '/opt/homebrew/bin/ffmpeg')
FFPROBE = os.environ.get('FFPROBE', '/opt/homebrew/bin/ffprobe')
FPS, RATE, WIDTH, HEIGHT = 24, 48000, 128, 72


def run(args):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=30)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors='replace'))
    return p.stdout


def ceilq(q):
    return -(-q.numerator // q.denominator)


def nearest(q):
    return (2 * q.numerator + q.denominator) // (2 * q.denominator)


def timestamp(frame, stream):
    value = frame.get('pts', frame.get('best_effort_timestamp'))
    if value is None:
        raise ValueError('Decoded frame has no presentation timestamp')
    return int(value) * Fraction(stream['time_base'])


def load_source(path):
    p = json.loads(run([FFPROBE, '-v', 'error', '-show_streams',
                        '-show_frames', '-of', 'json', str(path)]))
    video = next(s for s in p['streams'] if s['codec_type'] == 'video')
    vf = [f for f in p['frames'] if f['stream_index'] == video['index']]
    if not vf or (video['width'], video['height']) != (WIDTH, HEIGHT):
        raise ValueError('Expected decoded 128x72 video')
    origin = timestamp(vf[0], video)
    times = [timestamp(f, video) - origin for f in vf]
    if times != sorted(times):
        raise ValueError('Video presentation timestamps are not ordered')
    raw = run([FFMPEG, '-v', 'error', '-copyts', '-i', str(path),
               '-map', '0:v:0', '-an', '-fps_mode', 'passthrough',
               '-pix_fmt', 'rgb24', '-f', 'rawvideo', 'pipe:1'])
    frame_bytes = WIDTH * HEIGHT * 3
    if len(raw) != len(times) * frame_bytes:
        raise ValueError('Probe/decode frame counts disagree')
    frames = np.frombuffer(raw, dtype=np.uint8).reshape(-1, frame_bytes)
    result = {'times': times, 'frames': frames, 'audio': None,
              'audio_offset': Fraction(0)}
    audio = next((s for s in p['streams'] if s['codec_type'] == 'audio'), None)
    if audio is None:
        return result
    af = [f for f in p['frames'] if f['stream_index'] == audio['index']]
    if not af:
        return result
    channels = int(audio['channels'])
    if channels not in (1, 2):
        raise ValueError('Only mono/stereo sources are in this contract')
    first = timestamp(af[0], audio)
    source_rate = int(audio['sample_rate'])
    # Matroska millisecond rounding is not an audio discontinuity. Keep sample
    # continuity; reject actual gaps instead of silently compressing them.
    total = 0
    tolerance = max(Fraction(audio['time_base']), Fraction(1, source_rate))
    for frame in af:
        if abs(timestamp(frame, audio) - first - Fraction(total, source_rate)) > tolerance:
            raise ValueError('Discontinuous source audio is outside these fixtures')
        total += int(frame['nb_samples'])
    pcm = run([FFMPEG, '-v', 'error', '-copyts', '-i', str(path),
               '-map', '0:a:0', '-vn', '-af', 'aresample=48000:async=0',
               '-ac', str(channels), '-c:a', 'pcm_s16le', '-f', 's16le', 'pipe:1'])
    samples = np.frombuffer(pcm, dtype='<i2').reshape(-1, channels)
    if channels == 1:
        samples = np.repeat(samples, 2, axis=1)
    result['audio'] = samples
    result['audio_offset'] = first - origin
    return result


def audio_block(source, start, end, count):
    block = np.zeros((count * 2000, 2), dtype='<i2')
    data = source['audio']
    if data is None:
        return block
    # Exact half-open clip interval, including fractional final-frame padding.
    valid = min(len(block), ceilq((end - start) * RATE))
    pos = (start - source['audio_offset']) * RATE
    index = nearest(pos)
    lo = max(0, ceilq(-pos), -index)
    hi = min(valid, len(data) - index)
    if hi > lo:
        block[lo:hi] = data[index + lo:index + hi]
    return block


def render(manifest, output):
    manifest = Path(manifest).resolve()
    output = Path(output).resolve()
    job = json.loads(manifest.read_text(), parse_float=Decimal)
    if (job.get('fps'), job.get('width'), job.get('height')) != (FPS, WIDTH, HEIGHT):
        raise ValueError('Contract requires 24 fps and 128x72')
    if not job.get('clips'):
        raise ValueError('At least one clip is required')
    plans, sources = [], {}
    source_paths = {name: (manifest.parent / value).resolve()
                    for name, value in job['sources'].items()}
    if output == manifest or output in source_paths.values():
        raise ValueError('Output would overwrite an input')
    for clip in job['clips']:
        name = clip['source']
        start, end = Fraction(clip['in_s']), Fraction(clip['out_s'])
        if not (0 <= start < end <= Fraction(29, 10)):
            raise ValueError('Expected 0 <= in_s < out_s <= 2.9')
        path = source_paths[name]
        if path not in sources:
            sources[path] = load_source(path)
        plans.append((sources[path], start, end, ceilq((end - start) * FPS)))
    output.parent.mkdir(parents=True, exist_ok=True)
    # Two pipes stream the output, avoiding a large raw-video scratch file.
    read_fd, write_fd = os.pipe()
    cmd = [FFMPEG, '-v', 'error', '-y', '-thread_queue_size', '64',
           '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', '128x72',
           '-framerate', '24', '-i', 'pipe:0', '-thread_queue_size', '64',
           '-f', 's16le', '-ar', '48000', '-ac', '2', '-i', 'pipe:' + str(read_fd),
           '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'ffv1', '-level', '3',
           '-pix_fmt', 'bgr0', '-fps_mode', 'passthrough', '-c:a', 'pcm_s16le',
           '-f', 'matroska', str(output)]
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE, pass_fds=(read_fd,))
    except BaseException:
        os.close(read_fd)
        os.close(write_fd)
        raise
    os.close(read_fd)
    errors = []
    timed_out = threading.Event()

    def kill_on_timeout():
        timed_out.set()
        proc.kill()

    timer = threading.Timer(90, kill_on_timeout)
    timer.daemon = True
    timer.start()

    def feed_audio():
        try:
            with os.fdopen(write_fd, 'wb') as pipe:
                for source, start, end, count in plans:
                    pipe.write(audio_block(source, start, end, count).tobytes())
        except BaseException as error:
            errors.append(error)

    writer = threading.Thread(target=feed_audio, daemon=True)
    writer.start()
    try:
        for source, start, end, count in plans:
            for k in range(count):
                index = bisect_right(source['times'], start + Fraction(k, FPS)) - 1
                if index < 0:
                    raise ValueError('No source frame at requested time')
                proc.stdin.write(source['frames'][index].tobytes())
        proc.stdin.close()
        proc.stdin = None
        _, stderr = proc.communicate(timeout=60)
        writer.join(timeout=5)
        if timed_out.is_set():
            raise TimeoutError('Output encoding exceeded 90 seconds')
        if proc.returncode:
            raise RuntimeError(stderr.decode(errors='replace'))
        if writer.is_alive() or errors:
            raise RuntimeError('Audio pipe failed: ' + repr(errors))
    finally:
        timer.cancel()
        if proc.stdin is not None:
            proc.stdin.close()
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        writer.join(timeout=1)
    frames = sum(p[3] for p in plans)
    return {'frames': frames, 'audio_samples': frames * 2000, 'output': str(output)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(render(args.manifest, args.output)))


if __name__ == '__main__':
    main()

