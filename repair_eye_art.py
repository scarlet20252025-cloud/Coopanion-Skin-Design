"""Register complete painted face expressions to the approved master."""

import cv2
import numpy as np


FACE_BOX = (435,420,799,654)
MOODS = (
    ("gentle-smile",("happy","love")),
    ("annoyed",("angry",)),
    ("surprised",("surprised",)),
    ("shy",("shy",)),
    ("sad",("sad",)),
    ("confused",("confused",)),
    ("sleepy",("sleepy",)),
    ("dragged",("dragged",)),
)


def rgba(rgb, alpha):
    a = np.uint8(np.rint(np.clip(alpha,0,1)*255))
    return np.dstack((np.where(a[:,:,None]>0,np.uint8(np.rint(np.clip(rgb,0,255))),0),a))


def smooth(value):
    k = np.clip(value,0,1)
    return k*k*(3-2*k)


def register_face_box(original, painting):
    l,t,r,b = FACE_BOX
    source = original[t:b,l:r,:3]
    generated = cv2.resize(painting[:,:,:3],(r-l,b-t),interpolation=cv2.INTER_AREA)
    anchors = np.full((b-t,r-l),255,np.uint8)
    anchors[39:180,40:352] = 0
    anchors[182:224,200:284] = 0

    def grey(image):
        return cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)

    score,matrix = cv2.findTransformECC(
        grey(source),grey(generated),np.eye(2,3,dtype=np.float32),cv2.MOTION_AFFINE,
        (cv2.TERM_CRITERIA_COUNT|cv2.TERM_CRITERIA_EPS,90,1e-5),anchors,3)
    if score < .98:
        raise ValueError(f"Expression is misregistered: {score:.4f}")
    paint = cv2.warpAffine(generated,matrix,(r-l,b-t),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,
                           borderMode=cv2.BORDER_REPLICATE)
    return paint,float(score),cv2.invertAffineTransform(matrix)


def register_mood(original, painting):
    paint,score,_ = register_face_box(original,painting)
    return paint,score


def complexion(portrait):
    """Measure the same two cheek areas below the eyes in every aligned key."""
    l,t,_,_ = FACE_BOX
    samples = np.concatenate(
        [portrait[593-t:607-t,x-l:x+34-l,:3].reshape(-1,3) for x in (586,690)])
    skin = (samples[:,0]>225)&(samples[:,1]>179)&(samples[:,2]>172)
    if np.count_nonzero(skin)<200:
        raise ValueError("The aligned face does not cover its cheek samples")
    return np.median(samples[skin],axis=0)


def expression_palette(master, load):
    moods = [register_mood(master,load(f"work/face-repair/mood-{name}.png")) for name,_ in MOODS]
    target = np.median([complexion(paint) for paint,_ in moods],axis=0)
    return target,moods


def match_complexion(portrait, source, target):
    """Move only existing skin tones toward the approved expression palette."""
    rgb = portrait[:,:,:3].astype(np.float32)
    red,green,blue = rgb.transpose(2,0,1)
    warmth = red-blue
    weight = (smooth((red-170)/52)*smooth((green-121)/56)*smooth((blue-115)/56)*
              smooth((warmth-7)/12)*smooth((73-warmth)/25))
    adjusted = np.rint(np.clip(rgb+(target-source)*weight[:,:,None],0,255))
    result = portrait.copy()
    result[:,:,:3] = adjusted.astype(np.uint8)
    return result


def match_head_skin(layer, source, target):
    result = layer.copy()
    l,t,r,b = FACE_BOX
    # Continue past the sampling rectangle to include the entire jaw and neck overlap.
    result[t:b+20,l:r] = match_complexion(layer[t:b+20,l:r],source,target)
    return result


def mouth_support(portrait):
    """Find lip pigment in a safe part of the cheek, away from hair and chin."""
    left,top,_,_ = FACE_BOX
    region = np.s_[597-top:631-top,644-left:700-left]
    red,green,_ = portrait[region].astype(np.int16).transpose(2,0,1)
    pigment = (green<191)&(red-green>22)
    mask = np.zeros(portrait.shape[:2],np.uint8)
    mask[region] = pigment.astype(np.uint8)
    if not mask.any():
        raise ValueError("The painted mouth is missing")
    return cv2.dilate(mask,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))


def speech_frames(base, open_mouth):
    """Deform just the regenerated lip pigment on each continuous face."""
    _,top,_,_ = FACE_BOX
    mask = mouth_support(open_mouth)
    clean_donor = cv2.inpaint(open_mouth,mask,3,cv2.INPAINT_TELEA)
    weight = smooth((cv2.distanceTransform(mask,cv2.DIST_L2,5)-1)/2)
    pigment = (open_mouth.astype(np.float32)-clean_donor)*weight[:,:,None]
    clean_base = cv2.inpaint(base,mouth_support(base),3,cv2.INPAINT_TELEA)
    y,x = np.indices(mask.shape,dtype=np.float32)
    center = 615-top
    frames = [base]
    for opening in (.42,.69,1):
        paint = cv2.remap(pigment,x,center+(y-center)/opening,cv2.INTER_LINEAR)
        frames.append(np.uint8(np.rint(np.clip(clean_base+paint,0,255))))
    return frames
