"""Correct ownership of the removal difference against the locked mother's ink.

These are semantic boundary landmarks in the original source, not new ink.
Exterior alpha and every RGB pixel come from the mother. Hidden regions are absent.
"""
from pathlib import Path
import json
import cv2,numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;O=P/'official-visible'
m=np.array(Image.open(O/'mother-source-matte.png').convert('RGBA'));h,w=m.shape[:2]
# Right boundary follows narrow lock, then the foreground rear-hair occlusion.
anchors=np.array([[302,373],[325,376],[350,376],[375,375],[400,371],[425,365],[450,358],[475,350],[500,341],[525,330],[550,315],[575,297],[600,278],[625,258],[650,246],[675,239],[700,235],[725,234],[750,235],[775,240],[795,248],[800,245],[825,228],[850,215],[875,204],[900,196],[920,194],[930,190],[940,187]],float)
ys=np.arange(h);xp=np.interp(ys,anchors[:,0],anchors[:,1]);xx=np.arange(w)[None,:]
# Snap the contact edge to the source's dark ink, preserving its full width.
lum=m[:,:,:3].mean(2)
for y in range(310,540):
 c=int(round(xp[y]));lo=max(0,c-6);hi=min(w,c+9)
 ink=lo+int(np.argmin(lum[y,lo:hi]));xp[y]=ink+2.5
xp[310:540]=cv2.GaussianBlur(xp[310:540].reshape(-1,1),(1,7),1).ravel()
# In the open slit, place ownership boundary in transparency, not through ink.
for y in range(540,790):
 c=int(round(xp[y]));void=np.flatnonzero(m[y,max(c-6,0):c+14,3]<8)
 if len(void):xp[y]=max(c-6,0)+void[0]+1
# Ownership uncertainty around the same-colour root is resolved from mother ink.
coverage=np.clip(xp[:,None]+.5-xx,0,1)
coverage[(ys<302)|(ys>940)]=0
for y in range(302,340):
 left=373-(y-302)*1.11
 coverage[y]*=np.clip(xx[0]-left+.5,0,1)
part=m.copy();part[:,:,3]=np.uint8(m[:,:,3]*coverage+.5);part[part[:,:,3]==0,:3]=0
Image.fromarray(part).save(O/'near-visible-mother.png')
Image.fromarray(np.uint8(coverage*255+.5)).save(O/'near-ownership-mask.png')
(O/'near-ownership.json').write_text(json.dumps({'source':'../master.png','initial_difference':'near-difference-mask.png','correction':'mother ink landmarks; bow belongs foreground, broad inner strand excluded','right_boundary_yx':anchors.tolist(),'hidden_content':'not yet generated','status':'visible source only, not a complete component'},indent=2)+'\n',encoding='utf-8')
board=Image.new('RGB',(900,1000),'#25252c');d=ImageDraw.Draw(board)
for i,(im,bg) in enumerate([(Image.fromarray(m),'#e8e2ef'),(Image.fromarray(part),'#e8e2ef'),(Image.fromarray(part),'#25252c')]):
 b=Image.new('RGBA',im.size,bg);b.alpha_composite(im);b=b.crop((130,280,400,950)).resize((294,730));board.paste(b,(i*300,35))
 d.text((i*300+5,10),['Mother','Visible mother pixels','Dark background'][i],fill='white')
board.crop((0,0,900,770)).save(O/'near-visible-source-review.png')
