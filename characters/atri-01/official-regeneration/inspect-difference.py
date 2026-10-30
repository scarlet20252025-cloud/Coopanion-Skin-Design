from pathlib import Path
import numpy as np, cv2
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent
m=np.array(Image.open(P.parent/'master.png').convert('RGBA'))
e=np.array(Image.open(P/'registered/mother-without-near-pony-01.png').convert('RGBA'))
ma=m[:,:,3]/255.;ea=e[:,:,3]/255.
d=np.max(np.abs(m[:,:,:3].astype(float)*ma[:,:,None]-e[:,:,:3]*ea[:,:,None]),axis=2)
region=np.zeros(d.shape,bool);region[295:960,130:390]=True
heat=np.zeros_like(m);heat[:,:,0]=255;heat[:,:,3]=np.uint8(np.clip(d*3,0,255))*region
board=Image.new('RGB',(1200,810),'#25252c');dr=ImageDraw.Draw(board)
for i,(name,im) in enumerate([('Mother',Image.fromarray(m)),('Removal edit',Image.fromarray(e)),('Difference',Image.fromarray(heat))]):
 b=Image.new('RGBA',im.size,'#c5c8d0');b.alpha_composite(im);b=b.crop((120,260,430,960)).resize((350,770));board.paste(b,(i*400,30));dr.text((i*400+10,8),name,fill='white')
board.save(P/'near-difference-diagnostic.png')
for t in [10,20,30,50]:
 sel=(d>t)&region&(ma>.1)
 print(t,int(sel.sum()))
