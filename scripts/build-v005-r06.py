"""Register the generated waving palm, replace only its explicit local mask."""
from pathlib import Path
import json,hashlib,shutil
import cv2,numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];A=R/'characters/original-01';O=A/'rig-v005-r06';P=R/'packs/gpt-dragon-v005-r06'
lock=json.loads((A/'production-lock.json').read_text(encoding='utf-8'))
assert hashlib.sha256((R/lock['active_master']).read_bytes()).hexdigest()==lock['sha256']
src=np.array(Image.open(A/'rig-v005-r04/arm-left.png').convert('RGBA'));edit=np.array(Image.open(O/'wave-arm-edit.png').convert('RGBA'));assert src.shape==edit.shape
mask=np.zeros(src.shape[:2],np.uint8);mask[640:798,510:640]=255;mask[src[:,:,3]<250]=0
gray=lambda a:cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2GRAY).astype('float32')/255
cc,warp=cv2.findTransformECC(gray(src),gray(edit),np.eye(2,3,dtype='float32'),cv2.MOTION_TRANSLATION,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,100,1e-7),mask,5)
assert cc>.95 and abs(warp[:,2]).max()<8
edit=cv2.warpAffine(edit,warp,(1254,1254),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
cfg=json.loads((O/'wave-mask.json').read_text(encoding='utf-8'));maskim=Image.new('L',(1254,1254));ImageDraw.Draw(maskim).polygon([tuple(p) for p in cfg['polygon']],fill=255);maskim.save(O/'wave-hand-mask.png');region=np.array(maskim)>0
out=src.copy();out[region]=edit[region];assert np.array_equal(out[~region],src[~region])
Image.fromarray(out).save(O/'arm-wave.png');shutil.copy2(O/'arm-wave.png',P/'tex/arm-wave.png')
report={'master_sha256':lock['sha256'],'registration_correlation':cc,'translation':warp.tolist(),'outside_hand_mask_changes':0,'rest_arm':'unchanged r04 arm-left.png','review':'pending'}
(O/'wave-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
