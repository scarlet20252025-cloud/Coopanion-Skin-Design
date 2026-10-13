from pathlib import Path
import json,base64,io,sys,collections,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'characters/original-01/rig-v005-r02'/(sys.argv[2] if len(sys.argv)>2 else 'qa');OUT.mkdir(exist_ok=True)
data=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
if len(sys.argv)>3:data['samples']=[s for s in data['samples'] if s['word'] in sys.argv[3].split(',')]
lock=json.loads((ROOT/'characters/original-01/production-lock.json').read_text(encoding='utf-8'));assert data['master']==lock['sha256']
groups=collections.defaultdict(list)
def finite(o):
    if isinstance(o,float):return math.isfinite(o)
    if isinstance(o,dict):return all(finite(v) for v in o.values())
    if isinstance(o,list):return all(finite(v) for v in o)
    return True
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
for s in data['samples']:
    assert finite(s['layout'])
    im=Image.open(io.BytesIO(base64.b64decode(s.pop('png').split(',',1)[1]))).convert('RGBA');assert im.getbbox()
    name=f"{s['word']}-{s['frame']:03d}.png";im.save(OUT/name)
    groups[s['word']].append((s,im))
for word,entries in groups.items():
    width,height=entries[0][1].size;crop=(int(width/2-185),0,int(width/2+185),height)
    board=Image.new('RGB',(6*240,math.ceil(len(entries)/6)*310),'#f3eff9');draw=ImageDraw.Draw(board)
    for j,(s,im) in enumerate(entries):
        center=s['layout'].get('x',width/2);im=im.crop((int(center-185),0,int(center+185),height));im.thumbnail((240,280),Image.Resampling.LANCZOS);x,y=j%6*240,j//6*310;board.paste(im,(x,y),im);draw.text((x+8,y+280),f"{s['t']:.3f}s | {s['layout']['mode']}",font=font,fill='#655073')
    board.save(OUT/(word+'-contact.png'))
report={'master_sha256':data['master'],'samples':len(data['samples']),'groups':{k:len(v) for k,v in groups.items()},'finite_layouts':True,'nonempty_frames':True,'source':'native kit preview export','visual_review':'pending','limits':f"{len(data['samples'])} snapshots; see timeline for sampling intervals; not an exhaustive 60 fps motion validation"}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(OUT/'timeline.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
