"""Evidence completeness and image contact sheets; never judges artistic correctness."""
import base64
import io
import json
import math
from pathlib import Path
import project

def finite(value):
    if isinstance(value,float): return math.isfinite(value)
    if isinstance(value,dict): return all(finite(v) for v in value.values())
    if isinstance(value,list): return all(finite(v) for v in value)
    return True

def validate_data(data):
    errors=[]
    if data.get('schema')!=2: errors.append('Use schema 2 collector; legacy captures lack coverage/fingerprint')
    if not data.get('pack_fingerprint'): errors.append('Missing pack fingerprint')
    expected=data.get('expected',[]);samples=data.get('samples',[]);checks=data.get('checks',[])
    keys=[s.get('key') for s in samples]
    if not expected or len(expected)!=len(set(expected)): errors.append('Missing or duplicate planned sample keys')
    if len(keys)!=len(set(keys)) or set(keys)!=set(expected): errors.append('Missing/duplicate/unexpected sample coverage')
    if not checks or any(c.get('accepted') is not True for c in checks): errors.append('Missing or rejected actions/interactions')
    if set(s.get('facing') for s in samples)!={-1,1}: errors.append('Both directions required')
    if not finite({k:v for k,v in data.items() if k!='samples'}) or any(not finite({k:v for k,v in s.items() if k!='png'}) for s in samples): errors.append('Nonfinite values')
    if data.get('page_errors') or data.get('request_errors'): errors.append('Browser/page/resource errors')
    if not any(s.get('phase')=='recovery' for s in samples): errors.append('Missing recovery evidence')
    if not any(s.get('phase')=='held' and s.get('layout',{}).get('mode')=='drag' for s in samples): errors.append('Missing actual dragged state')
    return errors

def build(input_path, out):
    from PIL import Image,ImageDraw
    data=project.read(input_path);errors=validate_data(data);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    samples=data.get('samples',[]);sheets=[];frames=[];blank=[]
    for i,s in enumerate(samples):
        if i%12==0:
            sheet=Image.new('RGB',(1200,4*310),'#202124');sheets.append(sheet)
        try:
            raw=base64.b64decode(s['png'].split(',',1)[1],validate=True)
            image=Image.open(io.BytesIO(raw)).convert('RGBA')
            if image.size!=tuple(data['viewport']): raise ValueError('Frame size does not match viewport')
            bounds=image.getbbox()
            if not bounds: blank.append(i);continue
            if (bounds[2]-bounds[0])*(bounds[3]-bounds[1])<64: blank.append(i);continue
            # Preserve whole viewport files; trim only the contact-sheet thumbnails.
            for j,(label,color) in enumerate([('light','#e9e4f1'),('dark','#202124')]):
                bg=Image.new('RGBA',image.size,color);bg.alpha_composite(image)
                name=f'{i:03d}-{label}.png';bg.convert('RGB').save(out/name)
                if s.get('key','').split(':')[1] in ['wave','pointer']:
                    x0,y0,x1,y1=bounds
                    bg.crop((x0,y0,x1,y0+int((y1-y0)*.65))).convert('RGB').save(out/f'{i:03d}-{label}-upper.png')
                thumb=bg.crop(bounds).convert('RGB');thumb.thumbnail((195,275))
                sheet.paste(thumb,((i%3)*400+j*200,(i%12//3)*310))
            ImageDraw.Draw(sheet).text(((i%3)*400+4,(i%12//3)*310+278),s['key'][:60],fill='white')
            frames.append({'index':i,'key':s['key'],'alpha_bounds':bounds,'light':f'{i:03d}-light.png','dark':f'{i:03d}-dark.png'})
        except (ValueError,KeyError,OSError,IndexError) as e: errors.append(f'Frame {i}: {e}')
    if blank: errors.append('Blank/tiny images: '+str(blank))
    for i,sheet in enumerate(sheets):sheet.save(out/('contact.jpg' if i==0 else f'contact-{i+1:02d}.jpg'))
    # A readable index avoids forcing a smaller model to open every full-resolution file at once.
    (out/'frames.json').write_text(json.dumps(frames,indent=2)+'\n',encoding='utf-8')
    result={'schema':2,'machine_passed':not errors,'errors':errors,'samples':len(samples),'pack_fingerprint':data.get('pack_fingerprint'),
            'input_sha256':project.sha(input_path),'input_file':Path(input_path).resolve().relative_to(project.ROOT).as_posix(),
            'contact_sheets':len(sheets),'visual_review':'required; machine checks do not establish seamless art'}
    (out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result
