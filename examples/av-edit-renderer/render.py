#!/usr/bin/env python3
"""Guarded entry point; never replace an existing output, preserve partial attempts."""
import argparse,json,os,shutil,signal,subprocess,sys,tempfile
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',required=True);p.add_argument('--output',required=True);args=p.parse_args()
 manifest=Path(args.manifest).resolve();target=Path(args.output).absolute()
 if target.exists() or target.is_symlink():raise SystemExit('Output already exists; choose a new filename.')
 if not target.parent.is_dir():raise SystemExit('Create the output directory first.')
 env=os.environ.copy()
 for key,name in [('FFMPEG','ffmpeg'),('FFPROBE','ffprobe')]:
  env[key]=env.get(key) or shutil.which(name) or ''
  if not env[key]:raise SystemExit('Put '+name+' on PATH or set '+key)
 # This file is newly and exclusively allocated. Only it is passed to the
 # reference engine's overwrite-enabled encoder. It is retained on failure.
 fd,path=tempfile.mkstemp(prefix='.veyrul-attempt-',suffix='.mkv',dir=target.parent);os.close(fd)
 stage=Path(path)
 command=[sys.executable,str(Path(__file__).with_name('render_reference.py')),'--manifest',str(manifest),'--output',str(stage)]
 child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,start_new_session=True)
 try:out,err=child.communicate(timeout=110)
 except subprocess.TimeoutExpired:
  os.killpg(child.pid,signal.SIGKILL);child.communicate();raise SystemExit('Renderer timed out; partial attempt retained at '+str(stage))
 if child.returncode:sys.stderr.buffer.write(err);raise SystemExit('Renderer failed; attempt retained at '+str(stage))
 try:os.link(stage,target)
 except FileExistsError:raise SystemExit('Output appeared during rendering; preserved it. New attempt retained at '+str(stage))
 # Retaining this hard link keeps the attempt with no duplicate payload blocks.
 print(json.dumps({'output':str(target),'retained_attempt':str(stage),'engine_result':json.loads(out)}))
if __name__=='__main__':main()
