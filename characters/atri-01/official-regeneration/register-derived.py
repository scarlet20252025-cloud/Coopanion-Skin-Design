"""Map a generated local edit through its unchanged source landmarks."""
from pathlib import Path
import json,sys
import cv2,numpy as np
from PIL import Image
P=Path(__file__).resolve().parent
name,reference=sys.argv[1:3]
a=np.array(Image.open(P/'raw'/f'{name}.png').convert('RGBA'))
b=np.array(Image.open(P/'raw'/f'{reference}.png').convert('RGBA'))
s=cv2.SIFT_create()
ka,da=s.detectAndCompute(cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2GRAY),(a[:,:,3]>230).astype('uint8')*255)
kb,db=s.detectAndCompute(cv2.cvtColor(b[:,:,:3],cv2.COLOR_RGB2GRAY),(b[:,:,3]>230).astype('uint8')*255)
good=[m for m,n in cv2.BFMatcher().knnMatch(da,db,k=2) if m.distance<.65*n.distance]
x=np.float32([ka[m.queryIdx].pt for m in good]);y=np.float32([kb[m.trainIdx].pt for m in good])
if len(good)<8:
 raise SystemExit(f'Registration rejected: only {len(good)} reliable source correspondences; no transform or raster written')
M,ins=cv2.estimateAffinePartial2D(x,y,method=cv2.RANSAC,ransacReprojThreshold=3)
assert M is not None and ins.sum()>=8, 'Insufficient unchanged reference features'
R=json.loads((P/f'{reference}-registration.json').read_text())
T=np.vstack((R['matrix'],[0,0,1]))@np.vstack((M,[0,0,1]));T=T[:2]
f=a.astype(np.float32)/255;f[:,:,:3]*=f[:,:,3:4]
w=cv2.warpAffine(f,T,(1145,1374),flags=cv2.INTER_CUBIC);w=np.clip(w,0,1)
w[:,:,:3]=np.divide(w[:,:,:3],w[:,:,3:4],out=np.zeros_like(w[:,:,:3]),where=w[:,:,3:4]>1e-7)
Image.fromarray(np.uint8(np.clip(w*255,0,255).round())).save(P/'registered'/f'{name}.png')
err=np.linalg.norm(x@M[:,:2].T+M[:,2]-y,axis=1)[ins.ravel()>0]
report={'name':name,'status':'registered-needs-whole-composition-review','reference':reference,'relative_matrix':M.tolist(),'matrix':T.tolist(),'reference_fit_rms':float(np.sqrt(np.mean(err**2))),'inliers':int(ins.sum()),'alpha_policy':'generated alpha; premultiplied uniform similarity only'}
(P/f'{name}-registration.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
