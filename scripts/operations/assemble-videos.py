#!/usr/bin/env python3
"""Combine recorded native workflow, actual assistant draft and physician review."""
import pathlib,subprocess,json
root=pathlib.Path(__file__).resolve().parents[2];out=root/'docs/evidence/local-hospital/videos'
manifest=[]
for m in ['DX','CT','MR','US','MG']:
 files=[out/(m+'.webm'),out/(m+'-assistant.webm'),out/(m+'-physician-review.webm')]
 args=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y']
 for p in files:args+=['-i',str(p)]
 filters=[]
 for i in range(3):filters.append(f'[{i}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=10,setpts=PTS-STARTPTS[v{i}]')
 filters.append('[v0][v1][v2]concat=n=3:v=1:a=0[v]')
 target=out/(m+'-complete.mp4')
 subprocess.run(args+['-filter_complex',';'.join(filters),'-map','[v]','-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],check=True)
 duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(target)]))
 manifest.append({'modality':m,'file':str(target.relative_to(root)),'duration_seconds':duration,'chapters':['Registration, order, scanner emulator, real images, native technical report','Actual OpenMausBot Codex draft','Physician review, native save and reopen'],'edited':True,'raw_clips':[str(p.relative_to(root))for p in files]});print(m,'complete video',round(duration), 'seconds',flush=True)
(root/'docs/evidence/local-hospital/videos.json').write_text(json.dumps(manifest,indent=2))
