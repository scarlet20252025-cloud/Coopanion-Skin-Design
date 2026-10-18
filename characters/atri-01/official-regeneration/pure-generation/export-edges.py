"""Official-style transparent texel colour bleed. Alpha and opaque art are immutable."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

ROOT=Path(__file__).resolve().parents[4]
PACK=ROOT/'scratch/candidates/atri-pure-components-01'
source=json.loads((PACK/'SOURCE.json').read_text(encoding='utf8'))
reports=[]
for part in source['parts']:
    path=PACK/part['file'];a=np.array(Image.open(path).convert('RGBA'))
    before=a.copy();alpha_sha=hashlib.sha256(a[:,:,3].tobytes()).hexdigest()
    known=a[:,:,3]>=128
    distance,indices=distance_transform_edt(~known,return_indices=True)
    edge=(~known)&(distance<=6)
    yy,xx=indices
    a[edge,:3]=a[yy[edge],xx[edge],:3]
    assert np.array_equal(a[:,:,3],before[:,:,3])
    assert np.array_equal(a[known],before[known])
    Image.fromarray(a).save(path)
    reports.append(dict(id=part['id'],alpha_sha256=alpha_sha,alpha_changed_pixels=0,opaque_art_changed_pixels=0,
                        rgb_changed_pixels=int(np.any(a[:,:,:3]!=before[:,:,:3],axis=2).sum()),
                        file_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
report={'policy':'Reference kit outfit_assemble: bleed neighbouring opaque colours into transparent edge texels before filtering. Here only alpha<128, within6px; alpha byte-for-byte identical, all alpha>=128 RGBA unchanged. No masks from mother or shape edits. Approved expression textures excluded.', 'parts':reports}
(PACK/'EDGE-EXPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({'parts':len(reports),'alpha_changed_pixels':0,'opaque_art_changed_pixels':0,'edge_rgb_changes':sum(x['rgb_changed_pixels'] for x in reports)},indent=2))
