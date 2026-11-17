import argparse
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
import json
r=Path(__file__).resolve().parent
version=json.loads((r/'pack/xingyun/figure.json').read_text(encoding='utf-8'))['version']
parser=argparse.ArgumentParser(description='Render review images from the current local Xingyun pack.')
parser.add_argument('--out',type=Path,default=r/f'art-{version}')
args=parser.parse_args()
a=args.out
a.mkdir(parents=True,exist_ok=True)
model=json.loads((r/'pack/xingyun/model.json').read_text())
def tile(id,k=None):
 d=model['parts'][id]; image=Image.open(r/'pack/xingyun'/d['file']).convert('RGBA')
 x,y,w,h=d['box']
 if k is not None:
  tx=k%d['columns']*w
  ty=k//d['columns']*h
  image=image.crop((tx,ty,tx+w,ty+h))
 return image,(x,y)
def full(id,k=None):
 im=Image.new('RGBA',(1139,1381))
 src,pos=tile(id,k); im.paste(src,pos)
 return im
def masked(id,cover):
 im=full(id)
 im.putalpha(ImageChops.multiply(im.getchannel('A'),ImageChops.invert(full(cover).getchannel('A'))))
 return im
def head(k):
 out=full('headOpen')
 for n in ['eyeLeft','eyeRight']:
  if k:
   im,pos=tile(n,k); out.paste(im,pos)
 return out
base=Image.new('RGBA',(1139,1381))
for id in ['legBack','legNear','body','leftArm','staff','rightArm','lockLeftMotion','lockRightMotion']:
 im=masked(id,{'leftArm':'leftCover','rightArm':'rightCover'}[id]) if id in ('leftArm','rightArm') else full(id,8 if id.endswith('Motion') else None)
 base.alpha_composite(im)
for k,n in [(0,'open'),(16,'closed')]:
 face=head(k)
 im=base.copy(); im.alpha_composite(face); im.alpha_composite(full('crow')); im.save(a/f'assembled-{n}.png')
master=Image.open(r.parent/'xingyun-prep/source/master.png').convert('RGBA')
master.alpha_composite(Image.open(a/'assembled-open.png')); master.save(a/'master-overlay.png')
eye_box=(440,494,820,622)
motion=[]
for k in list(range(17))+list(range(15,0,-1)):
 im=Image.new('RGBA',(380,128),'#28272d'); im.alpha_composite(head(k).crop(eye_box)); motion.append(im.convert('RGB'))
motion[0].save(a/'blink-preview.gif',save_all=True,append_images=motion[1:],duration=[640]+[35]*16+[42]*15,loop=0,optimize=True)
out=Image.new('RGB',(760,445),'#28272d')
d=ImageDraw.Draw(out)
for j,k in enumerate([0,4,8,11,14,16]):
 im=head(k).crop(eye_box)
 out.paste(im,(j%2*380,j//2*148+14),im)
 d.text((j%2*380+4,j//2*148+4),str(k+1),fill='white')
out.save(a/'blink-check.png')
area=(422,669,850,1017)
s=Image.new('RGB',(856,348),'#26252b')
for i,p in enumerate([r/'art-0.1.1/assembled-open.png',a/'assembled-open.png']):
 im=Image.open(p).crop(area)
 s.paste(im,(i*428,0),im)
s.save(a/'hair-snake-check.png')
