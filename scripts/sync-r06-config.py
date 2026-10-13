"""Motion-only update: no image regeneration."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];A=R/'characters/original-01';P=R/'packs/gpt-dragon-v005-r06/model.json'
m=json.loads(P.read_text(encoding='utf-8'));cfg=json.loads((A/'rig-v005-r06/motion-config.json').read_text(encoding='utf-8'))
assert cfg['arms']==m['motion_rig']['arms'],'Masks/anchors require an explicit source rebuild'
m['motion_rig']=cfg;m['secondary_rig']=json.loads((A/'rig-v005-r05/secondary-config.json').read_text(encoding='utf-8'))
m['behavior_rig']=json.loads((A/'rig-v005-r06/behavior-config.json').read_text(encoding='utf-8'))
P.write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8');print('Motion parameters updated; all images reused')
