"""Reassign the actual rear-curtain ink to foreground before testing hidden fill.

All visible pixels remain mother pixels. Concealed donor uses a recorded rigid
translation, not a contour warp. This is a new diagnostic, not an acceptance.
"""
from pathlib import Path
import json,sys
import cv2,numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;O=P/'official-visible';reverse='--reverse' in sys.argv;latest='--latest' in sys.argv;safe_overlap='--safe-overlap' in sys.argv;internal_matte='--internal-matte' in sys.argv;registered_overlap='--registered-overlap' in sys.argv;boundary_exact='--boundary-exact' in sys.argv;poisson='--poisson' in sys.argv;N=P/('gradient-underlap-review' if poisson else 'boundary-continuous-review' if boundary_exact else 'registered-underlap-review' if registered_overlap else 'internal-matte-review' if internal_matte else 'reverse-removal-safe-review' if safe_overlap else 'reverse-removal-v3-review' if latest else 'reverse-removal-review' if reverse else 'ownership-corrected');N.mkdir(exist_ok=True)
def read(p):return np.asarray(Image.open(p).convert('RGBA'),np.float32)/255
def pm(a):
 a=a.copy();a[:,:,:3]*=a[:,:,3:4];return a
def st(a):
 a=a.copy();a[:,:,:3]=np.divide(a[:,:,:3],a[:,:,3:4],out=np.zeros_like(a[:,:,:3]),where=a[:,:,3:4]>1e-6);return np.clip(a,0,1)
