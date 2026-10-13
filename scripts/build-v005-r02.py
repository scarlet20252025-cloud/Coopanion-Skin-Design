"""Registered v005 pose/eye edits and conservative head/neck articulation study.

Original visible pixels are retained. Generated pixels are used only in explicit
eye masks, sitting differences, and covered head/neck underpaint regions.
"""
from pathlib import Path
import json,hashlib,io,zipfile
import xml.etree.ElementTree as ET
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'characters/original-01';OLD=ART/'layers-v005-r01';OUT=ART/'rig-v005-r02'
lock=json.loads((ART/'production-lock.json').read_text(encoding='utf-8'));src=ROOT/lock['active_master']
assert hashlib.sha256(src.read_bytes()).hexdigest()==lock['sha256']
m=np.array(Image.open(src).convert('RGBA'));h,w=m.shape[:2]
reports=[]
def save(name,a):Image.fromarray(a).save(OUT/(name+'.png'))
def register(name,region):
    e=np.array(Image.open(OUT/(name+'-edit.png')).convert('RGBA'));assert e.shape==m.shape
    mask=np.zeros((h,w),np.uint8);x0,y0,x1,y1=region;mask[y0:y1,x0:x1]=255;mask[(m[:,:,3]<240)|(e[:,:,3]<240)]=0
    gray=lambda a:cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2GRAY).astype('float32')/255
    cc,warp=cv2.findTransformECC(gray(m),gray(e),np.eye(2,3,dtype='float32'),cv2.MOTION_TRANSLATION,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,100,1e-7),mask,5)
    assert cc>.97 and np.max(abs(warp[:,2]))<8
    e=cv2.warpAffine(e,warp,(w,h),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
    reports.append({'edit':name,'correlation':cc,'translation':warp.tolist(),'unchanged_region':region});save(name+'-registered',e);return e
half=register('blink-half',[400,200,920,420]);sit=register('sit',[380,80,925,575])
roi=Image.open(OLD/'blink-edit-mask.png').convert('L');ra=np.array(roi);blend=np.minimum(ra,np.array(roi.filter(ImageFilter.GaussianBlur(2))))/255
eye_half=m.copy();eye_half[:,:,:3]=np.round(m[:,:,:3]*(1-blend[:,:,None])+half[:,:,:3]*blend[:,:,None]).astype('uint8')
closed=np.array(Image.open(OLD/'blink-closed-v005.png').convert('RGBA'))
eyes={'open':m,'half':eye_half,'closed':closed}
for name,a in eyes.items():
    assert np.array_equal(a[ra==0],m[ra==0]);assert np.array_equal(a[:,:,3],m[:,:,3])
    save('standing-'+name,a)

# Clean isolated ownership specks; this changes masks only, never the master.
hm=np.array(Image.open(OLD/'head-visible-mask.png'))>0
for value in [True,False]:
    mask=((hm==value)&(m[:,:,3]>16)).astype('uint8')
    n,lab,stats,_=cv2.connectedComponentsWithStats(mask,8)
    for i in range(1,n):
        if stats[i,cv2.CC_STAT_AREA]<180:hm[lab==i]=not value
hm[:560]=True;hm[920:]=False
head_visible=m.copy();head_visible[~hm]=0
body_visible=m.copy();body_visible[hm]=0
save('head-visible-mask',hm.astype('uint8')*255)
head_raw=np.array(Image.open(OLD/'head-isolation-registered.png').convert('RGBA'))
body_raw=np.array(Image.open(OLD/'body-underpaint-registered.png').convert('RGBA'))
# New hidden pixels are strictly under opaque original pixels of the other group.
back=head_raw.copy();back[(m[:,:,3]<255)|hm]=0
base=body_raw.copy();base[(m[:,:,3]<255)|~hm]=0
base=np.array(Image.alpha_composite(Image.fromarray(base),Image.fromarray(body_visible)))
save('hair-covered-underpaint',back);save('body-covered-underpaint',base)
for name,a in eyes.items():
    head=a.copy();head[~hm]=0;save('head-'+name,head)
rest=Image.alpha_composite(Image.alpha_composite(Image.fromarray(back),Image.fromarray(base)),Image.fromarray(head_visible))
r=np.array(rest);visible=m[:,:,3]>0
assert np.array_equal(r[visible],m[visible]);assert np.array_equal(r[:,:,3],m[:,:,3])
rest.save(OUT/'standing-rest-reassembled.png')

# Sitting edit changes lower pose; restore exact master head/face above y=580.
# A narrow blend in the unchanged hair/neck band prevents a horizontal seam.
mix=np.clip((np.arange(h)-580)/40,0,1)[:,None,None]
sit=np.round(m*(1-mix)+sit*mix).astype('uint8')
for name,a in eyes.items():
    out=sit.copy();out[ra>0]=a[ra>0];save('sitting-'+name,out)
save('sitting-difference-mask',np.any(sit!=m,axis=2).astype('uint8')*255)
assert np.array_equal(sit[:580],m[:580])
opaque=lambda a:Image.fromarray(a[:,:,3]).point(lambda v:255 if v>64 else 0).getbbox()
feet_stand=opaque(m)[3];feet_sit=opaque(sit)[3]
meta={'master_sha256':lock['sha256'],'canvas':[w,h],'registrations':reports,'rest_pixel_mismatches':0,'outside_eye_changes':0,'sitting_preserved_head_rows':[0,579],'standing_feet_y':feet_stand,'sitting_feet_y':feet_sit,'head_pivot':[670,615],'rotation_limit_degrees':2.5,'head_translation_limit_px':3,'independent_scaling':False,'checks':{'rest':'passed','blink_roi':'passed','sitting_head_identity':'passed','motion':'pending-visual-preview','desktop':'not-tested'}}
(OUT/'geometry.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
layers=[('hair-covered-underpaint',back,True),('body-covered-underpaint',base,True),('head-open',head_visible,True),('sitting-open',sit,False),('head-half',np.array(Image.open(OUT/'head-half.png')),False),('head-closed',np.array(Image.open(OUT/'head-closed.png')),False)]
root=ET.Element('image',w=str(w),h=str(h),name='v005-r02 head neck and pose study');stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(OUT/'gpt-dragon-v005-r02.ora','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
    for name,a,show in layers:
        b=io.BytesIO();Image.fromarray(a).save(b,format='PNG');path=f'data/{name}.png';z.writestr(path,b.getvalue());stack.insert(0,ET.Element('layer',name=name,src=path,x='0',y='0',opacity='1.0',visibility='visible' if show else 'hidden',**{'composite-op':'svg:src-over'}))
    z.writestr('stack.xml',ET.tostring(root,encoding='utf-8',xml_declaration=True));b=io.BytesIO();rest.save(b,format='PNG');z.writestr('mergedimage.png',b.getvalue())
print(json.dumps(meta,ensure_ascii=False,indent=2))
