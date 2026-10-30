"""Register complete generated components without recutting their alpha."""
from pathlib import Path
import json,argparse
import cv2,numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
arg=argparse.ArgumentParser();arg.add_argument('name');arg.add_argument('--box',nargs=4,type=int,required=True);arg.add_argument('--landmarks');a=arg.parse_args()
src=np.array(Image.open(HERE/'raw'/(a.name+'.png')).convert('RGBA'));mother=np.array(Image.open(HERE.parent/'master.png').convert('RGBA'))
srcgray=cv2.cvtColor(src[:,:,:3],cv2.COLOR_RGB2GRAY);dstgray=cv2.cvtColor(mother[:,:,:3],cv2.COLOR_RGB2GRAY)
mask=np.zeros(mother.shape[:2],np.uint8);x0,y0,x1,y1=a.box;mask[y0:y1,x0:x1]=255
sift=cv2.SIFT_create();k1,d1=sift.detectAndCompute(srcgray,(src[:,:,3]>230).astype('uint8')*255);k2,d2=sift.detectAndCompute(dstgray,mask)
pairs=cv2.BFMatcher().knnMatch(d1,d2,k=2) if d1 is not None and d2 is not None else []
good=[m for m,n in pairs if m.distance<.72*n.distance]
report={'name':a.name,'matching_features':len(good),'alpha_policy':'generated alpha only; similarity registration, no cutout','status':'unregistered'}
if len(good)>=4 or a.landmarks:
 p=np.float32([k1[m.queryIdx].pt for m in good]);q=np.float32([k2[m.trainIdx].pt for m in good]);M,inliers=(None,None)
 if len(good)>=4 and not a.landmarks:M,inliers=cv2.estimateAffinePartial2D(p,q,method=cv2.RANSAC,ransacReprojThreshold=3)
 if a.landmarks:
  lm=json.loads((HERE/a.landmarks).read_text());p=np.array(lm['source']);q=np.array(lm['target']);pc=p-p.mean(0);qc=q-q.mean(0)
  u,s,v=np.linalg.svd(pc.T@qc);rot=u@v;scale=s.sum()/(pc**2).sum();shift=q.mean(0)-scale*p.mean(0)@rot;M=np.column_stack((scale*rot.T,shift));inliers=np.ones((len(p),1),np.uint8);report['method']='manual source landmarks, least-squares similarity, all residuals retained'
 if M is not None and int(inliers.sum())>=(3 if a.landmarks else 4) and np.linalg.det(M[:,:2])>1e-5:
  use=inliers.ravel()>0;err=np.linalg.norm(p@M[:,:2].T+M[:,2]-q,axis=1)
  report.update(matrix=M.tolist(),inliers=int(use.sum()),rms=float(np.sqrt(np.mean(err[use]**2))),max_residual=float(err[use].max()),status='registered-needs-visual-review')
  premult=src.astype(np.float32)/255.;premult[:,:,:3]*=premult[:,:,3:4]
  warped=cv2.warpAffine(premult,M,(mother.shape[1],mother.shape[0]),flags=cv2.INTER_CUBIC)
  warped=np.clip(warped,0,1);warped[:,:,:3]=np.divide(warped[:,:,:3],warped[:,:,3:4],out=np.zeros_like(warped[:,:,:3]),where=warped[:,:,3:4]>1e-7)
  registered=np.uint8(np.clip(warped*255,0,255).round())
  out=HERE/'registered';out.mkdir(exist_ok=True);Image.fromarray(registered).save(out/(a.name+'.png'))
  frames=[('mother',mother),('generated aligned',registered)]
  overlay=Image.fromarray(registered);overlay.putalpha(overlay.getchannel('A').point(lambda x:int(x*.5)));mixed=Image.fromarray(mother);mixed.alpha_composite(overlay);frames.append(('50% overlay',np.array(mixed)))
  board=Image.new('RGB',(1140,500),'#303038');draw=ImageDraw.Draw(board)
  for i,(label,pixels) in enumerate(frames):
   im=Image.fromarray(pixels);bg=Image.new('RGBA',im.size,'#e8e2ef');bg.alpha_composite(im);bg.thumbnail((375,455));board.paste(bg,(i*380,35));draw.text((i*380+8,8),label,fill='white')
  board.save(HERE/(a.name+'-comparison.png'))
if report['status']=='unregistered':
 # A failed new registration must never silently leave an older raster usable.
 stale=HERE/'registered'/(a.name+'.png')
 if stale.exists():stale.unlink()
(HERE/(a.name+'-registration.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
