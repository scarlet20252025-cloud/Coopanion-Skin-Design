"""Difference-based pilot. Keep intermediate masks reviewable; never promote automatically."""
from pathlib import Path
import hashlib,json
import cv2,numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent
out=P/'official-visible';out.mkdir(exist_ok=True)
m=np.array(Image.open(P.parent/'master.png').convert('RGBA'))
e=np.array(Image.open(P/'registered/mother-without-near-pony-01.png').convert('RGBA'))
ma=m[:,:,3]/255.;ea=e[:,:,3]/255.
d=np.max(np.abs(m[:,:,:3].astype(float)*ma[:,:,None]-e[:,:,:3]*ea[:,:,None]),axis=2)
roi=np.zeros(d.shape,np.uint8);roi[312:944,130:378]=1
delta=((d>22)&(ma>.06)&(roi>0)).astype('uint8')
# Select the substantial removed component rather than unrelated thin changed ink.
core=cv2.morphologyEx(delta,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
n,labels,stats,_=cv2.connectedComponentsWithStats(core)
label=labels[840,165]
if label==0:label=1+np.argmax(stats[1:,cv2.CC_STAT_AREA])
core=np.uint8(labels==label)
candidate=cv2.dilate(core,np.ones((5,5),np.uint8))&(delta>0)
contours,_=cv2.findContours(candidate.astype('uint8'),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
mask=np.zeros(delta.shape,np.uint8)
cv2.drawContours(mask,contours,-1,255,cv2.FILLED)
# Exterior AA is inherited from mother, never thresholded away.
mask=cv2.GaussianBlur(mask,(3,3),.55).astype(float)/255
part=m.copy();part[:,:,3]=np.uint8(ma*mask*255+.5)
part[part[:,:,3]==0,:3]=0
Image.fromarray(part).save(out/'near-visible-pilot.png')
Image.fromarray(np.uint8(mask*255+.5)).save(out/'near-difference-mask.png')
board=Image.new('RGB',(1200,780),'#292932');dr=ImageDraw.Draw(board)
for i,(title,im,bg) in enumerate([('Mother',Image.fromarray(m),'#e8e2ef'),('Visible component - light',Image.fromarray(part),'#e8e2ef'),('Visible component - dark',Image.fromarray(part),'#25252c')]):
 b=Image.new('RGBA',im.size,bg);b.alpha_composite(im);b=b.crop((120,270,425,950)).resize((330,736));board.paste(b,(400*i,30));dr.text((400*i+5,8),title,fill='white')
board.save(out/'near-mask-review.png')
report={'method':'registered removal edit -> substantial difference component -> mother pixels','status':'pilot needs visual review, not runtime ready','threshold':22,'mother_sha256':hashlib.sha256((P.parent/'master.png').read_bytes()).hexdigest(),'registration':'mother-without-near-pony-01-registration.json','mask':'near-difference-mask.png','visible_pixels':int((part[:,:,3]>0).sum())}
(out/'near-mask-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
