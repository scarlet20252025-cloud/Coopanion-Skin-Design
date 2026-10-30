"""Reverse the recorded reference crop and actual output canvas scale."""
from pathlib import Path
from PIL import Image
import cv2,numpy as np,json
P=Path(__file__).resolve().parent
src=np.asarray(Image.open(P/'raw/far-lobe-complete-01.png').convert('RGBA'),np.float32)/255
assert src.shape[0]==src.shape[1]
output_scale=src.shape[0]/1024
s=1/(2.7*output_scale);M=np.array([[s,0,810-242/2.7],[0,s,680-120/2.7]],np.float64)
src[:,:,:3]*=src[:,:,3:4]
g=cv2.warpAffine(src,M,(1145,1374),flags=cv2.INTER_CUBIC);g=np.clip(g,0,1)
g[:,:,:3]=np.divide(g[:,:,:3],g[:,:,3:4],out=np.zeros_like(g[:,:,:3]),where=g[:,:,3:4]>1e-6)
Image.fromarray(np.uint8(g*255+.5)).save(P/'registered/far-lobe-complete-01.png')
(P/'far-lobe-complete-01-registration.json').write_text(json.dumps({'method':'inverse recorded reference crop plus uniform output canvas scale; not a feature fit','matrix':M.tolist(),'status':'requires visual geometry review','automatic_feature_matches':1,'automatic_fit_rejected':True,'no_affine_shape_correction':True},indent=2)+'\n')
