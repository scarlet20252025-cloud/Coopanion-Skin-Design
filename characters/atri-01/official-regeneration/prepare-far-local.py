"""Reference crop only: no new artwork or contour patches."""
from pathlib import Path
from PIL import Image
import hashlib,json
P=Path(__file__).resolve().parent
R=P/'references/far-local-v3';R.mkdir(parents=True,exist_ok=True)
box=(700,250,1030,990)
for name,src in [('target',P/'official-visible/far-visible-mother.png'),('mother-context',P.parent/'master.png')]:
    im=Image.open(src).convert('RGBA').crop(box)
    # Uniform enlargement, transparent square padding, explicit reversible placement.
    im=im.resize((396,888),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',(1024,1024));canvas.alpha_composite(im,(314,68))
    canvas.save(R/(name+'.png'))
record={'method':'crop reference, uniform scale and padding only','mother_crop_box':box,'scale':1.2,'padding_xy':[314,68],'output_size':[1024,1024], 'inverse_to_mother':[1/1.2,0,0,1/1.2,700-314/1.2,250-68/1.2], 'sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in R.glob('*.png')}}
(R/'preparation.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record))
