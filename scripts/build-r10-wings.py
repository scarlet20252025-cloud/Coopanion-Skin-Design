"""Registered generated underpaint + deterministic original-pixel wing separation."""
from pathlib import Path
import json, shutil, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageChops
R=Path(__file__).resolve().parents[1]
P=R/'packs/gpt-dragon-v005-r10'; OLD=R/'packs/gpt-dragon-v005-r09'
OUT=R/'characters/original-01/rig-v005-r10'
source=Path(r'C:\Users\63526\.codex\generated_images\01a13400-0fec-79a2-9cdc-067895581192\exec-b8919d6e-87b2-46d6-be58-9e5e5079a99f.png')
shutil.copy2(source,OUT/'wingless-generated.png')
parts=[{'id':'left','root':[567,721],'polygon':[[276,805],[276,605],[514,605],[512,690],[552,719],[569,703],[601,720],[591,779],[554,752],[536,765],[516,803],[493,777],[472,770],[450,780],[429,806],[420,779],[400,757],[373,748],[345,751],[313,778]]},
 {'id':'right','root':[797,724],'polygon':[[797,722],[822,635],[1000,635],[1000,830],[947,784],[929,773],[909,775],[894,790],[884,813],[865,787],[842,776],[814,795],[799,772],[774,767],[774,738]]}]
combined=Image.open(OLD/'tex/body-without-limbs.png').convert('RGBA')
# Restore the already-painted wing root hidden under the sleeve, not the sleeve itself.
combined=Image.alpha_composite(Image.open(OLD/'tex/arm-hole-fill.png').convert('RGBA'),combined)
union=Image.new('L',combined.size)
wing_alpha=Image.new('L',combined.size)
for part in parts:
 mask=Image.new('L',combined.size);ImageDraw.Draw(mask).polygon([tuple(p) for p in part['polygon']],fill=255)
 union=ImageChops.lighter(union,mask)
 wing=combined.copy();wing.putalpha(ImageChops.multiply(wing.getchannel('A'),mask));wing.save(P/f"tex/wing-{part['id']}.png")
 wing_alpha=ImageChops.lighter(wing_alpha,wing.getchannel('A'))
 mask.save(OUT/f"wing-{part['id']}-mask.png")
# The generated edit preserves source geometry. Resample once to the locked canvas.
gen=Image.open(source).convert('RGBA').resize(combined.size,Image.Resampling.LANCZOS)
under=gen.copy();under.putalpha(ImageChops.multiply(gen.getchannel('A'),wing_alpha));under.save(P/'tex/wing-underpaint.png')
for name in ['body-covered-underpaint','body-without-legs','body-without-arms','body-without-limbs','arm-hole-fill']:
 im=Image.open(OLD/f'tex/{name}.png').convert('RGBA');im.putalpha(ImageChops.multiply(im.getchannel('A'),ImageChops.invert(union)));im.save(P/f'tex/{name}.png')
cfg={'parts':parts,'cycles':4,'angle_degrees':9,'fold':.10,'source':'v005 existing body + existing sleeve underpaint; wings contain no arm texture','underpaint':'built-in imagegen wing removal, only original wing alpha admitted'}
model=json.loads((P/'model.json').read_text(encoding='utf-8'));model['wing_rig']=cfg
(P/'model.json').write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'wing-rig.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Built isolated left/right wing textures and restricted hair underpaint')
