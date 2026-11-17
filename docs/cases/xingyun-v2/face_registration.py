"""Register edited face artwork to the original jaw without modifying the PNG."""
import cv2
import numpy as np
from PIL import Image


def main_shape(alpha):
    _,labels,stats,_=cv2.connectedComponentsWithStats((alpha>=96).astype(np.uint8))
    if len(stats)<2:
        raise ValueError("face.png has no opaque face")
    index=1+int(np.argmax(stats[1:,4]))
    return labels==index, int(stats[index,1]+stats[index,3]-1)


def registered_face(image, jaw_reference):
    face=np.array(image.convert("RGBA"))
    reference=np.asarray(jaw_reference.convert("RGBA"))
    core,bottom=main_shape(face[...,3])
    guide,chin=main_shape(reference[...,3])
    support=cv2.dilate(core.astype(np.uint8),np.ones((5,5),np.uint8))>0
    face[~support]=0
    if bottom<=chin+6:
        return Image.fromarray(face)

    y,x=np.indices(face.shape[:2],dtype=np.float32)
    progress=np.clip((y-550)/(chin-550),0,1)
    map_y=y+(bottom-chin)*progress*progress*(3-2*progress)
    alpha=face[...,3:4].astype(np.float32)/255
    premult=np.concatenate((face[...,:3]*alpha,alpha*255),axis=-1)
    mapped=cv2.remap(premult,x,map_y,cv2.INTER_LINEAR)
    mask=mapped[...,3].copy()
    color=np.divide(mapped[...,:3]*255,mask[...,None],
                    out=np.zeros_like(mapped[...,:3]),where=mask[...,None]>.1)

    # The reference is only a registration guide for the cheeks and chin.
    # Keep the painted skin from the edited file inside that contour.
    lower=np.clip((y-602)/24,0,1)
    contour=reference[...,3].astype(np.float32)
    mask=np.minimum(mask,255*(1-lower)+contour*lower)
    depth=cv2.distanceTransform(guide.astype(np.uint8),cv2.DIST_L2,5)
    edge=(depth<3)&(contour>0)&(y>=610)&(mask>0)
    weight=np.clip((3-depth)/2,0,1)*edge
    color=color*(1-weight[...,None])+reference[...,:3]*weight[...,None]
    return Image.fromarray(np.rint(np.clip(np.dstack((color,mask)),0,255)).astype(np.uint8))


def clear_original_mouth(image):
    """Remove baked lip pixels from a face used with separate mouth tiles."""
    face=np.array(image.convert("RGBA"))
    l,t,r,b=693,571,774,633
    patch=face[t:b,l:r]
    y,x=np.indices(patch.shape[:2])
    area=((x+l-733)/23)**2+((y+t-601)/12)**2<=1
    patch[...,:3]=cv2.inpaint(patch[...,:3].copy(),area.astype(np.uint8),4,cv2.INPAINT_TELEA)
    return Image.fromarray(face)
