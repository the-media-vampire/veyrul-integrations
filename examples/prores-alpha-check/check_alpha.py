#!/usr/bin/env python3
"""Verify a small original RGBA fixture through FFmpeg ProRes 4444. MIT-0 license.
No source footage, downloads, model calls or installations. Retain all outputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def check(folder):
    folder=Path(folder)
    folder.mkdir(parents=False,exist_ok=False)
    commands=[]
    def run(args):
        result=subprocess.run(args,capture_output=True,check=True,timeout=60)
        commands.append(args)
        return result.stdout
    source=folder/'input.rgba'; output=folder/'output.mov'
    raw=bytes(value for frame in range(3) for y in range(32) for x in range(32)
              for value in ((x*7+frame*13)%256,(y*7)%256,93,[0,64,192,255][x//8]))
    source.write_bytes(raw)
    run(['ffmpeg','-hide_banner','-nostdin','-n','-f','rawvideo','-pixel_format','rgba',
         '-video_size','32x32','-framerate','24','-i',str(source),'-frames:v','3',
         '-c:v','prores_ks','-profile:v','4','-pix_fmt','yuva444p10le','-alpha_bits','16',str(output)])
    decoded=run(['ffmpeg','-v','error','-i',str(output),'-pix_fmt','rgba','-f','rawvideo','pipe:1'])
    if len(decoded)!=len(raw):raise ValueError('decoded_frame_length_mismatch')
    errors=[abs(a-b) for a,b in zip(raw[3::4],decoded[3::4])]
    probe=json.loads(run(['ffprobe','-v','error','-show_streams','-of','json',str(output)]))['streams'][0]
    report={'ffmpeg':run(['ffmpeg','-version']).decode().splitlines()[0],
            'source_sha256':hashlib.sha256(raw).hexdigest(),
            'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'source_preserved':source.read_bytes()==raw,'frames':3,'size':[32,32],
            'max_alpha_8bit_error':max(errors),'decoded_alpha_levels':sorted(set(decoded[3::4])),
            'stream':{k:probe.get(k) for k in ['codec_name','profile','pix_fmt','nb_frames','r_frame_rate']},
            'accepted':max(errors)<=1 and source.read_bytes()==raw,
            'commands':commands,
            'limits':'Synthetic numerical alpha check only. RGB is lossy. No ComfyUI graph, target editor, premultiplication handling, HDR or archival-master compatibility test.'}
    with (folder/'receipt.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n')
    if not report['accepted']:raise ValueError('alpha_check_failed_outputs_retained')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('new_output_directory',type=Path)
    args=parser.parse_args()
    print(json.dumps(check(args.new_output_directory),indent=2))
