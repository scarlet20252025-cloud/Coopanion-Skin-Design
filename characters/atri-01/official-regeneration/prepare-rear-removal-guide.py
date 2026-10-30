from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;im=Image.open(P.parent/'master.png').convert('RGBA');d=ImageDraw.Draw(im)
for text,p,label,color in [('REMOVE BROAD INNER REAR CURTAIN',(865,1000),(20,1180),'#e53838'),('KEEP NARROW OUTER PONY',(955,855),(720,1240),'#2477e0')]:
 d.ellipse((p[0]-12,p[1]-12,p[0]+12,p[1]+12),outline=color,width=4)
 d.line((label[0]+50,label[1]-5,*p),fill=color,width=4)
 d.rectangle((label[0],label[1],label[0]+360,label[1]+32),fill='white')
 d.text((label[0]+5,label[1]+7),text,fill=color)
im.save(P/'references/far-rear-removal-guide.png')
