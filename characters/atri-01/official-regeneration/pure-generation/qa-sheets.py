"""Present actual rendered exports on light/dark backgrounds without changing art."""
from pathlib import Path
import json,sys,math
from PIL import Image,ImageDraw

p=Path(sys.argv[1]);meta=json.loads((p/'samples.json').read_text(encoding='utf8'))
for kind in ['neutral','wave','run','walk','shake','nod','jump','dance','sit','moods','blink','pointer']:
    chosen=[(i,s) for i,s in enumerate(meta['samples']) if s['key'].split(':')[1]==kind]
    cols=4;tw,th=270,355;rows=math.ceil(len(chosen)/cols)
    board=Image.new('RGB',(cols*tw,rows*th),'#38323e');d=ImageDraw.Draw(board)
    for k,(i,s) in enumerate(chosen):
        im=Image.open(p/f'{i:03}.png').convert('RGBA');bg=Image.new('RGBA',im.size,'#e8e2ef' if s['facing']==1 else '#202128');bg.alpha_composite(im)
        box=s['layout']['box'];cx=box['x']+box['w']/2;left=max(0,int(cx-340));right=min(im.width,int(cx+340));bg=bg.crop((left,0,right,im.height));bg.thumbnail((tw,th-24))
        x=(k%cols)*tw;y=(k//cols)*th;board.paste(bg,(x,y+24));d.text((x+4,y+5),s['key'],fill='white')
    board.save(p/(kind+'-sheet.jpg'),quality=92)
print(len(meta['samples']), 'frames; rejected checks:',sum(not x['accepted'] for x in meta['checks']))
