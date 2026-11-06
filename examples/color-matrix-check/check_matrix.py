"""Original bounded SDR control; FFmpeg/ffprobe must already be installed. MIT-0."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);a=ap.parse_args()
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):raise SystemExit('Install FFmpeg and ffprobe separately with your operator permission.')
    # A new directory only. Existing inputs and results are never overwritten.
    a.output.mkdir(parents=True,exist_ok=False)
    colors=[(145,95,243),(255,0,0),(128,128,128)]
    source=b''.join(bytes(rgb)*(32*32) for rgb in colors)
    inp=a.output/'input.rgb';inp.write_bytes(source)
    def run(args):
        p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
        if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')[-2000:])
        return p.stdout
    version=run(['ffmpeg','-version']).decode().splitlines()[0]
    results={}
    for label,matrix in [('correct_matrix','bt709'),('mismatched_matrix','bt601')]:
        out=a.output/(label+'.mp4')
        # Both streams are tagged BT.709; the second deliberately converts with BT.601.
        yuv=a.output/(label+'.yuv')
        convert=['ffmpeg','-v','error','-nostdin','-n','-f','rawvideo','-pixel_format','rgb24','-video_size','32x32','-framerate','24','-i',str(inp),'-frames:v','3','-vf','scale=in_range=full:out_range=limited:out_color_matrix='+matrix+',format=yuv444p','-f','rawvideo',str(yuv)]
        run(convert)
        # Raw samples carry no tags. Deliberately interpret both buffers as BT.709.
        args=['ffmpeg','-v','error','-nostdin','-n','-f','rawvideo','-pixel_format','yuv444p','-video_size','32x32','-framerate','24','-color_range','tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-i',str(yuv),'-frames:v','3','-c:v','libx264','-crf','0','-color_range','tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709',str(out)]
        run(args)
        decoded=run(['ffmpeg','-v','error','-nostdin','-i',str(out),'-frames:v','3','-pix_fmt','rgb24','-f','rawvideo','-'])
        if len(decoded)!=len(source):raise RuntimeError('unexpected decoded length')
        probe=json.loads(run(['ffprobe','-v','error','-select_streams','v:0','-show_streams','-of','json',str(out)]))['streams'][0]
        observed=[list(decoded[i*32*32*3+(16*32+16)*3:i*32*32*3+(16*32+16)*3+3]) for i in range(3)]
        results[label]={'sample_rgb':observed,'max_absolute_rgb_error':max(abs(x-y) for x,y in zip(source,decoded)),'tags':{k:probe.get(k) for k in ['pix_fmt','color_range','color_space','color_transfer','color_primaries']},'conversion_command':convert,'encode_command':args}
    assert hashlib.sha256(inp.read_bytes()).digest()==hashlib.sha256(source).digest()
    # This is this fixture's acceptance threshold, not a general delivery specification.
    assert results['correct_matrix']['max_absolute_rgb_error']<=2,results
    assert results['mismatched_matrix']['max_absolute_rgb_error']>2,results
    result={'ffmpeg':version,'source_rgb':colors,'frames':3,'dimensions':[32,32],'results':results,'conclusion':'Matching colour tags alone do not prove the stored samples used the matching conversion.','limits':['Original synthetic SDR solid colours only.','No Kinetograph engine run or identification of its bug cause.','No HDR, player display, target editor, real footage or perceptual-quality validation.','RGB24 test does not establish higher-bit colour fidelity.']}
    (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
