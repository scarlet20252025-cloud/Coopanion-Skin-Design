"""Mother-visible + genuinely generated concealed source, isolated ponytail pilot.

No runtime pack promotion. Remaining mother is a diagnostic foreground only.
"""
from pathlib import Path
import json,hashlib
import cv2,numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;O=P/'official-visible'
def read(p):return np.asarray(Image.open(p).convert('RGBA'),np.float32)/255
def pm(x):
 x=x.copy();x[:,:,:3]*=x[:,:,3:4];return x
def straight(x):
 x=x.copy();x[:,:,:3]=np.divide(x[:,:,:3],x[:,:,3:4],out=np.zeros_like(x[:,:,:3]),where=x[:,:,3:4]>1e-6);return np.clip(x,0,1)
def save(name,x):Image.fromarray(np.uint8(straight(x)*255+.5)).save(O/name)
def over(a,b):return a+b*(1-a[:,:,3:4])
m=read(O/'mother-source-matte.png');g=read(P/'raw/near-pony-hidden-02.png');edit=read(P/'registered/mother-without-near-pony-01.png')
c=np.asarray(Image.open(O/'near-ownership-mask.png'),np.float32)/255
vis=read(O/'near-visible-mother.png');h,w=m.shape[:2];yy,xx=np.mgrid[:h,:w]
# Only concealed root and rear-overlapped lower-right may receive generated art.
hidden=((yy>=790)&(yy<=944)&(xx>=180)&(xx<290))|((yy>=280)&(yy<340)&(xx>=323)&(xx<400))
hidden=hidden.astype(np.float32)*(1-c)
# Tiny RGB ghosts with alpha 1/255 are not visible ink; retain all >=3/255 coverage.
g[g[:,:,3]<3/255]=0
part=pm(vis)+pm(g)*hidden[:,:,None]
part=np.clip(part,0,1)
# Complementary foreground alpha avoids double attenuation of split AA pixels.
pa=vis[:,:,3];ma=m[:,:,3]
fa=np.divide(ma-pa,1-pa,out=np.zeros_like(ma),where=(1-pa)>1e-6)
fg=m.copy();fg[:,:,3]=np.clip(fa,0,1);fg=pm(fg)
# Backfill never creates new silhouette outside the mother. Its source is the
# removal edit, not a stretched old hair patch; foreground owns broad rear ink.
safe=cv2.erode((ma>.98).astype('uint8'),np.ones((7,7),np.uint8)).astype(np.float32)
fill=pm(edit)*(c*safe)[:,:,None]
save('near-pony-complete.png',part);save('mother-remainder.png',fg);save('near-rear-fill.png',fill)
def render(amount):
 # Tied root follows the head. Free span bends laterally; no independent rigid
 # root rotation and no twisting, scaling or cosine displacement across width.
 t=np.clip((yy-430)/480,0,1).astype(np.float32)
 fall=t*t*(3-2*t)
 moved=cv2.remap(part,(xx-amount*fall).astype(np.float32),yy.astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT)
 moved=np.clip(moved,0,1)
 return over(fg,over(moved,fill))
neutral=render(0);save('pilot-neutral.png',neutral)
diff=np.abs(neutral-pm(m));aoutside=(neutral[:,:,3]>.1)&(ma<.05)
report={'status':'diagnostic only; visual review pending','mother':hashlib.sha256((P.parent/'master.png').read_bytes()).hexdigest(),'visible_source':'near-visible-mother.png','hidden_source':'../raw/near-pony-hidden-02.png','hidden_registration':[[1,0,0],[0,1,0]],'hidden_registration_note':'same canvas edit; visible generated pixels discarded; identity only for concealed pixels','root_fixed_until_y':430,'test_tip_displacement_px':[-12,0,12],'neutral_outside_mother_pixels':int(aoutside.sum()),'neutral_premultiplied_mae':float(diff.mean()),'body_expression_status':'remaining mother used for part diagnostic; not a runtime or expression test'}
board=Image.new('RGB',(1440,1080),'#292932');d=ImageDraw.Draw(board)
for j,bg in enumerate(['#e8e2ef','#202128']):
 for i,(name,a) in enumerate([('Mother',pm(m)),('-12px stress',render(-12)),('Rest',neutral),('+12px stress',render(12))]):
  im=Image.fromarray(np.uint8(straight(a)*255+.5));b=Image.new('RGBA',(w,h),bg);b.alpha_composite(im);b.thumbnail((355,500));board.paste(b,(i*360,j*540+30));d.text((i*360+8,j*540+8),name,fill='white')
board.save(O/'pilot-motion-review.png')
details=Image.new('RGB',(1280,900),'#292932');d=ImageDraw.Draw(details)
for j,(box,label) in enumerate([((295,270,420,430),'Root'),((135,740,310,960),'Lower occlusion')]):
 for i,(name,a) in enumerate([('Mother',pm(m)),('-12px',render(-12)),('Rest',neutral),('+12px',render(12))]):
  im=Image.fromarray(np.uint8(straight(a)*255+.5));b=Image.new('RGBA',(w,h),'#e8e2ef');b.alpha_composite(im);b=b.crop(box);b.thumbnail((315,400));b=b.resize((315,400));details.paste(b,(i*320,j*450+30));d.text((i*320+5,j*450+8),label+' '+name,fill='white')
details.save(O/'pilot-detail-review.png')
(O/'pilot-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
