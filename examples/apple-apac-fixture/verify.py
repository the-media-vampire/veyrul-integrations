#!/usr/bin/env python3
"""Create and check genuine Apple APAC MOV fixtures on macOS; no network calls.
Run from a Veyrul integration checkout with the adjacent ffmpeg-safe-media folder.
Requires existing Apple command-line tools/afconvert plus FFmpeg and Python 3.9+.
All media is generated locally. Keep outputs and logs; each subprocess <=60s.
"""
import hashlib, json, platform, subprocess, sys
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if len(sys.argv)!=2 or platform.system()!='Darwin':
        raise SystemExit('macOS only: python3 verify.py NEW_OUTPUT_DIRECTORY')
    here=Path(__file__).resolve().parent
    root=Path(sys.argv[1]).resolve();root.mkdir(parents=True,exist_ok=False)
    calls=[]
    def run(label,args,expected=0):
        p=subprocess.run(args,capture_output=True,timeout=60)
        (root/(label+'.stdout')).write_bytes(p.stdout)
        (root/(label+'.stderr')).write_bytes(p.stderr)
        row={'label':label,'command':args,'exit':p.returncode}
        calls.append(row)
        if expected is not None and p.returncode!=expected:
            raise RuntimeError(f'{label} failed; retained diagnostics in {root}')
        return p
    def probe(label,path):
        p=run(label,['ffprobe','-v','warning','-show_streams','-show_format','-of','json',str(path)])
        return json.loads(p.stdout)
    def packets(label,path,selector):
        p=run(label,['ffprobe','-v','warning','-select_streams',selector,'-show_packets',
            '-show_data_hash','sha256','-show_entries','packet=data_hash','-of','json',str(path)])
        return [x['data_hash'] for x in json.loads(p.stdout)['packets']]
    saved=here.parent/'ffmpeg-safe-media/probe_apple_apac.py'
    # This existing script supplies genuinely encoded CAF and native reference PCM.
    if not saved.is_file():raise SystemExit('Use the integration checkout with ffmpeg-safe-media/probe_apple_apac.py')
    run('saved-probe',['python3',str(saved),str(root/'native-source')])
    native=root/'native-source';caf=native/'apple-apac.caf';source_pcm=native/'native-decoded-pcm.stdout'
    source_pcm_hash=sha(source_pcm);caf_hash=sha(caf);wav_hash=sha(native/'stereo-tone.wav')
    tools={}
    for name in ['native_mux','native_decode']:
        tools[name]=root/name
        run('compile-'+name,['clang','-fobjc-arc','-fblocks','-fno-modules',
            '-framework','Foundation','-framework','AVFoundation','-framework','CoreMedia',
            '-framework','AudioToolbox',str(here/(name+'.m')),'-o',str(tools[name])])
    video=root/'video-aac.mov'
    run('video-aac',['ffmpeg','-v','error','-nostdin','-n','-f','lavfi','-i',
        'testsrc2=size=128x72:rate=24:duration=2','-i',str(native/'stereo-tone.wav'),
        '-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','ultrafast','-threads','1',
        '-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','iec61966-2-1',
        '-colorspace','bt709','-color_range','tv','-c:a','aac','-b:a','128k',str(video)])
    video_hash=sha(video);caf_packets=packets('caf-packets',caf,'a:0')
    original_video_packets=packets('video-source-packets',video,'v:0')
    original_aac_packets=packets('aac-source-packets',video,'a:0')
    cases=[]
    for order in ['aac-first','apac-first']:
        mixed=root/(order+'.mov');copied=root/(order+'-copy-all.mov');selected=root/(order+'-aac-only.mov')
        args=[str(tools['native_mux']),str(video),str(caf),str(mixed)]
        if order=='apac-first':args.append('apac-first')
        run(order+'-mux',args)
        mixed_hash=sha(mixed);d=probe(order+'-probe',mixed)
        assert len(d['streams'])==3
        aac=next(s for s in d['streams'] if s.get('codec_name')=='aac')
        apac=next(s for s in d['streams'] if s.get('codec_tag_string')=='apac')
        assert aac['channels']==2 and apac['channels']==2
        assert (aac['index'],apac['index'])==((1,2) if order=='aac-first' else (2,1))
        mp=packets(order+'-apac-packets',mixed,str(apac['index']))
        assert mp==caf_packets and len(mp)==96
        native_pcm=root/(order+'-native.pcm')
        p=run(order+'-native-decode',[str(tools['native_decode']),str(mixed),str(native_pcm)])
        shape=json.loads(p.stdout);assert shape['frames']==96000 and shape['bytes']==384000
        assert sha(native_pcm)==source_pcm_hash
        # A successful copy exit and identical packets still need native decode.
        copy_result=run(order+'-copy-all',['ffmpeg','-v','error','-nostdin','-n','-i',str(mixed),
            '-map','0','-c','copy',str(copied)],expected=None)
        copy_info=probe(order+'-copy-probe',copied) if copied.exists() and copied.stat().st_size else {'streams':[]}
        copy_apac=next((s for s in copy_info['streams'] if s.get('codec_tag_string')=='apac'),None)
        cp=packets(order+'-copy-apac-packets',copied,str(copy_apac['index'])) if copy_apac else []
        copy_pcm=root/(order+'-copy-native.pcm')
        native_copy=run(order+'-copy-native-decode',[str(tools['native_decode']),str(copied),str(copy_pcm)],expected=None)
        copy_decodes_equal=native_copy.returncode==0 and copy_pcm.exists() and sha(copy_pcm)==source_pcm_hash
        # Read codec identity from the actual file, so swapped audio order is safe.
        run(order+'-aac-only',['ffmpeg','-v','error','-nostdin','-n','-i',str(mixed),
            '-map','0:v:0','-map','0:'+str(aac['index']),'-c','copy',str(selected)])
        sd=probe(order+'-aac-only-probe',selected)
        assert [s.get('codec_name') for s in sd['streams']]==['h264','aac']
        assert packets(order+'-selected-video-packets',selected,'v:0')==original_video_packets
        assert packets(order+'-selected-aac-packets',selected,'a:0')==original_aac_packets
        run(order+'-selected-decode',['ffmpeg','-v','error','-nostdin','-i',str(selected),
            '-map','0:v:0','-map','0:a:0','-f','null','-'])
        assert sha(mixed)==mixed_hash
        cases.append({'order':order,'fixture_sha256':mixed_hash,'fixture_bytes':mixed.stat().st_size,
            'streams':[{'index':s['index'],'codec':s.get('codec_name'),'tag':s.get('codec_tag_string'),
                'track_id':s.get('id'),'duration':s.get('duration')} for s in d['streams']],
            'genuine_apac_packets_preserved':len(mp),'native_apac_pcm_equals_caf':True,'native_pcm_frames':96000,
            'ffmpeg_copy_all_exit':copy_result.returncode,'copied_stream_count':len(copy_info['streams']),
            'copied_apac_packet_payloads_equal':cp==caf_packets,'copied_native_decode_exit':native_copy.returncode,
            'copied_native_pcm_equals_source':copy_decodes_equal,'copied_apac_duration':copy_apac.get('duration') if copy_apac else None,
            'aac_selected_from_absolute_index':aac['index'],'aac_only_video_packets_equal':len(original_video_packets),
            'aac_only_audio_packets_equal':len(original_aac_packets),'aac_only_fully_decoded':True,'mixed_original_unchanged':True})
    assert sha(caf)==caf_hash and sha(video)==video_hash and sha(native/'stereo-tone.wav')==wav_hash
    # Existing destination guard is tested with an expendable generated original.
    prior=sha(root/'aac-first.mov')
    refused=run('existing-output-refused',[str(tools['native_mux']),str(video),str(caf),str(root/'aac-first.mov')],expected=None)
    assert refused.returncode!=0 and sha(root/'aac-first.mov')==prior
    result={'status':'passed_in_stated_scope','platform':platform.platform(),'saved_probe_sha256':sha(saved),
        'source_caf_sha256':caf_hash,'source_native_pcm_sha256':source_pcm_hash,'cases':cases,
        'originals_unchanged':True,'existing_output_guard_passed':True,'model_calls':0,'network_calls':0,
        'scope':'Purpose-generated 128x72/24fps SDR video and two stereo audio tracks with real Apple APAC payloads. Not an iPhone recording, FOA/spatial metadata, head-tracked playback, browser pipeline or fidelity-policy approval.',
        'calls':calls}
    (root/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='calls'},indent=2))


if __name__=='__main__':main()
