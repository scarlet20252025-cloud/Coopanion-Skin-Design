"""Incremental arm source and original-coordinate underpaint, preserving r03 motion."""
from pathlib import Path
import json,hashlib,sys,shutil,io,zipfile
import xml.etree.ElementTree as ET
import numpy as np,cv2
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];A=R/'characters/original-01';O=A/'rig-v005-r04';P=R/'packs/gpt-dragon-v005-r04'
lock=json.loads((A/'production-lock.json').read_text());src=R/lock['active_master'];assert hashlib.sha256(src.read_bytes()).hexdigest()==lock['sha256']
cfg=json.loads((O/'motion-config.json').read_text());meta=json.loads((P/'model.json').read_text());assert meta['master_sha256']==lock['sha256']
if '--motion-only' in sys.argv:
 for old,new in zip(meta['motion_rig']['arms'],cfg['arms'],strict=True):assert all(old.get(k)==new.get(k) for k in ['id','polygon','exclude_ellipses']), 'Mask changed; use full build'
 meta['motion_rig']=cfg;(P/'model.json').write_text(json.dumps(meta,indent=2)+'\n');print('Motion only; art reused');sys.exit(0)
m=np.array(Image.open(src).convert('RGBA'));e=np.array(Image.open(O/'arm-underpaint-edit.png').convert('RGBA'));assert e.shape==m.shape
reg=np.zeros(m.shape[:2],np.uint8);reg[170:570,390:900]=255;reg[m[:,:,3]<250]=0
gray=lambda a:cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2GRAY).astype('float32')/255
cc,warp=cv2.findTransformECC(gray(m),gray(e),np.eye(2,3,dtype='float32'),cv2.MOTION_TRANSLATION,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,100,1e-7),reg,5)
assert cc>.97 and abs(warp[:,2]).max()<8
e=cv2.warpAffine(e,warp,(m.shape[1],m.shape[0]),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP);Image.fromarray(e).save(O/'arm-underpaint-registered.png')
headmask=np.array(Image.open(A/'rig-v005-r02/head-visible-mask.png'))>0
base=np.array(Image.open(A/'rig-v005-r02/body-covered-underpaint.png'));legless=np.array(Image.open(A/'rig-v005-r03/body-without-legs.png'))
original=base.copy();union=np.zeros(m.shape[:2],bool);layers=[]
def save(name,a):
 Image.fromarray(a).save(O/(name+'.png'));shutil.copy2(O/(name+'.png'),P/'tex'/(name+'.png'))
for arm in cfg['arms']:
 maskim=Image.new('L',Image.fromarray(m).size);draw=ImageDraw.Draw(maskim);draw.polygon([tuple(p) for p in arm['polygon']],fill=255)
 for box in arm.get('exclude_ellipses',[]):draw.ellipse(box,fill=0)
 mask=(np.array(maskim)>0)&~headmask;Image.fromarray(mask.astype('uint8')*255).save(O/(arm['id']+'-mask.png'))
 union|=mask;part=original.copy();part[~mask]=0;save('arm-'+arm['id'],part);layers.append(('arm-'+arm['id'],part))
base[union]=0;legless[union]=0;patch=e.copy();patch[~union]=0
save('body-without-arms',base);save('body-without-limbs',legless);save('arm-hole-fill',patch)
rest=Image.fromarray(base)
for name,a in layers:rest=Image.alpha_composite(rest,Image.fromarray(a))
assert np.array_equal(np.array(rest),original)
report={'master_sha256':lock['sha256'],'rest_mismatches':0,'registration_correlation':cc,'translation':warp.tolist(),'motion':'pending','inherited_elasticity':meta['leg_rig']['elasticity']}
# Reuse approved eye pixels for a one-eye wink; never generate another face atlas.
for prefix in ['head','sitting']:
 opened=np.array(Image.open(P/'tex'/(prefix+'-open.png')));closed=np.array(Image.open(P/'tex'/(prefix+'-closed.png')))
 wink=opened.copy();wink[:,:730]=closed[:,:730];save(prefix+'-wink',wink)
 assert np.array_equal(wink[:,730:],opened[:,730:]) and np.array_equal(wink[:,:,3],opened[:,:,3])
meta['motion_rig']=cfg;meta['arm_checks']=report;(P/'model.json').write_text(json.dumps(meta,indent=2)+'\n');(O/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
tree=ET.Element('image',w=str(m.shape[1]),h=str(m.shape[0]),name='v005-r04 original-coordinate arm source');stack=ET.SubElement(tree,'stack')
with zipfile.ZipFile(O/'gpt-dragon-v005-r04-arms.ora','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for name,a,show in [('master-reference',m,False),('arm-hole-fill',patch,False),('body-without-arms',base,True)]+[(name,a,True) for name,a in layers]:
  b=io.BytesIO();Image.fromarray(a).save(b,format='PNG');p='data/'+name+'.png';z.writestr(p,b.getvalue());stack.insert(0,ET.Element('layer',name=name,src=p,x='0',y='0',opacity='1.0',visibility='visible' if show else 'hidden',**{'composite-op':'svg:src-over'}))
 z.writestr('stack.xml',ET.tostring(tree,encoding='utf-8',xml_declaration=True));b=io.BytesIO();rest.save(b,format='PNG');z.writestr('mergedimage.png',b.getvalue())
print(json.dumps(report,indent=2))
