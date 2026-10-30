"""Use published closed-form matting for the mother ink/background interface.

Only a narrow, semantically confirmed internal overlap is estimated. This does
not create hair geometry or replace approved expression files.
"""
from pathlib import Path
import json
import cv2,numpy as np
from PIL import Image,ImageDraw
from pymatting import estimate_alpha_cf,estimate_foreground_ml
P=Path(__file__).resolve().parent;S=P/'reverse-removal-safe-review';O=P/'official-visible';N=P/'cf-matte-review';N.mkdir(exist_ok=True)
def read(p):return np.asarray(Image.open(p).convert('RGBA'),np.float64)/255
def pm(a):
 a=a.copy();a[:,:,:3]*=a[:,:,3:4];return a
def st(a):
 a=a.copy();a[:,:,:3]=np.divide(a[:,:,:3],a[:,:,3:4],out=np.zeros_like(a[:,:,:3]),where=a[:,:,3:4]>1e-6);return np.clip(a,0,1)
def save(n,a):Image.fromarray(np.uint8(st(a)*255+.5)).save(N/n)
def over(a,b):return a+b*(1-a[:,:,3:4])
m=read(O/'mother-source-matte.png');h,w=m.shape[:2];fg=pm(read(S/'pair-remainder.png'));far=pm(read(S/'far-pony-complete.png'));near=pm(read(O/'near-pony-complete.png'));fill=pm(read(S/'pair-rear-fill.png'))
report=json.loads((S/'report.json').read_text());anchors=np.array(report['boundary_yx']);cuts=np.interp(np.arange(h),anchors[:,0],anchors[:,1]);lum=m[:,:,:3].mean(2)
x0,y0,x1,y1=850,800,953,932;rgb=m[y0:y1,x0:x1,:3].copy();ma=m[y0:y1,x0:x1,3:4]
rgb=rgb*ma+np.array([.91,.89,.94])*(1-ma)
trimap=np.zeros(rgb.shape[:2]);centers=[]
for j,y in enumerate(range(y0,y1)):
 prediction=int(cuts[y])-4;left=prediction-7;right=prediction+5
 edge=left+int(np.argmin(lum[y,left:right]));centers.append(edge)
 trimap[j,:max(0,edge+1-x0)]=1
 trimap[j,max(0,edge+1-x0):max(0,edge+6-x0)]=.5
alpha=estimate_alpha_cf(rgb,trimap)
F,B=estimate_foreground_ml(rgb,alpha,return_background=True)
for j,y in enumerate(range(y0,y1)):
 edge=centers[j]
 for x in range(edge,edge+6):
  if m[y,x,3]<.99:continue
  i=x-x0;a=alpha[j,i]
  # The source underneath this narrow mixed ink band is the estimated original
  # background color. Preserve the generated contour elsewhere.
  far[y,x]=np.r_[B[j,i],1]
  fg[y,x]=np.r_[F[j,i]*a,a]
Image.fromarray(np.uint8(alpha*255+.5)).save(N/'interface-alpha.png')
Image.fromarray(np.uint8(trimap*255+.5)).save(N/'interface-trimap.png')
save('far-pony-complete.png',far);save('pair-remainder.png',fg);save('pair-rear-fill.png',fill)
yy,xx=np.mgrid[:h,:w]
def move(p,a,start,end):
 t=np.clip((yy-start)/(end-start),0,1).astype(np.float32);f=t*t*(3-2*t)
 return np.clip(cv2.remap(p.astype(np.float32),(xx-a*f).astype(np.float32),yy.astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT),0,1)
def render(a):return over(fg,over(move(near,-a,430,910),over(move(far,a,800,940),fill)))
states=[('Mother',pm(m))]+[(str(n)+'px',render(n)) for n in [0,6,-6,12,-12]]
for label,box,size in [('full',(0,0,w,h),(280,340)),('lower',(840,750,995,970),(300,440))]:
 board=Image.new('RGB',(size[0]*6,(size[1]+30)*2),'#292932');d=ImageDraw.Draw(board)
 for j,bg in enumerate(['#e8e2ef','#202128']):
  for i,(name,a) in enumerate(states):
   im=Image.fromarray(np.uint8(st(a)*255+.5));b=Image.new('RGBA',(w,h),bg);b.alpha_composite(im);b=b.crop(box);scale=min(size[0]/b.width,size[1]/b.height);b=b.resize((round(b.width*scale),round(b.height*scale)),Image.Resampling.LANCZOS);board.paste(b,(i*size[0],j*(size[1]+30)+30));d.text((i*size[0]+8,j*(size[1]+30)+8),name,fill='white')
 board.save(N/(label+'.png'))
for n in [0,6,-6,12,-12]:save('frame-'+str(n)+'.png',render(n))
neutral=render(0);report.update(status='UNREVIEWED published matting prototype; not an art pass',method='PyMatting estimate_alpha_cf + estimate_foreground_ml',method_docs='https://pymatting.github.io/examples.html',interface_box=[x0,y0,x1,y1],neutral_premultiplied_mae=float(np.abs(neutral-pm(m)).mean()),outside_alpha_pixels=int(((neutral[:,:,3]>.1)&(m[:,:,3]<.05)).sum()),promotion_allowed=False)
(N/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k] for k in ['status','neutral_premultiplied_mae','outside_alpha_pixels']}))
