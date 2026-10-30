from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;R=P/'references/far-tip-registration';R.mkdir(exist_ok=True)
for name,file in [('mother',P/'official-visible/mother-source-matte.png'),('generation',P/'registered/mother-without-far-rear-03.png')]:
 im=Image.open(file).convert('RGBA');bg=Image.new('RGBA',im.size,'#e8e2ef');bg.alpha_composite(im);box=(800,700,1000,1050);bg=bg.crop(box).resize((600,1050));d=ImageDraw.Draw(bg)
 for x in range(810,1000,10):
  u=(x-800)*3;d.line((u,0,u,1050),fill='#999999');d.text((u+1,3),str(x),fill='black')
 for y in range(710,1050,10):
  v=(y-700)*3;d.line((0,v,600,v),fill='#999999');d.text((1,v+1),str(y),fill='black')
 bg.save(R/(name+'.png'))
