"""Assemble whole generated drawings only. No mother pixels, old body masks or painted repairs."""
from pathlib import Path
import json, hashlib, shutil
import cv2
import numpy as np
from PIL import Image

P = Path(__file__).resolve().parent.parent
ROOT = P.parents[2]
OLD = ROOT/'scratch/candidates/atri-hair-junctions'
OUT = ROOT/'scratch/candidates/atri-pure-components-01'
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'tex').mkdir(exist_ok=True)
W,H=1145,1374
identity=np.array([[1.,0,0],[0,1.,0]])
records=[]

def similarity(a,b):
    a,b=np.array(a,float),np.array(b,float)
    v,w=a[1]-a[0],b[1]-b[0]
    theta=np.arctan2(w[1],w[0])-np.arctan2(v[1],v[0])
    scale=np.linalg.norm(w)/np.linalg.norm(v)
    c,s=np.cos(theta),np.sin(theta)
    linear=scale*np.array([[c,-s],[s,c]])
    return np.column_stack((linear,b[0]-linear@a[0]))

def add(key, path, matrix=identity, z=0, pivot=None, role='fixed', clip=None, mask=None,
        exclude=None, keep_islands=False):
    source=np.array(Image.open(path).convert('RGBA'))
    if clip is not None:
        y0,y1=clip
        keep_rows=np.zeros(source.shape[0],bool); keep_rows[y0:y1+1]=True
        source[~keep_rows]=0
    n,labels,stats,_=cv2.connectedComponentsWithStats((source[:,:,3]>0).astype('uint8'))
    keep=1+int(np.argmax(stats[1:,4]))
    removed=int(((source[:,:,3]>0)&(labels!=keep)).sum())
    if not keep_islands:
        source[labels!=keep]=0 # Only detached islands, never redraw or erode retained alpha.
        removed=int(((np.array(Image.open(path).convert('RGBA'))[:,:,3]>0)&(labels!=keep)).sum())
    else:
        removed=0
    a=source.astype(np.float32)/255
    a[:,:,:3]*=a[:,:,3:4]
    a=cv2.warpAffine(a,matrix,(W,H),flags=cv2.INTER_LINEAR)
    if mask is not None:
        # The mask is given in canvas coordinates and is applied after the part's own transform, so a
        # measured row band stays the same band in the assembled character.
        mk=np.array(Image.open(mask).convert('RGBA'))[:,:,3]
        a[mk<=128]=0
    if exclude is not None:
        a[exclude]=0
    a[:,:,:3]=np.divide(a[:,:,:3],a[:,:,3:4],out=np.zeros_like(a[:,:,:3]),where=a[:,:,3:4]>1e-8)
    file='tex/'+key+'.png'
    pixels=np.uint8(np.clip(a*255,0,255).round())
    count,lab,st,_=cv2.connectedComponentsWithStats((pixels[:,:,3]>0).astype('uint8'))
    main=1+int(np.argmax(st[1:,4]))
    if keep_islands:
        post=0
    else:
        post=int(((pixels[:,:,3]>0)&(lab!=main)).sum())
        pixels[lab!=main]=0
    Image.fromarray(pixels).save(OUT/file)
    records.append(dict(id=key,file=file,z=z,pivot=pivot or [592,581],role=role,poses=['seated','dizzy'] if key=='seated-clean' else ['standing'],source=str(path.relative_to(ROOT)),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),matrix=matrix.tolist(),clip=clip,removed_detached_pixels=removed,removed_detached_after_registration=post,art_status='provisional diagnostic; not user accepted'))

