from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;R=P/'references/far-local-v3'
for name,src,box in [('generated',P/'raw/far-pony-hidden-03.png',(520,500,815,1100)),('mother',P/'official-visible/far-visible-mother.png',(790,570,990,970))]:
 im=Image.open(src).convert('RGBA');bg=Image.new('RGBA',im.size,'#e8e2ef');bg.alpha_composite(im);bg=bg.crop(box).resize(((box[2]-box[0])*2,(box[3]-box[1])*2));d=ImageDraw.Draw(bg)
 for x in range((box[0]//20+1)*20,box[2],20):
  u=(x-box[0])*2;d.line((u,0,u,bg.height),fill=(130,130,130,120));d.text((u+2,5),str(x),fill='black')
 for y in range((box[1]//20+1)*20,box[3],20):
  v=(y-box[1])*2;d.line((0,v,bg.width,v),fill=(130,130,130,120));d.text((2,v+2),str(y),fill='black')
 bg.save(R/(name+'-grid.png'))
