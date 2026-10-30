"""Review generated assets only; never includes mother pixels in reconstruction."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
P=Path(__file__).resolve().parent
parts=['ponytail-left-02','ponytail-right-05','rear-complete-01','leg-left-02','leg-right-01','garment-connected-01','ahoge-01','bow-right-01','head-01','bow-left-01']
rejected=set(json.loads((P/'progress.json').read_text(encoding='utf-8')).get('rejected',[]))
if rejected.intersection(parts):
 raise SystemExit('Assembly blocked: rejected source parts: '+', '.join(sorted(rejected.intersection(parts))))
canvas=Image.new('RGBA',(1145,1374));used=[]
for part in parts:
 f=P/'registered'/(part+'.png')
 if f.exists():canvas.alpha_composite(Image.open(f).convert('RGBA'));used.append(part)
canvas.save(P/'assembly.png')
board=Image.new('RGB',(1725,750),'#303038');d=ImageDraw.Draw(board)
for i,(label,col,im) in enumerate([('MOTHER','#e8e2ef',Image.open(P.parent/'master.png')),('GENERATED ONLY - incomplete','#e8e2ef',canvas),('DARK BACKGROUND','#24242b',canvas)]):
 bg=Image.new('RGBA',canvas.size,col);bg.alpha_composite(im);bg.thumbnail((565,680));board.paste(bg,(i*575,45));d.text((i*575+10,12),label,fill='white')
board.save(P/'assembly-review.png')
(P/'assembly-report.json').write_text(json.dumps({'used':used,'missing':[p for p in parts if p not in used],'state':'incomplete generated-only review; not accepted'},indent=2)+'\n')
detail=Image.new('RGB',(1800,900),'#303038')
for j,(name,box) in enumerate([('face',(460,360,790,610)),('near cuff',(320,860,530,1020)),('far cuff',(750,840,855,1000)),('hem',(390,1040,810,1150))]):
 for i,col in enumerate(['#ffffff','#202026']):
  im=canvas.crop(box);bg=Image.new('RGBA',im.size,col);bg.alpha_composite(im);bg.thumbnail((430,420));detail.paste(bg,(j*450,i*450+30))
  ImageDraw.Draw(detail).text((j*450+10,i*450+8),name,fill='white')
detail.save(P/'assembly-details.png')
print(json.dumps({'used':used,'missing':[p for p in parts if p not in used]}))