# 2026-10-16 user review round 2: the near lock must be ONE COMPLETE lock (its occluded length must
# have content) and must not end in hair-thin tails. The user rejected pony-pair-left-01 and
# ponytail-left-01, and the fresh gpt-image-2.5 drawing (raw/ponytail-near-complete-05.png) came
# back as a hair-thin ribbon, so the near lock is now the left half of the complete pair drawing
# recovered from the original model (raw/ponytail-near-complete-06.png, from
# art-source/complete-ponytails-reextract.png; provenance in ponytail-near-complete-06-request.json).
# fit-locks.py places it by curve registration (outer profile onto the master silhouette, root
# reported against its bow, profile error 4.09px) and measures from the master's own pixels which
# rows show the lock in front (551-978): the whole lock sits in the back layer and only that band is
# repeated in front of the head hair, above the bow. The far lock placement is preserved unchanged
# because the user accepted it.
lock_fit=json.loads((P/'pure-generation/lock-placement.json').read_text(encoding='utf8'))
# 2026-10-16 user clarification: the version to keep is the one scratch/preview-current.png and
# qa/current (13:21) were rendered from. That build drew the near lock from
# raw/pony-pair-left-01.png with the recorded library fit (outer profile error 3.0px, far 8.9px) and
# put its rows above y=545 in front of the head hair. Restored exactly that way - no mask, no
# code-side alpha deletion. The only newer change kept is the near arm layer order (z=9).
FIT_LIBRARY=json.loads((ROOT/'scratch/asset-candidates-fit.json').read_text(encoding='utf8'))
near=np.array(FIT_LIBRARY['left-library']['matrix'],float)[:2]
far=np.array(FIT_LIBRARY['right-current']['matrix'],float)[:2]
NEAR_LOCK=ROOT/'characters/atri-01/official-regeneration/raw/pony-pair-left-01.png'
# 2026-10-16 user decision A: the lock's upper part covers the crown hair again (the front piece is no
# longer restricted to the rows head-clean leaves open), and the split to the back layer is moved down
# to the middle of the lock so the lower half sits under the hair ends.
NEAR_LOCK_FRONT_CLIP=(0,640)
rear=np.array([[.9,0,40],[0,.9,15]])
# 2026-10-16 user review: next to the left bow the head showed two parallel outlines, because
# rear-hair draws its own contour just outside the head's own contour (it is placed at 0.9 scale with
# a [40,15] shift, so the two never coincide). Ownership: the head's outline belongs to head-clean, so
# the thin sliver of rear-hair that lies just outside the head contour - within 8px - is trimmed.
# Rear hair that really hangs outside the head (the long side/back masses) is far outside that band
# and is not touched.
HEAD_ALPHA=np.array(Image.open(P/'registered/head-blank-01.png').convert('RGBA'))[:,:,3]>60
from scipy.ndimage import binary_fill_holes
# head-blank-01 keeps the face area transparent for the expression layers, so holes are filled first;
# otherwise "outside the head" would include the whole face and wipe the hair behind it.
HEAD_FILLED=binary_fill_holes(HEAD_ALPHA)
OUTSIDE_HEAD=cv2.distanceTransform((~HEAD_FILLED).astype('uint8'),cv2.DIST_L2,5)
HEAD_ROWS=np.zeros((1374,1145),bool);HEAD_ROWS[150:521]=True
# Narrowed 2026-10-16 after the contour-wide version emptied the band beside the face: now only 3px,
# and only over the crown-to-bow rows (y 150-360), so face height is never touched.
REAR_TRIM=(OUTSIDE_HEAD<=6)&(~HEAD_FILLED)&HEAD_ROWS
add('tail-left',NEAR_LOCK,near,-2,[370,300])
add('tail-left-front',NEAR_LOCK,near,6.05,[370,300],role='lock-front',clip=NEAR_LOCK_FRONT_CLIP)
add('tail-right',P/'raw/ponytail-far-complete-06.png',far,-1,[803,300])
add('rear-hair',P/'raw/rear-hair-complete-04.png',rear,0,exclude=REAR_TRIM)
add('leg-left',P/'registered/leg-left-02.png',z=1,pivot=[551,1090],role='leg')
add('leg-right',P/'registered/leg-right-01.png',z=2,pivot=[659,1090],role='leg')
far_arm=np.array(json.loads((P/'pure-generation/far-arm-placement.json').read_text())['matrix'])
add('arm-right',P/'raw/arm-far-complete-03.png',far_arm,4,[691,660])
add('body',P/'registered/torso-complete-03.png',z=5,pivot=[584,666])
# 2026-10-16 user instruction: the near arm must be drawn above EVERY hair layer (the raised hand was
# being crossed by hair). Hair layers are tail-left -2, tail-right -1, rear-hair 0, head-clean 6,
# tail-left-front 6.05 and ahoge 8, so the arm moves to 9 - above all of them, and below nothing that
# it needs to stay under. The far arm is left untouched: in the master it belongs behind the torso,
# and lifting it above the hair would put it in front of the body instead.
add('arm-left',P/'registered/arm-near-complete-02-clean.png',z=9,pivot=[520,650],role='wave-arm')
add('head-clean',P/'registered/head-blank-01.png',z=6)
add('bow-left',P/'registered/bow-left-01.png',z=6.1,pivot=[370,300])
add('bow-right',P/'registered/bow-right-01.png',z=6.2,pivot=[803,300])
add('ahoge',P/'registered/ahoge-01.png',z=8,pivot=[565,169])

