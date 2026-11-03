from pathlib import Path
import json, subprocess, hashlib, wave, math, struct
import argparse,os,shutil
p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args()
I=Path(args.output).resolve();I.mkdir(exist_ok=False);P=I
FF=os.environ.get('FFMPEG') or shutil.which('ffmpeg');FP=os.environ.get('FFPROBE') or shutil.which('ffprobe')
if not FF or not FP:raise RuntimeError('Set FFMPEG and FFPROBE or put them on PATH')

def cmd(a,body=None):
 r=subprocess.run(a,input=body,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=40)
 if r.returncode: raise RuntimeError(r.stderr.decode()[-2000:])
 return r.stdout
fixtures={}
for name,rate,n,origin,offset,ar,ch in [('A',30,60,5,.35,48000,2),('B',24,72,2.2,-.2,44100,1),('C',25,75,.7,None,None,None)]:
 raw=b''.join(bytes(((i*29+17)%190+30,(i*47+31)%190+30,(i*71+53)%190+30))*(128*72) for i in range(n))
 args=[FF,'-hide_banner','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','128x72','-framerate',str(rate),'-i','pipe:0']
 if ar:
  wav=I/(name+' tone.wav')
  with wave.open(str(wav),'wb') as f:
   f.setnchannels(ch); f.setsampwidth(2); f.setframerate(ar)
   vals=bytearray()
   for j in range(round(3.2*ar)):
    t=j/ar; gate=0.0 if .7 <= t < .87 or 1.7 <= t < 1.85 else 1.0
    for c in range(ch):
     v=gate*(.12*math.sin(2*math.pi*(271+c*160)*t)+.05*math.sin(2*math.pi*(503+c*210)*t))
     vals.extend(struct.pack('<h',round(v*32767)))
   f.writeframes(vals)
  args+=['-i',str(wav)]
 vpts=f'(if(lt(N,30),N/30,1+(N-30)/15)+{origin})/TB' if name=='A' else f'(N/{rate}+{origin})/TB'
 filters=f'[0:v]settb=1/1000,setpts=\'{vpts}\'[v]'
 if ar: filters+=f';[1:a]asetpts=PTS+({origin+offset})/TB[a]'
 args+=['-filter_complex',filters,'-map','[v]']
 if ar: args+=['-map','[a]','-c:a','pcm_s16le']
 args+=['-c:v','ffv1','-pix_fmt','bgr0','-enc_time_base:v','1/1000','-fps_mode','passthrough','-avoid_negative_ts','disabled',str(I/(name+' source.mkv'))]
 cmd(args,raw)
 info=json.loads(cmd([FP,'-v','error','-show_streams','-show_format','-of','json',str(I/(name+' source.mkv'))]))
 frames=json.loads(cmd([FP,'-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(I/(name+' source.mkv'))]))['frames']
 fixtures[name]={'file':name+' source.mkv','sha256':hashlib.sha256((I/(name+' source.mkv')).read_bytes()).hexdigest(),'bytes':(I/(name+' source.mkv')).stat().st_size,'video_frames':len(frames),'first_pts':frames[0]['best_effort_timestamp_time'],'last_pts':frames[-1]['best_effort_timestamp_time'],'streams':[{k:s.get(k) for k in ['codec_type','codec_name','width','height','sample_rate','channels','start_time','avg_frame_rate','time_base']} for s in info['streams']]}
base={'sources':{n:n+' source.mkv' for n in fixtures},'fps':24,'width':128,'height':72}
for name,cuts in {
 'TRAIN': [('A',.10,1.10),('B',.50,1.25),('C',.20,.70),('A',1.40,2.65)],
 'FINAL': [('B',0,.625),('A',.20,.95),('A',1.60,2.35),('C',.32,.82),('B',.75,1.25),('A',.05,.175)],
 'HOLDOUT1':[('A',.4,.5),('C',.2,.3),('B',.03,.53),('A',.92,1.67),('A',.412,.413)],
 'HOLDOUT2':[('B',1.1,1.85),('A',2.05,2.8),('B',0,.25),('A',0,.25),('C',1.1,1.35)]
}.items():
 job={**base,'clips':[{'source':n,'in_s':a,'out_s':b} for n,a,b in cuts]}
 (I/(name+'.json')).write_text(json.dumps(job,indent=2)+'\n')
(P/'FIXTURES.json').write_text(json.dumps({'generated_calibration_media':True,'customer_media':False,'ffmpeg_version':'8.1','fixtures':fixtures},indent=2)+'\n')
print(json.dumps(fixtures,indent=2))
