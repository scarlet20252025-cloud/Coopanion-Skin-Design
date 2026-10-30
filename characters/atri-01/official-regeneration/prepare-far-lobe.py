from pathlib import Path
from PIL import Image
import json,hashlib
P=Path(__file__).resolve().parent;R=P/'references/far-lobe';R.mkdir(exist_ok=True)
box=(810,680,1010,970);scale=2.7;offset=(242,120)
im=Image.open(P/'official-visible/far-visible-mother.png').convert('RGBA').crop(box).resize((540,783),Image.Resampling.LANCZOS)
out=Image.new('RGBA',(1024,1024));out.alpha_composite(im,offset);out.save(R/'target.png')
(R/'preparation.json').write_text(json.dumps({'crop':box,'scale':scale,'offset':offset,'input_sha256':hashlib.sha256((R/'target.png').read_bytes()).hexdigest()},indent=2)+'\n')
