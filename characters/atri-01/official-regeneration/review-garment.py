from pathlib import Path
import json,hashlib
import cv2,numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent
mother=Image.open(P.parent/'master.png').convert('RGBA')
new=Image.open(P/'registered/garment-connected-01.png').convert('RGBA')
board=Image.new('RGB',(1440,1110),'#303038');d=ImageDraw.Draw(board)
regions=[('Whole garment',(330,575,855,1145)),('Near shoulder',(430,610,565,760)),('Near cuff',(340,855,535,1010)),('Far cuff',(755,835,850,995)),('Collar and neck',(490,575,705,710)),('Hem',(395,1030,805,1145))]
for row,(name,box) in enumerate(regions):
 for col,(label,im,color) in enumerate([('Mother',mother,'#e8e2ef'),('New source',new,'#e8e2ef'),('New on dark',new,'#24242b')]):
  tile=Image.new('RGBA',(box[2]-box[0],box[3]-box[1]),color);tile.alpha_composite(im.crop(box));tile.thumbnail((465,155));x=col*480;y=row*185;board.paste(tile,(x,y+25));d.text((x+5,y+4),name+' / '+label,fill='white')
board.save(P/'garment-method-review.png')
# All three complete arrangements use generated art only. Mother is a separate reference.
parts=['ponytail-left-02','ponytail-right-05','rear-complete-01','leg-left-02','leg-right-01','garment-connected-01','ahoge-01','bow-right-01','head-01','bow-left-01']
assembly=Image.new('RGBA',mother.size)
for part in parts:assembly.alpha_composite(Image.open(P/'registered'/f'{part}.png').convert('RGBA'))
assembly.save(P/'assembly-connected.png')
full=Image.new('RGB',(1710,730),'#303038');fd=ImageDraw.Draw(full)
for i,(label,im,bg) in enumerate([('MOTHER',mother,'#e8e2ef'),('CONNECTED SOURCE - DIAGNOSTIC',assembly,'#e8e2ef'),('DARK - NOT ACCEPTED',assembly,'#24242b')]):
 tile=Image.new('RGBA',mother.size,bg);tile.alpha_composite(im);tile.thumbnail((560,680));full.paste(tile,(i*570,35));fd.text((i*570+6,10),label,fill='white')
full.save(P/'assembly-connected-review.png')
a=np.array(Image.open(P/'raw/garment-connected-01.png').convert('RGBA'));b=np.array(mother)
s=cv2.SIFT_create();ka,da=s.detectAndCompute(cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2GRAY),(a[:,:,3]>230).astype('uint8')*255)
mask=np.zeros(b.shape[:2],np.uint8);mask[580:1140,335:850]=255
kb,db=s.detectAndCompute(cv2.cvtColor(b[:,:,:3],cv2.COLOR_RGB2GRAY),mask)
good=[m for m,n in cv2.BFMatcher().knnMatch(da,db,k=2) if m.distance<.72*n.distance]
x=np.float32([ka[m.queryIdx].pt for m in good]);y=np.float32([kb[m.trainIdx].pt for m in good])
M=np.array(json.loads((P/'garment-connected-01-registration.json').read_text())['matrix']);err=np.linalg.norm(x@M[:,:2].T+M[:,2]-y,axis=1);valid=err<=3
coverage={}
for name,(x0,y0,x1,y1) in regions:
 sel=valid&(y[:,0]>=x0)&(y[:,0]<x1)&(y[:,1]>=y0)&(y[:,1]<y1);coverage[name]={'matches':int(sel.sum()),'rms':float(np.sqrt(np.mean(err[sel]**2))) if sel.any() else None}
report={'state':'diagnostic; whole source still requires visual acceptance and separate motion-parts validation','feature_coverage':coverage,'matching_points':y[valid].tolist(),'parts':parts,'source_sha256':hashlib.sha256((P/'raw/garment-connected-01.png').read_bytes()).hexdigest(),'no_legacy_art_in_assembly':True}
(P/'garment-method-review.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(coverage))
