"""Recover source edge colors from the original opaque mother, without redrawing.

Old alpha is only a trimap guide. Unknown band may recover lost original ink;
alpha comes from C = alpha*F + (1-alpha)*B, not shrinking the old silhouette.
"""
from pathlib import Path
import hashlib,json
import cv2,numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;O=P/'official-visible'
src=Image.open(P.parent/'art-source/master-leg-v2.png').convert('RGB')
rgb=np.asarray(src,np.float32)/255
old=np.asarray(Image.open(P.parent/'master.png').convert('RGBA'),np.float32)/255
binary=(old[:,:,3]>.5).astype('uint8')
# Recover connected pale background slits that the previous matte marked opaque.
# White cloth is enclosed by its ink, and receives no background seed.
bgcandidate=(rgb.min(2)>.72)&(rgb[:,:,2]-rgb[:,:,0]>-.025)&(rgb[:,:,1]-rgb[:,:,0]>-.025)
n,lab,stats,_=cv2.connectedComponentsWithStats(bgcandidate.astype('uint8'))
seed=np.bincount(lab[(old[:,:,3]<.02)&bgcandidate],minlength=n)
bglabels=np.flatnonzero(seed>20);bglabels=bglabels[bglabels!=0]
background=np.isin(lab,bglabels)
binary[background]=0
inside=cv2.erode(binary,np.ones((7,7),np.uint8))>0
outside=cv2.dilate(binary,np.ones((11,11),np.uint8))==0
unknown=~(inside|outside)
dark=(rgb.mean(2)<.30)&(cv2.dilate(binary,np.ones((3,3),np.uint8))>0)
def nearest(mask):
 _,labels=cv2.distanceTransformWithLabels((~mask).astype('uint8'),cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
 coords=np.argwhere(mask);coords=coords[np.maximum(labels-1,0)]
 return rgb[coords[:,:,0],coords[:,:,1]]
F=nearest(dark);B=nearest(outside)
v=F-B;delta=rgb-B
a=np.clip((delta*v).sum(2)/np.maximum((v*v).sum(2),.001),0,1)
a=np.clip((a-.012)/.988,0,1)
a[inside]=1;a[outside]=0
straight=np.divide(rgb-(1-a[:,:,None])*B,np.maximum(a[:,:,None],.0001))
straight[inside]=rgb[inside];straight=np.clip(straight,0,1);straight[a<1/255]=0;a[a<1/255]=0
# Division by tiny alpha amplifies source/background grain into bright RGB.
# At soft outline pixels use the nearest real ink colour used by the matte fit.
soft=unknown&(a<.92);straight[soft]=F[soft]
straight[a==0]=0
result=np.dstack((straight,a))
Image.fromarray(np.uint8(result*255+.5)).save(O/'mother-source-matte.png')
recomp=straight*a[:,:,None]+B*(1-a[:,:,None]);error=np.abs(recomp-rgb)[unknown]
report={'source':'../art-source/master-leg-v2.png','source_sha256':hashlib.sha256((P.parent/'art-source/master-leg-v2.png').read_bytes()).hexdigest(),'locked_master_unchanged':True,'method':'source RGB; narrow trimap color-line matting; nearest local background and dark outline foreground; no painted pixels','unknown_band_mae':float(error.mean()),'changed_alpha_gt_0_1':int((np.abs(a-old[:,:,3])>.1).sum()),'status':'review required'}
(O/'mother-matte-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
board=Image.new('RGB',(1440,920),'#292932');d=ImageDraw.Draw(board)
for j,box in enumerate([(135,750,315,950),(305,430,370,620)]):
 for i,(label,im,bg) in enumerate([('Original RGB',src,'#e8e2ef'),('Old alpha',Image.fromarray(np.uint8(old*255+.5)),'#e8e2ef'),('Recovered source edge',Image.fromarray(np.uint8(result*255+.5)),'#e8e2ef'),('Dark background',Image.fromarray(np.uint8(result*255+.5)),'#202128')]):
  b=Image.new('RGBA',src.size,bg);b.alpha_composite(im.convert('RGBA'));b=b.crop(box);b.thumbnail((355,420));b=b.resize((355,420));board.paste(b,(i*360,j*460+25));d.text((i*360+5,j*460+5),label,fill='white')
board.save(O/'mother-matte-review.png');print(json.dumps(report))
