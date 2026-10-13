"""Mask a registered imagegen blink edit into locked v005; never redraw elsewhere."""
from pathlib import Path
import json,hashlib
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'characters/original-01';OUT=ART/'layers-v005-r01'
lock=json.loads((ART/'production-lock.json').read_text(encoding='utf-8'));src=ROOT/lock['active_master']
assert hashlib.sha256(src.read_bytes()).hexdigest()==lock['sha256']
m=np.array(Image.open(src).convert('RGBA'));e=np.array(Image.open(OUT/'blink-edit.png').convert('RGBA'));h,w=m.shape[:2]
assert e.shape==m.shape
mask=np.zeros((h,w),np.uint8);mask[200:420,400:920]=255;mask[(m[:,:,3]<240)|(e[:,:,3]<240)]=0
gray=lambda a:cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2GRAY).astype('float32')/255
cc,warp=cv2.findTransformECC(gray(m),gray(e),np.eye(2,3,dtype='float32'),cv2.MOTION_TRANSLATION,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,100,1e-7),mask,5)
assert cc>.97 and np.max(abs(warp[:,2]))<8
e=cv2.warpAffine(e,warp,(w,h),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
roi=Image.new('L',(w,h));d=ImageDraw.Draw(roi)
d.polygon([(538,423),(671,418),(701,454),(706,534),(662,551),(574,544),(538,503)],fill=255)
d.polygon([(756,427),(828,421),(854,449),(853,538),(802,552),(755,536)],fill=255)
# Feather inside the explicit ROI only, keeping every outside pixel unchanged.
a=np.array(roi);a=np.minimum(a,np.array(roi.filter(ImageFilter.GaussianBlur(2))))/255
out=m.copy();out[:,:,:3]=np.round(m[:,:,:3]*(1-a[:,:,None])+e[:,:,:3]*a[:,:,None]).astype('uint8')
Image.fromarray(out).save(OUT/'blink-closed-v005.png');roi.save(OUT/'blink-edit-mask.png')
assert np.array_equal(out[a==0],m[a==0]);assert np.array_equal(out[:,:,3],m[:,:,3])
report={'master_sha256':lock['sha256'],'translation':warp.tolist(),'registration_correlation':cc,'changed_pixels_outside_eye_roi':0,'alpha_changed':False,'scope':'closed-eye local expression candidate; not a finished blink curve'}
(OUT/'blink-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
