from pathlib import Path
from PIL import Image,ImageDraw
import json,numpy as np
P=Path(__file__).resolve().parent;O=P/'official-visible'
im=Image.open(O/'far-visible-mother.png').convert('RGBA');mask=Image.new('L',im.size,0);d=ImageDraw.Draw(mask)
# Magenta denotes missing source area only, never delivered as artwork.
d.polygon([(795,294),(811,294),(823,410),(825,525),(817,565),(799,592),(779,577),(780,455),(779,355)],fill=255)
anchors=np.array(json.loads((O/'far-ownership.json').read_text())['left_boundary_yx'])
inner=[];outer=[]
for y in range(782,940):
 x=float(np.interp(y,anchors[:,0],anchors[:,1]));amount=26*min(1,(940-y)/20)
 inner.append((x-amount,y));outer.append((x+5,y))
d.polygon(inner+outer[::-1],fill=255)
im.paste((255,0,255,255),(0,0),mask)
im.save(O/'far-hidden-magenta-guide.png');mask.save(O/'far-hidden-request-mask.png')
