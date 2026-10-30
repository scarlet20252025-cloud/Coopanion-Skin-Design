from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent
parts=['pony-pair-left-01','pony-pair-right-01','rear-system-01','leg-left-02','leg-right-01','garment-connected-01','ahoge-01','bow-right-01','head-01','bow-left-01']
canvas=Image.new('RGBA',(1145,1374))
for x in parts:canvas.alpha_composite(Image.open(P/'registered'/f'{x}.png').convert('RGBA'))
canvas.save(P/'hair-system-split-assembly.png')
mother=Image.open(P.parent/'master.png').convert('RGBA')
board=Image.new('RGB',(1710,730),'#303038');d=ImageDraw.Draw(board)
for i,(im,col,label) in enumerate([(mother,'#e8e2ef','MOTHER'),(canvas,'#e8e2ef','NEW SEPARATE LAYERS - DIAGNOSTIC'),(canvas,'#24242b','DARK BACKGROUND')]):
 bg=Image.new('RGBA',canvas.size,col);bg.alpha_composite(im);bg.thumbnail((560,680));board.paste(bg,(570*i,30));d.text((570*i+5,5),label,fill='white')
board.save(P/'hair-system-split-review.png')
def runs(im,y,x0,x1):
 a=np.array(im)[y,x0:x1,3]>127;edges=np.diff(np.r_[False,a,False].astype(int));return [[int(x0+s),int(x0+e-1)] for s,e in zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1))]
report={'parts':parts,'status':'diagnostic only; not integrated','far_row_runs':{y:{'mother':runs(mother,y,750,1020),'new':runs(canvas,y,750,1020)} for y in [550,600,650,700,750,800,850]},'near_row_runs':{y:{'mother':runs(mother,y,100,410),'new':runs(canvas,y,100,410)} for y in [500,600,700,800,900]}}
(P/'hair-system-split-review.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
