"""Two separate hair components; mother remainder is diagnostic only."""
from pathlib import Path
import json,hashlib
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageOps
P=Path(__file__).resolve().parent;O=P/'official-visible'
def read(p):return np.asarray(Image.open(p).convert('RGBA'),np.float32)/255
def pm(x):
 x=x.copy();x[:,:,:3]*=x[:,:,3:4];return x
def straight(x):
 x=x.copy();x[:,:,:3]=np.divide(x[:,:,:3],x[:,:,3:4],out=np.zeros_like(x[:,:,:3]),where=x[:,:,3:4]>1e-6);return np.clip(x,0,1)
def save(name,x):Image.fromarray(np.uint8(straight(x)*255+.5)).save(O/name)
def over(a,b):return a+b*(1-a[:,:,3:4])
m=read(O/'mother-source-matte.png');h,w=m.shape[:2];yy,xx=np.mgrid[:h,:w]
c1=np.asarray(Image.open(O/'near-ownership-mask.png'),np.float32)/255
c2=np.asarray(Image.open(O/'far-ownership-mask.png'),np.float32)/255
v1=read(O/'near-visible-mother.png');v2=read(O/'far-visible-mother.png')
part1=pm(read(O/'near-pony-complete.png'))
g=read(P/'registered/far-pony-hidden-01.png');g[g[:,:,3]<3/255]=0
hidden=(((yy>=790)&(yy<=960)&(xx>835)&(xx<950))|((yy>=300)&(yy<590)&(xx>710)&(xx<840))).astype(np.float32)*(1-c2)
part2=np.clip(pm(v2)+pm(g)*hidden[:,:,None],0,1)
save('far-pony-complete.png',part2)
pa=v1[:,:,3]+v2[:,:,3];ma=m[:,:,3]
fa=np.divide(ma-pa,1-pa,out=np.zeros_like(ma),where=(1-pa)>1e-6)
fg=m.copy();fg[:,:,3]=np.clip(fa,0,1);fg=pm(fg)
safe=cv2.erode((ma>.98).astype('uint8'),np.ones((7,7),np.uint8)).astype(np.float32)
fill=pm(read(P/'registered/mother-without-near-pony-01.png'))*(c1*safe)[:,:,None]
fill=over(pm(read(P/'registered/mother-without-far-pony-01.png'))*(c2*safe)[:,:,None],fill)
save('pair-remainder.png',fg);save('pair-rear-fill.png',fill)
def move(p,amount,start,end):
 t=np.clip((yy-start)/(end-start),0,1).astype(np.float32);f=t*t*(3-2*t)
 return np.clip(cv2.remap(p,(xx-amount*f).astype(np.float32),yy.astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT),0,1)
def render(a,b):return over(fg,over(move(part1,a,430,910),over(move(part2,b,590,940),fill)))
neutral=render(0,0);save('pair-neutral.png',neutral)
report={'status':'FAIL motion art acceptance; diagnostic only','scope':'independent near/far ponytails with original visible mother pixels and generated hidden continuation','render_reference':'/preview/vendor/kit/rig.js','source_matte':'mother-source-matte.png','root_pins':{'near':430,'far':590},'diagnostic_tip_px':6,'stress_max_tip_px':12,'neutral_premultiplied_mae':float(np.abs(neutral-pm(m)).mean()),'neutral_alpha_outside_source':int(((neutral[:,:,3]>.1)&(ma<.05)).sum()),'expression_lock':'unchanged; checked separately','known_limits':['far hidden root ends inside opaque head, not a fully exposed tied root','far lower hidden fill reveals a diagonal cut and color discontinuity at 6px displacement','near lower contact needs further refinement at 12px stress','remaining mother is a diagnostic foreground, not a final body layer'],'promotion_allowed':False}
(O/'pair-pilot-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
board=Image.new('RGB',(1440,1080),'#292932');d=ImageDraw.Draw(board)
states=[('Mother',pm(m)),('Outward 6px',render(-6,6)),('Rest',neutral),('Inward 6px',render(6,-6))]
for j,bg in enumerate(['#e8e2ef','#202128']):
 for i,(name,a) in enumerate(states):
  im=Image.fromarray(np.uint8(straight(a)*255+.5));b=Image.new('RGBA',(w,h),bg);b.alpha_composite(im);b.thumbnail((355,500));board.paste(b,(i*360,j*540+30));d.text((i*360+8,j*540+8),name,fill='white')
board.save(O/'pair-full-review.png')
board2=Image.new('RGB',(1440,1000),'#292932');d=ImageDraw.Draw(board2)
for j,box in enumerate([(775,510,880,680),(850,750,995,970)]):
 for i,(name,a) in enumerate(states):
  im=Image.fromarray(np.uint8(straight(a)*255+.5));b=Image.new('RGBA',(w,h),'#e8e2ef');b.alpha_composite(im);b=b.crop(box).resize((350,460));board2.paste(b,(i*360,j*500+30));d.text((i*360+8,j*500+8),name,fill='white')
board2.save(O/'far-detail-review.png');print(json.dumps(report))