# Fit the whole generated seated drawing to the existing seated coordinate contract.
src=np.array(Image.open(P/'raw/seated-whole-01.png').convert('RGBA'))
dst=np.array(Image.open(OLD/'tex/source-040.png').convert('RGBA'))
sift=cv2.SIFT_create(6000)
ka,da=sift.detectAndCompute(cv2.cvtColor(src[:,:,:3],cv2.COLOR_RGB2GRAY),(src[:,:,3]>230).astype('uint8')*255)
kb,db=sift.detectAndCompute(cv2.cvtColor(dst[:,:,:3],cv2.COLOR_RGB2GRAY),(dst[:,:,3]>230).astype('uint8')*255)
good=[m for m,n in cv2.BFMatcher().knnMatch(da,db,k=2) if m.distance<.65*n.distance]
a=np.float32([ka[m.queryIdx].pt for m in good]);b=np.float32([kb[m.trainIdx].pt for m in good])
matrix,inliers=cv2.estimateAffinePartial2D(a,b,method=cv2.RANSAC,ransacReprojThreshold=3)
assert matrix is not None and inliers.sum()>=12,'Seated drawing registration rejected'
e=np.linalg.norm(a@matrix[:,:2].T+matrix[:,2]-b,axis=1)[inliers.ravel()>0]
seat_report=dict(matrix=matrix.tolist(),inliers=int(inliers.sum()),rms=float(np.sqrt(np.mean(e**2))),max_residual=float(e.max()),status='registration only; expression placement and pose art need review')
(P/'pure-generation/seated-registration.json').write_text(json.dumps(seat_report,indent=2),encoding='utf8')
add('seated-clean',P/'raw/seated-whole-01.png',matrix,z=0,pivot=[588,1120])

lock=json.loads((P/'expression-lock.json').read_text(encoding='utf8'))
for file,sha in lock['files'].items():
    assert hashlib.sha256((OLD/file).read_bytes()).hexdigest()==sha, file
    if file.startswith('tex/'):
        shutil.copy2(OLD/file,OUT/file)
model=json.loads((OLD/'model.json').read_text(encoding='utf8'))
model['parts']=[{k:r[k] for k in ('id','file','z','pivot','role','poses')} for r in records]+lock['parts']
model['part_registration']={p['id']:[1,0,0,1,0,0] for p in model['parts']}
model['bounds']=[95,20,1045,1310]
model['words']=list(dict.fromkeys(model['words']))
# 2026-10-16 user instruction: bring the vocabulary up to the whale pack's list 1:1. The renderer
# forwards every word it knows to the official kit's native do(), and the kit draws the effects
# (heart/note/star/sweat/tear/spiral/ring/bubble) and the pointer themselves, so a word missing here
# simply never reaches them. Struggle already exists: mode==='drag' switches the face to flustered and
# adds a 15Hz shake to the hair/tuft.
WHALE_VOCAB=['bubble','heart','note','pointer','ring','spiral','star','sweat','tear',
             'drag','dragged','tremble']
model['words']=list(dict.fromkeys(list(model['words'])+WHALE_VOCAB))
model['pure_generation']={'provenance':'SOURCE.json','status':'diagnostic candidate; full art/motion acceptance pending'}
(OUT/'model.json').write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(OUT/'part-registration.json').write_text(json.dumps(model['part_registration'],indent=2)+'\n',encoding='utf8')
manifest=json.loads((OLD/'figure.json').read_text(encoding='utf8'))
manifest['name']['zh']='GPT 亚托莉 · 整件生成候选'
manifest['thumb']='tex/head-clean.png'
(OUT/'figure.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
source={'version':manifest['version'],'author':manifest['author'],'repository':manifest['homepage'],'method':'Only whole imagegen component drawings. Original approved expression art is the explicit exception. No mother pixel grafts, old cutout alphas, colour blending, outline restoration or mesh patches. Detached generated alpha islands removed mechanically; uniform similarity only.','status':'diagnostic; no installation or release','parts':records,'seated_registration':seat_report,'expression_files':{f:h for f,h in lock['files'].items() if f.startswith('tex/')},'hair_registration':'two anchor initial placements / rear initial uniform placement; no exact reconstruction claim','far_arm_correction':'Earlier visible-cuff-width assumption withdrawn. Full cuff is partly occluded by torso; assembly uses complete generated source50 behind complete generated torso.'}
(OUT/'SOURCE.json').write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
renderer=(OLD/'figure.js').read_text(encoding='utf8')
face=renderer[renderer.index(' function buildFace('):renderer.index('\n const figure=')]
(OUT/'figure.js').write_text((P/'pure-generation/renderer-template.js').read_text(encoding='utf8').replace('@@FACE@@',face),encoding='utf8')
(OUT/'EXPRESSION-PRESERVATION.json').write_text(json.dumps({'method':'buildFace/paintFace copied verbatim;26 accepted textures unchanged','source_renderer_sha256':hashlib.sha256((OLD/'figure.js').read_bytes()).hexdigest(),'copied_function_sha256':hashlib.sha256(face.encode()).hexdigest()},indent=2),encoding='utf8')
import runpy
runpy.run_path(str(P/'pure-generation/export-edges.py'),run_name='__main__')
print(json.dumps({'out':str(OUT),'whole_generated_parts':len(records),'preserved_expression_textures':len(source['expression_files']),'seated_fit':seat_report},indent=2))
