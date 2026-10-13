"""Register local isolation edits and retain master pixels in all visible layers.

This produces an editable decomposition study, NOT an animation-ready rig.
Generated occlusion fills remain hidden until their seams have been inspected.
"""
from pathlib import Path
import json,hashlib,io,zipfile
import xml.etree.ElementTree as ET
import cv2
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'characters/original-01'
OUT=ART/'layers-v005-r01'
lock=json.loads((ART/'production-lock.json').read_text(encoding='utf-8'))
source=ROOT/lock['active_master']
if hashlib.sha256(source.read_bytes()).hexdigest()!=lock['sha256']:raise SystemExit('Master hash mismatch; stopped.')
m=np.array(Image.open(source).convert('RGBA'));h,w=m.shape[:2]
def grey(a):return cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2GRAY).astype('float32')/255
def register(filename,region):
    im=np.array(Image.open(OUT/filename).convert('RGBA'))
    if im.shape!=m.shape:raise ValueError('Edit canvas changed: no independent resize permitted.')
    mask=np.zeros((h,w),np.uint8);x0,y0,x1,y1=region;mask[y0:y1,x0:x1]=255
    mask[(m[:,:,3]<240)|(im[:,:,3]<240)]=0
    mask=cv2.erode(mask,np.ones((5,5),np.uint8))
    warp=np.eye(2,3,dtype='float32')
    cc,warp=cv2.findTransformECC(grey(m),grey(im),warp,cv2.MOTION_TRANSLATION,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,100,1e-7),mask,5)
    if abs(warp[0,2])>8 or abs(warp[1,2])>8 or cc<.97:raise ValueError('Registration requires review')
    registered=cv2.warpAffine(im,warp,(w,h),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT)
    Image.fromarray(registered).save(OUT/filename.replace('-edit','-registered'))
    return registered,{'file':filename,'transform':'translation only','matrix':warp.tolist(),'correlation':cc,'unchanged_region':region}
head,head_reg=register('head-isolation-edit.png',[380,80,925,575])
body,body_reg=register('body-underpaint-edit.png',[420,885,905,1190])
# Classify by the closest registered edit, never use its changed visible pixels.
def distance(a):
    diff=np.mean(abs(a[:,:,:3].astype(float)-m[:,:,:3]),axis=2)
    return diff+(255-a[:,:,3])*2
head_mask=(distance(head)<distance(body)).astype(np.uint8)
head_mask[:560]=1;head_mask[920:]=0
head_mask=cv2.medianBlur(head_mask,5)
head_mask=(head_mask>0)&(m[:,:,3]>0)
visible_head=m.copy();visible_head[~head_mask]=0
visible_body=m.copy();visible_body[head_mask]=0
layers=[('body-visible-master',visible_body,True),('head-visible-master',visible_head,True)]
for name,a,_ in layers:Image.fromarray(a).save(OUT/f'{name}.png')
Image.fromarray(head_mask.astype('uint8')*255).save(OUT/'head-visible-mask.png')
merged=Image.alpha_composite(Image.fromarray(visible_body),Image.fromarray(visible_head))
merged.save(OUT/'reassembled.png')
a=np.array(merged);v=m[:,:,3]>0
changed=int(np.count_nonzero(np.any(a[v]!=m[v],axis=1)))
if changed:raise ValueError(f'Visible master pixels changed: {changed}')
# Occlusion candidates are preserved but deliberately hidden in editable source.
all_layers=[('body-underpaint-candidate',body,False),('hair-underpaint-candidate',head,False),*layers]
root=ET.Element('image',w=str(w),h=str(h),name='v005 same-coordinate layer study')
stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(OUT/'gpt-dragon-v005-layer-study.ora','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
    for name,pixels,visible in all_layers:
        buf=io.BytesIO();Image.fromarray(pixels).save(buf,format='PNG');src=f'data/{name}.png';z.writestr(src,buf.getvalue())
        stack.insert(0,ET.Element('layer',name=name,src=src,x='0',y='0',opacity='1.0',visibility='visible' if visible else 'hidden',**{'composite-op':'svg:src-over'}))
    z.writestr('stack.xml',ET.tostring(root,encoding='utf-8',xml_declaration=True));buf=io.BytesIO();merged.save(buf,format='PNG');z.writestr('mergedimage.png',buf.getvalue())
report={'master':lock['active_master'],'master_sha256':lock['sha256'],'canvas':[w,h],'offset':[0,0],'independent_resizing':False,'registrations':[head_reg,body_reg],'visible_pixel_mismatches':changed,'alpha_mismatches':int(np.count_nonzero(a[:,:,3]!=m[:,:,3])),'layer_scope':'head+hair and body visible ownership study; not final rig parts','underpaint':'hidden candidates; seams and articulation not accepted','animation_ready':False}
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
