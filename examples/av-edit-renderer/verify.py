"""Main-only frozen evaluator: decode actual output and compare media observations."""
from pathlib import Path
from fractions import Fraction
import bisect, json, math, os, signal, subprocess, sys, time, wave
from decimal import Decimal
import numpy as np
HERE=Path(__file__).resolve().parent
import shutil
FF=os.environ.get('FFMPEG') or shutil.which('ffmpeg')
FP=os.environ.get('FFPROBE') or shutil.which('ffprobe')
if not FF or not FP:raise RuntimeError('Set FFMPEG and FFPROBE or put them on PATH')

def run(args,body=None,timeout=45):
 r=subprocess.run(args,input=body,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
 if r.returncode: raise RuntimeError(r.stderr.decode(errors='replace')[-1500:])
 return r.stdout

def probe(file):return json.loads(run([FP,'-v','error','-show_streams','-of','json',str(file)]))['streams']
def times(file,kind):
 return [float(f['best_effort_timestamp_time']) for f in json.loads(run([FP,'-v','error','-select_streams',kind,'-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(file)]))['frames']]
def rational_times(file,kind):
 stream=next(s for s in probe(file) if s['codec_type']==('video' if kind.startswith('v') else 'audio'))
 tb=Fraction(stream['time_base'])
 frames=json.loads(run([FP,'-v','error','-select_streams',kind,'-show_frames','-show_entries','frame=best_effort_timestamp','-of','json',str(file)]))['frames']
 return [int(f['best_effort_timestamp'])*tb for f in frames]

def video(file):
 b=run([FF,'-v','error','-i',str(file),'-map','0:v:0','-fps_mode','passthrough','-pix_fmt','rgb24','-f','rawvideo','pipe:1'])
 return np.frombuffer(b,dtype=np.uint8).reshape(-1,72,128,3)
def audio(file,channels,rate=48000):
 b=run([FF,'-v','error','-i',str(file),'-map','0:a:0','-ar',str(rate),'-f','f32le','pipe:1'])
 return np.frombuffer(b,dtype='<f4').reshape(-1,channels)
def ceilfrac(x):return (x.numerator+x.denominator-1)//x.denominator

def expected(job,ignore_offsets=False,next_frame=False):
 cache={}; vs=[]; aa=[]; silence=[]; offset=0; clips=[]
 for c in job['clips']:
  name=c['source']; path=Path(job['_base'])/job['sources'][name]
  if name not in cache:
   streams=probe(path); vp=rational_times(path,'v:0'); origin=vp[0]
   ap=[s for s in streams if s['codec_type']=='audio']
   aud=audio(path,int(ap[0]['channels'])) if ap else np.zeros((0,2),dtype=np.float32)
   if ap and int(ap[0]['channels'])==1: aud=np.repeat(aud,2,axis=1)
   cache[name]=(video(path),[t-origin for t in vp],aud,(rational_times(path,'a:0')[0]-origin) if ap else 0)
  v,t,a,astart=cache[name]
  if ignore_offsets:astart=0
  start=Fraction(str(c['in_s'])); end=Fraction(str(c['out_s'])); n=ceilfrac((end-start)*24)
  selected=[max(0,bisect.bisect_right(t,start+Fraction(k,24))-1) for k in range(n)]
  if next_frame:selected=[min(len(v)-1,k+1) for k in selected]
  vs.extend(v[selected]); length=n*2000
  pos=np.arange(length)/48000+float(start)
  sample_indices=np.rint((pos-float(astart))*48000).astype(np.int64)
  valid=(sample_indices>=0)&(sample_indices<len(a))&(pos<float(end)-1e-10)
  out=np.zeros((length,2),dtype=np.float32); out[valid]=a[sample_indices[valid]]
  aa.append(out); silence.extend((~valid).tolist()); clips.append({'source':name,'start_sample':offset,'samples':length,'frames':n})
  offset+=length
 return np.array(vs),np.concatenate(aa),np.array(silence),clips

def score(path,job):
 ev,ea,silence,clips=expected(job); groups={};detail={}
 try:
  streams=probe(path); v=next(s for s in streams if s['codec_type']=='video'); a=next(s for s in streams if s['codec_type']=='audio')
  fmt=json.loads(run([FP,'-v','error','-show_entries','format=format_name','-of','json',str(path)]))['format']['format_name']
  groups['structure']='matroska' in fmt and v['codec_name']=='ffv1' and v['width']==128 and v['height']==72 and a['codec_name']=='pcm_s16le'
  actual=video(path); vp=np.array(times(path,'v:0'))
  match=[bool(np.max(np.abs(x.astype(int)-y.astype(int)))<=1) for x,y in zip(actual,ev)]
  groups['frame_identity']=len(actual)==len(ev) and all(match)
  groups['video_timestamps']=len(vp)==len(ev) and float(np.max(np.abs(vp-np.arange(len(ev))/24)))<=.0011 and abs(vp[0])<=1e-7 and v.get('avg_frame_rate')=='24/1'
  detail['frames']={'expected':len(ev),'actual':len(actual),'correct':sum(match),'missing':max(0,len(ev)-len(actual)),'extra':max(0,len(actual)-len(ev)),'wrong_indices':[i for i,ok in enumerate(match) if not ok][:25]}
  channels=int(a['channels']); actual_a=audio(path,channels); ap=np.array(times(path,'a:0'))
  aframes=json.loads(run([FP,'-v','error','-select_streams','a:0','-show_frames','-show_entries','frame=best_effort_timestamp_time,nb_samples','-of','json',str(path)]))['frames']
  count=0; audio_pts_errors=[]
  for af in aframes:
   audio_pts_errors.append(abs(float(af['best_effort_timestamp_time'])-count/48000));count+=int(af['nb_samples'])
  audio_continuous=bool(audio_pts_errors) and max(audio_pts_errors)<=.0011
  detail['max_audio_pts_error_s']=max(audio_pts_errors) if audio_pts_errors else None
  groups['audio_format_length']=channels==2 and int(a['sample_rate'])==48000 and len(actual_a)==len(ea) and len(ap)>0 and abs(ap[0])<=1e-7 and audio_continuous
  tests=[]
  # Mask all zero/nonzero signal transitions, including source tone gates,
  # under the same48-sample tolerance used for required silence.
  zero=np.max(np.abs(ea),axis=1)<1e-7
  safe=np.ones(len(ea),dtype=bool)
  for edge in np.flatnonzero(zero[1:]!=zero[:-1])+1:safe[max(0,edge-48):min(len(ea),edge+49)]=False
  if channels==2 and len(actual_a)==len(ea):
   # Direct sample comparison on non-boundary windows, allowing +/-one sample
   # for ordinary input resampling/timestamp quantization. No global realignment.
   for c in clips:
    lo=c['start_sample']; hi=lo+c['samples']
    for start in range(lo+240,hi-240,2400):
     stop=min(start+960,hi-240)
     if stop-start<240:continue
     mask=safe[start:stop]
     if not mask.any():continue
     best=min(float(np.sqrt(np.mean((actual_a[start+d:stop+d][mask]-ea[start:stop][mask])**2))) for d in (-1,0,1))
     tests.append({'start':start,'samples':stop-start,'rmse':best,'pass':best<=.003})
   groups['audio_signal']=bool(tests) and all(t['pass'] for t in tests)
   # Erode silent spans by48samples so resampler boundary ringing is not failure.
   robust=silence.copy()
   for shift in range(1,49):robust[shift:]&=silence[:-shift];robust[:-shift]&=silence[shift:]
   detail['required_silent_samples']=int(robust.sum())
   peak=float(np.max(np.abs(actual_a[robust]))) if robust.any() else 0
   groups['required_silence']=peak<=.001
   detail['silence_peak']=peak
  else:groups['audio_signal']=False;groups['required_silence']=False
  detail['audio']={'expected_samples':len(ea),'actual_samples':len(actual_a),'windows':tests,'passed_windows':sum(t['pass'] for t in tests),'channels':channels}
 except Exception as e:
  detail['error']=str(e)
 for k in ['structure','frame_identity','video_timestamps','audio_format_length','audio_signal','required_silence']:groups.setdefault(k,False)
 groups={k:bool(v) for k,v in groups.items()}
 return {'groups':groups,'passed':sum(groups.values()),'total':6,'accepted':all(groups.values()),'detail':detail}

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--output',required=True);p.add_argument('--report')
 args=p.parse_args();path=Path(args.manifest).resolve();job=json.loads(path.read_text(),parse_float=Decimal);job['_base']=str(path.parent)
 result=score(Path(args.output),job)
 if args.report:
  with open(args.report,'x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({'accepted':result['accepted'],'passed':result['passed'],'total':result['total']}))
 sys.exit(0 if result['accepted'] else 1)
