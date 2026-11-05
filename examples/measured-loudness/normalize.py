"""Measured FFmpeg loudness normalization to mono/stereo PCM16 WAV.

Original Veyrul utility, MIT. No upload, package installation or model call.
Measurement uses the same resample/channel preparation in both passes. A final
readback checks the encoded file; it does not substitute for listening.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def measured_values(stderr):
    start, end = stderr.rfind('{'), stderr.rfind('}')
    if start < 0 or end <= start:
        raise ValueError('No loudnorm measurement in FFmpeg output')
    values = json.loads(stderr[start:end + 1])
    for field in ('input_i', 'input_tp', 'input_lra', 'input_thresh', 'target_offset'):
        if field not in values or not math.isfinite(float(values[field])):
            raise ValueError('Non-finite or missing loudness measurement: ' + field)
    return values


def normalize(source, destination, *, receipt, ffmpeg='ffmpeg', integrated=-16.0,
              true_peak=-1.5, lra=11.0, sample_rate=48000, channels=1, stream=0):
    source, destination, receipt = map(lambda p: Path(p).resolve(), (source, destination, receipt))
    if not source.is_file() or destination.suffix.lower() != '.wav':
        raise ValueError('Use an existing input and a new .wav output')
    if destination.exists() or receipt.exists() or len({source, destination, receipt}) != 3:
        raise ValueError('Input, output and new receipt must be distinct; no overwrite')
    if not all(math.isfinite(v) for v in (integrated, true_peak, lra)):
        raise ValueError('Finite targets required')
    if not (-70 <= integrated <= -5 and -9 <= true_peak <= 0 and 1 <= lra <= 50):
        raise ValueError('Target outside loudnorm option ranges')
    if channels not in (1, 2) or sample_rate not in (44100, 48000, 96000) or not isinstance(stream, int) or stream < 0:
        raise ValueError('Unsupported output format or audio stream index')
    input_sha = digest(source)
    target = f'loudnorm=I={integrated}:TP={true_peak}:LRA={lra}'
    prepare = f'aresample={sample_rate},aformat=channel_layouts={"mono" if channels == 1 else "stereo"},'
    commands = []

    def run(argv):
        commands.append(argv)
        return subprocess.run(argv, capture_output=True, text=True, check=True, timeout=600)

    common = [ffmpeg, '-hide_banner', '-nostdin', '-n', '-i', str(source), '-map', f'0:a:{stream}', '-vn']
    first = run(common + ['-af', prepare + target + ':print_format=json', '-f', 'null', '-'])
    measured = measured_values(first.stderr)
    second_filter = prepare + target + ''.join(':' + dst + '=' + str(measured[src]) for dst, src in (
        ('measured_I', 'input_i'), ('measured_TP', 'input_tp'),
        ('measured_LRA', 'input_lra'), ('measured_thresh', 'input_thresh'), ('offset', 'target_offset')))
    rendered = run(common + ['-af', second_filter + ':linear=true:print_format=json',
                            '-ar', str(sample_rate), '-ac', str(channels), '-c:a', 'pcm_s16le', str(destination)])
    actual_mode = json.loads(rendered.stderr[rendered.stderr.rfind('{'):rendered.stderr.rfind('}') + 1]).get('normalization_type')
    # Measure the encoded output directly, without applying the preparation twice.
    final = run([ffmpeg, '-hide_banner', '-nostdin', '-i', str(destination), '-map', '0:a:0', '-vn',
                 '-af', target + ':print_format=json', '-f', 'null', '-'])
    output = measured_values(final.stderr)
    checks = {'input_preserved': digest(source) == input_sha,
              'loudness_within_0_2_LU': abs(float(output['input_i']) - integrated) <= 0.2,
              'true_peak_within_0_1_dB_of_ceiling': float(output['input_tp']) <= true_peak + 0.1}
    report = {'input_sha256': input_sha, 'output_sha256': digest(destination),
              'ffmpeg_version': run([ffmpeg, '-version']).stdout.splitlines()[0],
              'target': {'integrated_LUFS': integrated, 'true_peak_dBTP': true_peak, 'LRA': lra},
              'format': {'sample_rate': sample_rate, 'channels': channels, 'codec': 'pcm_s16le'},
              'pass1': measured, 'normalization_type': actual_mode, 'encoded_readback': output,
              'checks': checks, 'accepted_numerically': all(checks.values()), 'commands': commands,
              'limits': 'Numerical checks only. Listen to the result; LRA and linear mode are not guaranteed. FFmpeg may fall back to dynamic mode. No delivery-platform certification.'}
    with receipt.open('x') as stream_out:
        json.dump(report, stream_out, indent=2)
        stream_out.write('\n')
    if not all(checks.values()):
        raise ValueError('Encoded output missed a check; output and receipt retained for inspection')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input'); p.add_argument('output'); p.add_argument('--receipt', required=True)
    p.add_argument('--ffmpeg', default='ffmpeg'); p.add_argument('--integrated', type=float, default=-16)
    p.add_argument('--true-peak', type=float, default=-1.5); p.add_argument('--lra', type=float, default=11)
    p.add_argument('--sample-rate', type=int, default=48000); p.add_argument('--channels', type=int, default=1)
    p.add_argument('--stream', type=int, default=0)
    a = p.parse_args()
    result = normalize(a.input, a.output, receipt=a.receipt, ffmpeg=a.ffmpeg, integrated=a.integrated,
                       true_peak=a.true_peak, lra=a.lra, sample_rate=a.sample_rate, channels=a.channels, stream=a.stream)
    print(json.dumps({'accepted_numerically': result['accepted_numerically'], 'normalization_type': result['normalization_type']}))


if __name__ == '__main__':
    main()
