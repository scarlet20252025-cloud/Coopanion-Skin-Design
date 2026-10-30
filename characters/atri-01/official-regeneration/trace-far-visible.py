from pathlib import Path
import json
import cv2,numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;O=P/'official-visible'
m=np.array(Image.open(O/'mother-source-matte.png').convert('RGBA'))
e=np.array(Image.open(P/'registered/mother-without-far-pony-01.png').convert('RGBA'))
h,w=m.shape[:2];ys=np.arange(h);xx=np.arange(w)[None,:]
anchors=np.array([[590,795],[615,805],[640,822],[665,842],[690,855],[715,862],[740,867],[765,870],[785,870],[800,883],[825,901],[850,920],[875,933],[900,936],[925,930],[935,928],[945,936],[960,940]],float)
xp=np.interp(ys,anchors[:,0],anchors[:,1])
coverage=np.clip(xx-xp[:,None]+.5,0,1);coverage[(ys<590)|(ys>960)]=0
# Visible upper pony is behind short cheek hair. Difference alpha distinguishes
# it from the separate, unchanged pointed cheek bang above/right of it.
for y in range(510,590):
 row=((m[y,790:860,3]>180)&(e[y,790:860,3]<60)).astype('uint8')
 n,l,s,_=cv2.connectedComponentsWithStats(row.reshape(1,-1))
 if n>1:
  k=1+np.argmax(s[1:,cv2.CC_STAT_AREA])
  if s[k,cv2.CC_STAT_AREA]>=3:
   x=790+int(s[k,cv2.CC_STAT_LEFT]);r=x+int(s[k,cv2.CC_STAT_WIDTH]);coverage[y,x-2:r+3]=1
# Slit is genuine transparency; put the boundary there and retain all ink.
for y in range(600,786):
 row=(m[y,770:990,3]>100).astype('uint8')
 n,l,s,_=cv2.connectedComponentsWithStats(row.reshape(1,-1))
 groups=[k for k in range(1,n) if s[k,cv2.CC_STAT_AREA]>=8]
 if len(groups)>=2:
  k=groups[-1];prev=groups[-2]
  start=770+s[k,cv2.CC_STAT_LEFT];end=770+s[prev,cv2.CC_STAT_LEFT]+s[prev,cv2.CC_STAT_WIDTH]
  cut=(start+end)/2;coverage[y]=np.clip(xx[0]-cut+.5,0,1)
part=m.copy();part[:,:,3]=np.uint8(m[:,:,3]*coverage+.5);part[part[:,:,3]==0,:3]=0
Image.fromarray(part).save(O/'far-visible-mother.png');Image.fromarray(np.uint8(coverage*255+.5)).save(O/'far-ownership-mask.png')
(O/'far-ownership.json').write_text(json.dumps({'source':'mother-source-matte.png','removal_edit':'../registered/mother-without-far-pony-01.png','left_boundary_yx':anchors.tolist(),'root':'alpha difference excludes unchanged cheek bang','status':'visible source only, concealed completion pending'},indent=2)+'\n',encoding='utf-8')
board=Image.new('RGB',(900,700),'#292932');d=ImageDraw.Draw(board)
for i,(im,bg) in enumerate([(Image.fromarray(m),'#e8e2ef'),(Image.fromarray(part),'#e8e2ef'),(Image.fromarray(part),'#202128')]):
 b=Image.new('RGBA',im.size,bg);b.alpha_composite(im);b=b.crop((765,500,995,970)).resize((295,650));board.paste(b,(300*i,30));d.text((300*i+5,8),['Mother','Far visible','Dark background'][i],fill='white')
board.save(O/'far-visible-source-review.png')
