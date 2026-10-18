"""Assembled-silhouette comparison for the right lock candidates (the metric the user sees)."""
import importlib.util, json
from pathlib import Path
import numpy as np, cv2
from PIL import Image
spec=importlib.util.spec_from_file_location("fl","characters/atri-01/official-regeneration/pure-generation/fit-locks.py")
fl=importlib.util.module_from_spec(spec); spec.loader.exec_module(fl)
MA=fl.MA
PK="scratch/candidates/atri-pure-components-01/tex/"
ORDER=["rear-hair","leg-left","leg-right","arm-right","body","arm-left","head-clean","bow-left","bow-right","ahoge"]
acc=np.zeros(MA.shape,bool)
for pid in ORDER: acc|=np.array(Image.open(PK+pid+".png").convert("RGBA"))[:,:,3]>60
fits=json.load(open("scratch/asset-candidates-fit.json",encoding="utf8"))
def placed(rel,mat,side):
    a=np.array(Image.open(Path("characters/atri-01")/rel).convert("RGBA")).astype(np.float32)
    if a.shape[:2]!=(1374,1145):
        c=np.zeros((1374,1145,4),np.float32); h=min(a.shape[0],1374); w=min(a.shape[1],1145); c[:h,:w]=a[:h,:w]; a=c
    m=np.zeros((1374,1145),np.float32)
    mm=(a[:,:,3]>128).astype("uint8")
    if side<0: mm[:,560:]=0
    else: mm[:,:600]=0
    n,lab,st,_=cv2.connectedComponentsWithStats(mm)
    keep=1+int(np.argmax(st[1:,4])); m=(lab==keep).astype(np.float32)
    M=np.array(mat,float)[:2].astype(np.float32)
    return cv2.warpAffine(m,M,(1145,1374),flags=cv2.INTER_NEAREST)>0.5
def score(tag,rel,mat,side):
    comp=acc.copy()|placed(rel,mat,side)
    x0,x1=(0,520) if side<0 else (620,1145)
    err=0; red=0; blue=0
    for y in range(400,1000):
        c=np.nonzero(comp[y,x0:x1])[0]; m=np.nonzero(MA[y,x0:x1])[0]
        if len(c) and len(m): err+=abs((c.min() if side<0 else c.max())-(m.min() if side<0 else m.max()))
    red=int((MA&~comp)[400:1000,x0:x1].sum()); blue=int((comp&~MA)[400:1000,x0:x1].sum())
    print("  %-26s profile_err_sum %6d  master_only %6d  candidate_only %6d"%(tag,err,red,blue))
print("RIGHT lock candidates")
for key,rel in [("right-current","official-regeneration/raw/ponytail-far-complete-06.png"),
                ("right-library","art-source/complete-ponytails-v1.png"),
                ("right-new08","official-regeneration/raw/ponytail-far-complete-08.png"),
                ("right-new07","official-regeneration/raw/ponytail-far-complete-07.png")]:
    score(key,rel,fits[key]["matrix"],+1)
print("LEFT lock candidates")
for key,rel in [("left-current","official-regeneration/raw/ponytail-near-complete-04.png"),
                ("left-library","official-regeneration/raw/pony-pair-left-01.png")]:
    score(key,rel,fits[key]["matrix"],-1)