def save(n,a):Image.fromarray(np.uint8(st(a)*255+.5)).save(N/n)
def over(a,b):return a+b*(1-a[:,:,3:4])
m=read(O/'mother-source-matte.png');h,w=m.shape[:2];yy,xx=np.mgrid[:h,:w]
c1=np.asarray(Image.open(O/'near-ownership-mask.png'),np.float32)/255
c2=np.asarray(Image.open(O/'far-ownership-mask.png'),np.float32)/255
# Reference is the right edge of the actual foreground ink, not the taupe
# interior 8-20 px farther to its right. Continue through the natural tip slit.
anchors=np.array([[786,874],[800,876],[825,891],[850,905],[875,915],[900,924],[910,926],[920,928],[925,929],[930,930],[935,932],[940,934],[945,936],[960,940]],np.float32)
cuts=np.interp(np.arange(h),anchors[:,0],anchors[:,1])
c2[786:961]=np.clip(xx[786:961]-cuts[786:961,None]+.5,0,1)
v=m.copy();v[:,:,3]*=c2;v[v[:,:,3]==0,:3]=0
Image.fromarray(np.uint8(c2*255+.5)).save(N/'far-ownership-mask.png');save('far-visible-mother.png',pm(v))
donor=pm(read(P/'registered/far-lobe-complete-01.png'))
donor=cv2.warpAffine(donor,np.array([[1,0,-18],[0,1,0]],np.float32),(w,h),flags=cv2.INTER_CUBIC)
hidden=((yy>=800)&(yy<=928)).astype(np.float32)*(1-c2)
if reverse or latest:
 source_name='mother-without-far-rear-03' if latest else 'mother-without-far-rear-01'
 g=read(P/('registered/'+source_name+'.png'))
 # The complete pony is separated from body by real transparency below y600.
 # Select that connected semantic source, not the torso or a broad rectangle.
 roi=(yy>=600)&(yy<1060)&(xx>770)&(xx<1000)
 n,labels,stats,_=cv2.connectedComponentsWithStats(((g[:,:,3]>.1)&roi).astype('uint8'))
 label=labels[890,960]
 assert label>0 and stats[label,cv2.CC_STAT_AREA]>1000
 component=(labels==label).astype('uint8')
 # Include low-alpha edge pixels only when adjacent to this same component.
 component=cv2.dilate(component,np.ones((3,3),np.uint8)).astype(np.float32)*roi
 donor=pm(g)*component[:,:,None]
 if registered_overlap:
  # This is a separately registered concealed drawing, not a replacement of
  # any mother-visible pixels. Keep its complete generated alpha geometry.
  a=donor[:,:,3];core=cv2.erode((a>.2).astype('uint8'),np.ones((5,5),np.uint8))>0
  straight=st(donor);straight[core,3]=1;donor=pm(straight)
  donor=cv2.warpAffine(donor,np.array([[1,0,-18],[0,1,0]],np.float32),(w,h),flags=cv2.INTER_CUBIC)
  g=st(donor)
 save('generated-pony-semantic-source.png',donor)
 hidden=((yy>=790)&(yy<1050)).astype(np.float32)*(1-c2)
 if (safe_overlap or registered_overlap) and not poisson:
  # Generated material may only enter a concealed area. Protect the mother's
  # genuine negative space between the tips and foreground curtain.
  if not registered_overlap:hidden[yy>930]*=(m[:,:,3][yy>930]>.99)
  # Color registration only: transfer low-frequency boundary mismatch into the
  # concealed overlap. Neither alpha nor visible mother pixels are repainted.
  d=np.zeros((h,1,3),np.float32)
  for y in range(800,931):
   x=int(cuts[y])+4
   if g[y,x,3]>.98 and m[y,x,3]>.98:
    d[y,0]=np.clip(m[y,x,:3]-g[y,x,:3],-.3,.3)
  d=cv2.GaussianBlur(d,(1,15),3).reshape(h,1,3)
  distance=np.maximum(cuts[:,None]-xx,0)
  strength=np.exp(-distance/20)[:,:,None]
  protect=np.clip((g[:,:,:3].mean(2)-.28)/.18,0,1)[:,:,None]
  if boundary_exact:
   for y in range(800,931):
    x=int(np.ceil(cuts[y]));d[y,0]=m[y,x,:3]-g[y,x,:3] if g[y,x,3]>.98 and m[y,x,3]>.98 else 0
   # Boundary value matching is local. Do not average ink colors between rows
   # or spread a dark tip sample into the adjacent pale cel-shaded plane.
   strength=np.exp(-distance/8)[:,:,None]
   edge_distance=cv2.distanceTransform((g[:,:,3]>.2).astype('uint8'),cv2.DIST_L2,5)
   protect=np.clip((edge_distance-1)/2,0,1)[:,:,None]
  corrected=g.copy();corrected[:,:,:3]=np.clip(g[:,:,:3]+d*strength*protect,0,1)
  donor=pm(corrected) if registered_overlap else pm(corrected)*component[:,:,None]
 if poisson:
  # Known right boundary = original visible pony RGB. Known left boundary =
  # the complete generated concealed drawing, not the foreground curtain.
  source_rgb=np.uint8(np.clip(g[:,:,:3]*255+.5,0,255))
  destination_rgb=source_rgb.copy();known=v[:,:,3]>.99
  destination_rgb[known]=np.uint8(m[known,:3]*255+.5)
  selection=((g[:,:,3]>.99)&(yy>=800)&(yy<936)&(xx>cuts[:,None]-30)&(xx<cuts[:,None]+4)).astype('uint8')*255
  sx,sy,sw,sh=cv2.boundingRect(selection);center=(sx+sw//2,sy+sh//2)
  corrected_rgb=cv2.seamlessClone(source_rgb,destination_rgb,selection,center,cv2.NORMAL_CLONE).astype(np.float32)/255
  corrected=g.copy();corrected[:,:,:3]=corrected_rgb;donor=pm(corrected)
  Image.fromarray(selection).save(N/'color-registration-mask.png')
removed_speckles=0
contribution=donor*hidden[:,:,None]
if registered_overlap:
 n,lab,stats,_=cv2.connectedComponentsWithStats((contribution[:,:,3]>.1).astype('uint8'))
 small=np.zeros((h,w),np.uint8)
 for k in range(1,n):
  if stats[k,cv2.CC_STAT_AREA]<10:
   small[lab==k]=1
 small=(cv2.dilate(small,np.ones((3,3),np.uint8))>0)&(contribution[:,:,3]<.45)
 removed_speckles=int(((contribution[:,:,3]>0)&small).sum());contribution[small]=0
far=pm(v)+contribution
near=pm(read(O/'near-pony-complete.png'))
pa=read(O/'near-visible-mother.png')[:,:,3]+v[:,:,3]
fa=np.divide(m[:,:,3]-pa,1-pa,out=np.zeros_like(pa),where=(1-pa)>1e-6)
fg=m.copy();fg[:,:,3]=np.clip(fa,0,1);fg=pm(fg)
shared_edge_pixels=0
if registered_overlap:
 # Internal AA has a complete opaque background now. The external-alpha
 # complement formula would incorrectly restore these foreground pixels to
 # opacity 1. Use actual coverage and un-mat RGB against this known background.
 mixed=(c2>.001)&(c2<.999)&(m[:,:,3]>.99)&(far[:,:,3]>.999)&(yy>=790)&(yy<931)
 a=1-c2[mixed]
 color=m[mixed,:3]-far[mixed,:3]*c2[mixed,None]
 fg[mixed,:3]=np.clip(color,0,a[:,None]);fg[mixed,3]=a
 shared_edge_pixels=int(mixed.sum())
matte_rows=[]
if internal_matte:
 rgb=m[:,:,:3];lum=rgb.mean(2)
 centers={};differences={}
 for y in range(800,931):
  prediction=int(cuts[y])-4;left=max(0,prediction-7);right=min(w,prediction+5)
  edge=left+int(np.argmin(lum[y,left:right]));centers[y]=edge
  if m[y,edge+6,3]>.99 and g[y,edge+6,3]>.99 and lum[y,edge+6]>.62:
   differences[y]=rgb[y,edge+6]-g[y,edge+6,:3]
 assert len(differences)>10
 keys=np.array(list(differences));values=np.array(list(differences.values()))
 offsets=np.stack([np.interp(np.arange(h),keys,values[:,k]) for k in range(3)],axis=1)
 offsets=cv2.GaussianBlur(offsets.reshape(h,1,3),(1,15),3).reshape(h,3)
 for y in range(800,931):
  edge=centers[y]
  if m[y,edge+9,3]<.99 or g[y,edge+6,3]<.99:continue
  ink=rgb[y,edge];delta=offsets[y]
  # Complete the rear hair's background independently under its foreground ink.
  # Visible background pixels beyond the original ink remain original pixels.
  for x in range(max(0,edge-35),edge+6):
   if donor[y,x,3]<.99:continue
   b=np.clip(g[y,x,:3]+delta,0,1)
   far[y,x]=np.r_[b,1]
  for x in range(edge,edge+6):
   if m[y,x,3]<.99:continue
   b=far[y,x,:3];c=rgb[y,x];direction=ink-b
   alpha=float(np.clip(np.dot(c-b,direction)/max(np.dot(direction,direction),1e-6),0,1))
   lower=np.maximum(np.maximum(1-c/np.maximum(b,1e-6),0),np.maximum((c-b)/np.maximum(1-b,1e-6),0)).max()
   alpha=max(alpha,float(lower))
   if x>=edge+4 and np.abs(c-b).max()<.035:
    far[y,x,:3]=c;alpha=0
   if alpha<1e-5:fg[y,x]=0
   else:
    color=np.clip((c-(1-alpha)*far[y,x,:3])/alpha,0,1)
    fg[y,x]=np.r_[color*alpha,alpha]
  matte_rows.append([y,edge])
 save('internal-matte-foreground.png',fg)
safe=cv2.erode((m[:,:,3]>.98).astype('uint8'),np.ones((7,7),np.uint8)).astype(np.float32)
fill=pm(read(P/'registered/mother-without-near-pony-01.png'))*(c1*safe)[:,:,None]
fill=over(pm(read(P/'registered/mother-without-far-pony-01.png'))*(c2*safe)[:,:,None],fill)
save('far-pony-complete.png',far);save('pair-remainder.png',fg);save('pair-rear-fill.png',fill)
def move(p,a,start,end):
 t=np.clip((yy-start)/(end-start),0,1).astype(np.float32);f=t*t*(3-2*t)
 return np.clip(cv2.remap(p,(xx-a*f).astype(np.float32),yy.astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT),0,1)
def render(a):return over(fg,over(move(near,-a,430,910),over(move(far,a,800,940),fill)))
states=[('Mother',pm(m))]+[(str(n)+'px',render(n)) for n in [0,6,-6,12,-12]]
for label,box,size in [('full',(0,0,w,h),(280,340)),('lower',(840,750,995,970),(300,440)),('root',(775,470,890,670),(300,440))]:
 board=Image.new('RGB',(size[0]*6,(size[1]+30)*2),'#292932');d=ImageDraw.Draw(board)
 for j,bg in enumerate(['#e8e2ef','#202128']):
  for i,(name,a) in enumerate(states):
   im=Image.fromarray(np.uint8(st(a)*255+.5));b=Image.new('RGBA',(w,h),bg);b.alpha_composite(im);b=b.crop(box);scale=min(size[0]/b.width,size[1]/b.height);b=b.resize((round(b.width*scale),round(b.height*scale)),Image.Resampling.LANCZOS);board.paste(b,(i*size[0],j*(size[1]+30)+30));d.text((i*size[0]+8,j*(size[1]+30)+8),name,fill='white')
 board.save(N/(label+'.png'))
for n in [0,6,-6,12,-12]:save('frame-'+str(n)+'.png',render(n))
neutral=render(0)
report={'status':'UNREVIEWED; diagnostic only','donor':'../registered/far-lobe-complete-01.png','donor_rigid_translation':[-18,0],'reason':'hidden clearance only; donor visible alpha is never used to replace the mother contour','boundary_yx':anchors.tolist(),'foreground_owns':'actual rear-curtain outline, not the adjacent pony interior','far_bend_window':[800,940],'far_tie_root':[805,295],'near_bend_window':[430,910],'neutral_premultiplied_mae':float(np.abs(neutral-pm(m)).mean()),'outside_alpha_pixels':int(((neutral[:,:,3]>.1)&(m[:,:,3]<.05)).sum()),'promotion_allowed':False}
if reverse or latest:report.update(donor='../registered/'+source_name+'.png',donor_rigid_translation=[0,0],reason='Generated pony exposed by removing its foreground curtain from full mother. Connected source alpha retained; no donor translation or shape correction.')
if safe_overlap:report.update(negative_space_protection='new concealed pixels excluded from original visible tip gaps below y930; inspect for dynamic truncation',color_registration='low-frequency RGB correction inside concealed overlap only; alpha unchanged by color correction')
if registered_overlap:report.update(donor_rigid_translation=[-18,0],opaque_core='5x5 erosion of generated alpha>.2 set to opaque; boundary alpha retained',reason='Independent concealed source registration against occlusion clearance; full generated contour retained, no clipping to mother silhouette, all visible pixels from mother',color_registration='low-frequency boundary RGB offset inside concealed overlap',removed_disconnected_speckle_pixels=removed_speckles,shared_internal_AA_pixels=shared_edge_pixels)
if boundary_exact:report['color_registration']='Per-row boundary RGB match, exponential 8px decay into concealed overlap; generated outline protected, visible mother pixels untouched'
if poisson:report['color_registration']='OpenCV NORMAL_CLONE gradient-domain color registration; original visible pony is the right boundary and generated concealed hair is the left boundary; only concealed RGB consumed, source alpha/contour unchanged'
if internal_matte:report.update(internal_matte='foreground ink alpha estimated against independent background, foreground RGB un-matted to reproduce mother; no opaque-complement formula on the internal AA edge',matte_rows=matte_rows)
(N/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
