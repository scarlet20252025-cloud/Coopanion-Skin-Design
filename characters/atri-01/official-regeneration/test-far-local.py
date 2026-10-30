"""Isolated diagnostic. Never overwrite the existing pack or previous pilot."""
from pathlib import Path
import json,hashlib,sys
import cv2,numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;O=P/'official-visible';mode=sys.argv[1] if len(sys.argv)>1 else 'hidden';N=P/({'hidden':'local-fill-review','whole':'local-full-layer-review','lobe':'local-lobe-review'}[mode]);N.mkdir(exist_ok=True)
def read(p):return np.asarray(Image.open(p).convert('RGBA'),np.float32)/255
def pm(x):
 x=x.copy();x[:,:,:3]*=x[:,:,3:4];return x
def st(x):
 x=x.copy();x[:,:,:3]=np.divide(x[:,:,:3],x[:,:,3:4],out=np.zeros_like(x[:,:,:3]),where=x[:,:,3:4]>1e-6);return np.clip(x,0,1)
def save(name,x):Image.fromarray(np.uint8(st(x)*255+.5)).save(N/name)
def over(a,b):return a+b*(1-a[:,:,3:4])
m=read(O/'mother-source-matte.png');h,w=m.shape[:2];yy,xx=np.mgrid[:h,:w]
c=np.asarray(Image.open(O/'far-ownership-mask.png'),np.float32)/255
v=read(O/'far-visible-mother.png');g=read(P/'registered/far-pony-hidden-03.png');g[g[:,:,3]<3/255]=0
region=(((yy>=775)&(yy<=960)&(xx>825)&(xx<990))|((yy>=300)&(yy<590)&(xx>710)&(xx<850))).astype(np.float32)
hidden=region*(1-c)
part=np.clip(pm(v)+pm(g)*hidden[:,:,None],0,1)
if mode=='whole':part=pm(g)
if mode=='lobe':
 g=read(P/'registered/far-lobe-complete-01.png');g[g[:,:,3]<3/255]=0
 hidden=((yy>=770)&(yy<=935)).astype(np.float32)*(1-c)
 part=np.clip(pm(v)+pm(g)*hidden[:,:,None],0,1)
save('far-pony-complete.png',part)
near=pm(read(O/'near-pony-complete.png'));fg=pm(read(O/'pair-remainder.png'));fill=pm(read(O/'pair-rear-fill.png'))
def move(p,amount,start,end):
 t=np.clip((yy-start)/(end-start),0,1).astype(np.float32);f=t*t*(3-2*t)
 return np.clip(cv2.remap(p,(xx-amount*f).astype(np.float32),yy.astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT),0,1)
def render(n):return over(fg,over(move(near,-n,430,910),over(move(part,n,590,940),fill)))
states=[('Mother',pm(m))]+[(str(n)+'px',render(n)) for n in [0,6,-6,12,-12]]
for label,box,size in [('full',(0,0,w,h),(280,340)),('lower',(840,750,995,970),(300,440)),('root',(775,470,890,670),(300,440))]:
 board=Image.new('RGB',(size[0]*6,(size[1]+30)*2),'#292932');d=ImageDraw.Draw(board)
 for j,bg in enumerate(['#e8e2ef','#202128']):
  for i,(name,a) in enumerate(states):
   im=Image.fromarray(np.uint8(st(a)*255+.5));b=Image.new('RGBA',(w,h),bg);b.alpha_composite(im);b=b.crop(box);scale=min(size[0]/b.width,size[1]/b.height);b=b.resize((round(b.width*scale),round(b.height*scale)),Image.Resampling.LANCZOS);board.paste(b,(i*size[0],j*(size[1]+30)+30));d.text((i*size[0]+8,j*(size[1]+30)+8),name,fill='white')
 board.save(N/(label+'.png'))
for n in [0,6,-6,12,-12]:save('frame-'+str(n)+'.png',render(n))
neutral=render(0)
report={'status':'UNREVIEWED; source registration does not establish art acceptance','donor':'../registered/far-pony-hidden-03.png','new_pixels':'generated concealed pixels only','visible_source':'../official-visible/far-visible-mother.png','neutral_premultiplied_mae':float(np.abs(neutral-pm(m)).mean()),'outside_alpha_pixels':int(((neutral[:,:,3]>.1)&(m[:,:,3]<.05)).sum()),'promotion_allowed':False}
(N/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
