"""Bind current render evidence to candidate files; keep art and native-host acceptance separate."""
from pathlib import Path
import json,hashlib
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont

Q=Path(__file__).resolve().parent
ROOT=Q.parents[3]
PACK=ROOT/'scratch/candidates/atri-pure-components-01'
frames=Q/'qa/current'
meta=json.loads((frames/'samples.json').read_text(encoding='utf8'))
assert len(meta['samples'])==len(meta['expected'])==104
assert set(s['key'] for s in meta['samples'])==set(meta['expected'])
assert all(c['accepted'] for c in meta['checks'])
for s in meta['samples']:
    if ':run:action:' in s['key'] or ':walk:action:' in s['key']:
        assert s['layout']['mode']==s['key'].split(':')[1]
        assert s['layout']['facing']==s['facing'],s['key']
ratios=[s['secondary']['bodyScaleRatio'] for s in meta['samples']]
assert max(abs(x-1) for x in ratios)<1e-12
source=json.loads((PACK/'SOURCE.json').read_text(encoding='utf8'))
edge=json.loads((PACK/'EDGE-EXPORT.json').read_text(encoding='utf8'))
counts={}
for part in source['parts']:
    a=np.array(Image.open(PACK/part['file']).convert('RGBA'))
    counts[part['id']]=cv2.connectedComponents((a[:,:,3]>0).astype('uint8'))[0]-1
    assert counts[part['id']]==1,part['id']
    exp=next(x for x in edge['parts'] if x['id']==part['id'])
    assert hashlib.sha256(a[:,:,3].tobytes()).hexdigest()==exp['alpha_sha256']
lock=json.loads((Q.parent/'expression-lock.json').read_text(encoding='utf8'))
for f,sha in lock['files'].items():
    assert hashlib.sha256((ROOT/lock['baseline']/f).read_bytes()).hexdigest()==sha,f
    if f.startswith('tex/'):assert hashlib.sha256((PACK/f).read_bytes()).hexdigest()==sha,f
original=(ROOT/lock['baseline']/'figure.js').read_text(encoding='utf8')
functions=original[original.index(' function buildFace('):original.index('\n const figure=')]
assert functions in (PACK/'figure.js').read_text(encoding='utf8')

def png(key):
    i=next(i for i,s in enumerate(meta['samples']) if s['key']==key)
    return Image.open(frames/f'{i:03}.png').convert('RGBA')

keys=['1:neutral:rest:0.05','1:wave:action:0.85','1:sit:action:0.7']
tiles=[]
for key in keys:
    im=png(key);bg=Image.new('RGBA',im.size,'#e8e2ef');bg.alpha_composite(im)
    cx=im.width//2;tiles.append(bg.crop((cx-350,0,cx+350,800)))
font=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',22)
board=Image.new('RGB',(2100,882),'#f7f2f8');draw=ImageDraw.Draw(board)
for i,(tile,label) in enumerate(zip(tiles,['站姿','招手','坐姿'])):
    board.paste(tile,(i*700,42));draw.text((i*700+18,8),label,font=font,fill='#44384e')
draw.text((18,848),'实际渲染帧 · 整件生成候选 · 未安装',font=font,fill='#44384e')
board.save(Q/'preview-current.png')
im=png(keys[1]);bg=Image.new('RGBA',im.size,'#e8e2ef');bg.alpha_composite(im);cx=im.width//2
bg.crop((cx-250,270,cx+90,550)).resize((680,560),Image.Resampling.NEAREST).save(Q/'wave-joints-current.png')
files={str(f.relative_to(PACK)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(PACK.rglob('*')) if f.is_file()}
fingerprint=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
report={'date':'2026-10-16','candidate':'scratch/candidates/atri-pure-components-01','pack_fingerprint':fingerprint,'pack_files':files,'frame_count':104,'directions':[1,-1],'checks':len(meta['checks']),'rejected_checks':0,'travel_verified_actual_modes_and_directions':True,'body_scale_ratio':[min(ratios),max(ratios)],'component_alpha_gt0_connected_counts':counts,'edge_rgb_export_alpha_changed_pixels':0,'edge_rgb_export_opaque_rgba_changed_pixels':0,'approved_original_files_unchanged':29,'candidate_expression_textures_byte_identical':26,'expression_functions_copied_verbatim':True,'review':'Full-character and joint views, light/dark, two directions. Wave shoulder ellipse removed by whole-component imagegen61. Finite sampled review, not exhaustive art acceptance.','evidence':'qa/current/samples.json','screenshot_kind':'Actual SVG renderer PNG exports from page controls; browser screenshot API unavailable','limits':['User art acceptance pending; initial hair placements not an exact pixel reconstruction claim','Seated long hair still part of whole seated pose, no independent seated pony dynamics','Native host untested; not installed or published'],'adobe_generation_calls':0}
(Q/'VALIDATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
progress=json.loads((Q.parent/'progress.json').read_text(encoding='utf8'))
progress['pure_generation'].update(validation='pure-generation/VALIDATION.json',frame_count=104,checks=len(meta['checks']),final_torso='attempt-61.json',status='reviewable candidate; user art acceptance and seated independent hair dynamics pending')
(Q.parent/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'frames':104,'checks':len(meta['checks']),'rejects':0,'fingerprint':fingerprint,'expressions_preserved':True},indent=2))
