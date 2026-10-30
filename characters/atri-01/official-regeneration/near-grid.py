from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent
im=Image.open(P.parent/'master.png').convert('RGBA');bg=Image.new('RGBA',im.size,'#e8e2ef');bg.alpha_composite(im)
crop=bg.crop((130,280,400,950)).resize((540,1340));d=ImageDraw.Draw(crop)
for x in range(140,401,20):
 u=(x-130)*2;d.line((u,0,u,1340),fill=(100,120,150,100));d.text((u+2,2),str(x),fill='black')
for y in range(300,951,25):
 v=(y-280)*2;d.line((0,v,540,v),fill=(100,120,150,100));d.text((2,v+2),str(y),fill='black')
crop.save(P/'official-visible/near-mother-grid.png')
