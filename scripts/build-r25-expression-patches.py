"""Register imagegen edits and export local face patches; never paint new pixels."""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'characters/original-01/rig-v005-r25/drag-expression'
TEX = ROOT / 'packs/gpt-dragon-v005-r25/tex'
base = Image.open(TEX / 'head-closed.png').convert('RGBA')
reference = np.array(Image.open(SRC / 'eye-edit-input.png').convert('RGBA'))
reports = {}

def registered(name):
    edit = np.array(Image.open(SRC / name).convert('RGBA').resize((340,245),Image.Resampling.LANCZOS))
    mask = np.zeros((245,340),np.uint8)
    mask[0:30,:] = 255
    mask[60:115,:] = 255
    gray = lambda a: cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2GRAY).astype('float32')/255
    score,warp = cv2.findTransformECC(gray(reference),gray(edit),np.eye(2,3,dtype='float32'),cv2.MOTION_TRANSLATION,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,100,1e-6),mask,5)
    assert score>.92 and np.max(abs(warp[:,2]))<2, (score,warp)
    aligned = cv2.warpAffine(edit,warp,(340,245),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
    reports[name]={'correlation':score,'translation':warp.tolist()}
    out = Image.new('RGBA',base.size);out.paste(Image.fromarray(aligned),(520,350))
    return out

def patch(edit,polygons,name):
    mask=Image.new('L',base.size);d=ImageDraw.Draw(mask)
    for polygon in polygons:d.polygon(polygon,fill=255)
    a=np.minimum(np.array(mask),np.array(mask.filter(ImageFilter.GaussianBlur(1.4))))
    edit.putalpha(Image.fromarray(a));edit.save(TEX/name);mask.save(SRC/(name+'-mask.png'))

eyes=registered('squeezed-edit.png')
mask=Image.new('L',base.size);d=ImageDraw.Draw(mask)
for poly in [[(540,473),(568,460),(651,470),(690,493),(696,517),(659,537),(573,535),(540,510)],[(761,490),(793,477),(839,477),(852,498),(843,536),(774,532),(758,514)]]:d.polygon(poly,fill=255)
a=np.array(mask)
b=np.array(base);e=np.array(eyes);out=b.copy()
# Gradient-domain compositing matches generated skin to the existing cheek color.
# Separate each eye so the unchanged hair between them is never part of a blend.
count,labels=cv2.connectedComponents(a)
for i in range(1,count):
    local=np.uint8(labels==i)*255
    selection=local>0
    x,y,w,h=cv2.boundingRect(local)
    merged=cv2.seamlessClone(e[:,:,:3].copy(),out[:,:,:3].copy(),local.copy(),(x+w//2,y+h//2),cv2.NORMAL_CLONE)
    out[selection,:3]=merged[selection]
assert np.array_equal(out[a==0],b[a==0])
Image.fromarray(out).save(TEX/'head-flustered.png')
Image.fromarray(out).save(TEX/'sitting-flustered.png')
patch(registered('brow-clean-edit.png'),[[(606,380),(653,378),(688,389),(686,412),(649,405),(605,414)],[(774,380),(824,381),(843,397),(839,413),(776,410)]],'brow-underpaint.png')
(SRC/'registration.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
print(json.dumps(reports))
