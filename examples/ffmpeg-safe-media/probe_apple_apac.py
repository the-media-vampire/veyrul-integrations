#!/usr/bin/env python3
"""Probe actual Apple-encoded synthetic CAF audio on macOS; never a fake MOV tag.
No download, model call or third-party media. Requires afconvert, ffmpeg, ffprobe.
This measures commands on this machine; failure is evidence, not a universal claim.
"""
import hashlib
import json
import math
import platform
import struct
import subprocess
import sys
import wave
from pathlib import Path


def main():
    if len(sys.argv) != 2 or platform.system() != 'Darwin':
        raise SystemExit('macOS only: python3 probe_apple_apac.py NEW_OUTPUT_DIRECTORY')
    root = Path(sys.argv[1]).resolve()
    root.mkdir(parents=True, exist_ok=False)
    source = root / 'stereo-tone.wav'
    with wave.open(str(source), 'wb') as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(48000)
        out.writeframes(b''.join(struct.pack('<hh', int(3500*math.sin(2*math.pi*440*i/48000)),
            int(3500*math.sin(2*math.pi*660*i/48000))) for i in range(96000)))
    original = hashlib.sha256(source.read_bytes()).hexdigest()
    calls = []
    def run(label, args):
        p = subprocess.run(args, capture_output=True, timeout=30)
        (root / (label + '.stdout')).write_bytes(p.stdout)
        (root / (label + '.stderr')).write_bytes(p.stderr)
        calls.append({'label': label, 'command': args, 'exit': p.returncode,
                      'stderr': p.stderr.decode(errors='replace')[:5000]})
        return p
    run('macos', ['sw_vers'])
    run('ffmpeg-version', ['ffmpeg', '-version'])
    run('codec-list', ['ffmpeg', '-hide_banner', '-codecs'])
    encoded = root / 'apple-apac.caf'
    encode = run('native-encode-caf', ['afconvert', '-f', 'caff', '-d', 'apac',
        '-b', '128000', '-l', 'Stereo', str(source), str(encoded)])
    if encode.returncode != 0:
        (root / 'RESULT.json').write_text(json.dumps({'status':'native_encoding_unavailable',
            'calls':calls}, indent=2) + '\n')
        raise SystemExit('No Apple fixture available; no FFmpeg capability conclusion.')
    # Inspect the actual CAF Audio Description chunk: mFormatID must be apac.
    raw = encoded.read_bytes()
    assert raw[:4] == b'caff'
    pos = 8; fourcc = None
    while pos + 12 <= len(raw):
        kind, size = struct.unpack('>4sq', raw[pos:pos+12]); pos += 12
        if kind == b'desc': fourcc = raw[pos+8:pos+12].decode('ascii')
        if size < 0: break
        pos += size
    assert fourcc == 'apac', 'encoder_did_not_write_apac'
    decoded = root / 'native-decoded.wav'
    native = run('native-decode', ['afconvert', '-f', 'WAVE', '-d', 'LEI16',
                                  str(encoded), str(decoded)])
    assert native.returncode == 0
    # afconvert writes extensible WAV, which older Python wave modules reject.
    native_info = run('native-decoded-probe', ['ffprobe', '-v', 'error',
        '-show_streams', '-of', 'json', str(decoded)])
    assert native_info.returncode == 0
    stream = json.loads(native_info.stdout)['streams'][0]
    native_shape = {'channels':stream['channels'], 'sample_rate':int(stream['sample_rate']),
                    'frames':stream['duration_ts']}
    assert native_shape == {'channels':2, 'sample_rate':48000, 'frames':96000}
    native_pcm = run('native-decoded-pcm', ['ffmpeg', '-v', 'error', '-nostdin',
        '-i', str(decoded), '-map', '0:a:0', '-c:a', 'pcm_s16le', '-f', 's16le', '-'])
    assert native_pcm.returncode == 0 and len(native_pcm.stdout) == 96000*2*2
    probe = run('ffprobe-streams', ['ffprobe', '-v', 'warning', '-show_streams',
                                  '-show_format', '-of', 'json', str(encoded)])
    packet = run('ffprobe-packets', ['ffprobe', '-v', 'warning', '-select_streams', 'a:0',
        '-show_packets', '-show_data_hash', 'sha256', '-show_entries', 'packet=data_hash',
        '-of', 'json', str(encoded)])
    decode = run('ffmpeg-decode', ['ffmpeg', '-v', 'error', '-nostdin', '-i', str(encoded),
                                 '-map', '0:a:0', '-f', 'null', '-'])
    copy_caf = run('ffmpeg-copy-caf', ['ffmpeg', '-v', 'error', '-nostdin', '-n',
        '-i', str(encoded), '-map', '0:a:0', '-c', 'copy', str(root/'copied.caf')])
    copy_mov = run('ffmpeg-copy-mov', ['ffmpeg', '-v', 'error', '-nostdin', '-n',
        '-i', str(encoded), '-map', '0:a:0', '-c', 'copy', str(root/'copied.mov')])
    mov_probe = run('copied-mov-probe', ['ffprobe', '-v', 'warning', '-show_streams',
        '-show_format', '-of', 'json', str(root/'copied.mov')])
    mov_packets = run('copied-mov-packets', ['ffprobe', '-v', 'warning',
        '-select_streams', 'a:0', '-show_packets', '-show_data_hash', 'sha256',
        '-show_entries', 'packet=data_hash', '-of', 'json', str(root/'copied.mov')])
    mov_native = run('copied-mov-native-decode', ['afconvert', '-f', 'WAVE', '-d', 'LEI16',
        str(root/'copied.mov'), str(root/'mov-native-decoded.wav')])
    packet_list = json.loads(packet.stdout).get('packets', []) if packet.returncode==0 else []
    mov_packet_list = json.loads(mov_packets.stdout).get('packets', []) if mov_packets.returncode==0 else []
    mov_info = json.loads(mov_probe.stdout).get('streams', []) if mov_probe.returncode==0 else []
    transcode = run('ffmpeg-transcode-aac', ['ffmpeg', '-v', 'error', '-nostdin', '-n',
        '-i', str(encoded), '-map', '0:a:0', '-c:a', 'aac', str(root/'converted.m4a')])
    fallback = root/'native-pcm-to-aac.m4a'
    fallback_encode = run('native-pcm-to-aac', ['ffmpeg', '-v', 'error', '-nostdin', '-n',
        '-i', str(decoded), '-map', '0:a:0', '-c:a', 'aac', '-b:a', '128k', str(fallback)])
    assert fallback_encode.returncode == 0
    fallback_probe = run('native-pcm-to-aac-probe', ['ffprobe', '-v', 'error',
        '-show_streams', '-of', 'json', str(fallback)])
    fallback_stream = json.loads(fallback_probe.stdout)['streams'][0]
    assert fallback_stream['codec_name']=='aac' and fallback_stream['channels']==2
    assert abs(float(fallback_stream['duration'])-2.0)<0.05
    fallback_decode = run('native-pcm-to-aac-decode', ['ffmpeg', '-v', 'error', '-nostdin',
        '-i', str(fallback), '-map', '0:a:0', '-f', 'null', '-'])
    assert fallback_decode.returncode == 0
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original
    assert hashlib.sha256(encoded.read_bytes()).digest() == hashlib.sha256(raw).digest()
    result = {'status':'observations_recorded', 'platform':platform.platform(),
        'input_sha256':original, 'apac_sha256':hashlib.sha256(raw).hexdigest(),
        'apac_bytes':len(raw), 'caf_format_id':fourcc, 'native_decoded_shape':native_shape,
        'source_and_encoded_originals_unchanged':True,
        'ffprobe_exit':probe.returncode, 'packet_probe_exit':packet.returncode,
        'ffprobe_streams':json.loads(probe.stdout).get('streams', []) if probe.returncode==0 else [],
        'packets_observed':len(packet_list), 'copied_mov_streams':mov_info,
        'copied_mov_packets':len(mov_packet_list),
        'copied_mov_packet_payloads_equal':bool(packet_list) and packet_list==mov_packet_list,
        'copied_mov_native_decode_exit':mov_native.returncode,
        'copied_mov_bytes':(root/'copied.mov').stat().st_size if (root/'copied.mov').exists() else 0,
        'ffmpeg_decode_exit':decode.returncode, 'ffmpeg_copy_caf_exit':copy_caf.returncode,
        'ffmpeg_copy_mov_exit':copy_mov.returncode, 'ffmpeg_transcode_aac_exit':transcode.returncode,
        'native_pcm_then_aac_decode_passed':True,
        'native_pcm_then_aac_duration':fallback_stream['duration'],
        'scope':'Apple afconvert stereo CAF fixture, not an iPhone MOV or spatial playback/metadata validation.',
        'calls':calls}
    (root / 'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='calls'},indent=2))


if __name__ == '__main__':
    main()
