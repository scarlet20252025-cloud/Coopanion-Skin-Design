"""Incremental leg extraction: v005 pixels, editable polygons, local underpaint only."""
from pathlib import Path
import json,hashlib,shutil,zipfile,io
import xml.etree.ElementTree as ET
import cv2,numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];A=R/'characters/original-01';O=A/'rig-v005-r03';P=R/'packs/gpt-dragon-v005-r03'
lock=json.loads((A/'production-lock.json').read_text());src=R/lock['active_master'];assert hashlib.sha256(src.read_bytes()).hexdigest()==lock['sha256']
m=np.array(Image.open(src).convert('RGBA'));e=np.array(Image.open(O/'skirt-underpaint-edit.png').convert('RGBA'));assert e.shape==m.shape
mask=np.zeros(m.shape[:2],np.uint8);mask[200:900,350:920]=255;mask[m[:,:,3]<250]=0
gray=lambda x:cv2.cvtColor(x[:,:,:3],cv2.COLOR_RGB2GRAY).astype('float32')/255
cc,warp=cv2.findTransformECC(gray(m),gray(e),np.eye(2,3,dtype='float32'),cv2.MOTION_TRANSLATION,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,100,1e-7),mask,5)
assert cc>.97 and abs(warp[:,2]).max()<8
e=cv2.warpAffine(e,warp,(m.shape[1],m.shape[0]),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
Image.fromarray(e).save(O/'skirt-underpaint-registered.png')
cfg=json.loads((O/'leg-config.json').read_text());union=np.zeros(m.shape[:2],bool)
def save(name,a):
 Image.fromarray(a).save(O/(name+'.png'));shutil.copy2(O/(name+'.png'),P/'tex'/(name+'.png'))
legs=[]
for leg in cfg['legs']:
 maskim=Image.new('L',Image.fromarray(m).size);draw=ImageDraw.Draw(maskim);draw.polygon([tuple(p) for p in leg['polygon']],fill=255);draw.rectangle(leg['boot_bounds'],fill=255);maskim.save(O/(leg['id']+'-mask.png'))
 mask=np.array(maskim)>0;union|=mask;part=m.copy();part[~mask]=0;save('leg-'+leg['id'],part);legs.append(part)
front=np.array(Image.open(A/'rig-v005-r02/body-covered-underpaint.png'));original=front.copy();front[union]=0;save('body-without-legs',front)
patch=e.copy();patch[~union]=0;save('skirt-hole-fill',patch)
# Pixel identity is tested without underpaint; underpaint is hidden at rest.
rest=front.copy()
for leg in legs:rest=np.array(Image.alpha_composite(Image.fromarray(rest),Image.fromarray(leg)))
assert np.array_equal(rest,original)
meta=json.loads((P/'model.json').read_text());meta['leg_rig']=cfg;meta['leg_checks']={'master':lock['sha256'],'rest_mismatch':0,'underpaint_region':'union of explicit leg polygons only','registration_correlation':cc,'translation':warp.tolist(),'motion':'pending'}
(O/'validation.json').write_text(json.dumps(meta['leg_checks'],indent=2)+'\n');(P/'model.json').write_text(json.dumps(meta,indent=2)+'\n')
tree=ET.Element('image',w=str(m.shape[1]),h=str(m.shape[0]),name='v005-r03 original-coordinate leg source');stack=ET.SubElement(tree,'stack')
layers=[('master-reference',m,False),('skirt-hole-fill',patch,False),('leg-left',legs[0],True),('leg-right',legs[1],True),('body-without-legs',front,True)]
with zipfile.ZipFile(O/'gpt-dragon-v005-r03-legs.ora','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for name,a,show in layers:
  buf=io.BytesIO();Image.fromarray(a).save(buf,format='PNG');path='data/'+name+'.png';z.writestr(path,buf.getvalue());stack.insert(0,ET.Element('layer',name=name,src=path,x='0',y='0',opacity='1.0',visibility='visible' if show else 'hidden',**{'composite-op':'svg:src-over'}))
 z.writestr('stack.xml',ET.tostring(tree,encoding='utf-8',xml_declaration=True));buf=io.BytesIO();Image.fromarray(rest).save(buf,format='PNG');z.writestr('mergedimage.png',buf.getvalue())
print(json.dumps(meta['leg_checks'],indent=2))
