"""Build complete portrait frames from the master-matched blink paintings."""

import cv2
import numpy as np

from repair_eye_art import FACE_BOX, complexion, match_complexion, register_mood, rgba, smooth


# Upper lash and lower aperture from the three registered paintings.
# Each eye has its own geometry and fixed left-to-right sample positions.
LIDS = {
    "near": (
        [503,520,540,560,580,600,620,638,651],
        [[519,522,519,521,523,526,534,543,550],
         [522,528,531,534,537,540,543,547,550],
         [526,533,540,547,550,550,550,550,551]],
        [[522,532,552,567,573,574,570,554,552],
         [525,535,546,559,564,565,563,553,552],
         [529,541,550,556,558,557,556,554,553]],
    ),
    "far": (
        [705,713,722,734,746,758,769,779],
        [[548,542,537,532,529,525,525,528],
         [547,546,543,539,537,534,530,528],
         [554,553,550,550,548,543,536,531]],
        [[553,565,578,578,569,551,538,530],
         [551,560,570,569,566,555,541,533],
         [558,558,557,555,554,550,541,534]],
    ),
}


def deform_y(x, y, a, b, p):
    """Warp one full portrait toward the intermediate eyelid geometry."""
    x0,y0,_,_ = FACE_BOX
    result = y.copy()
    for xs, top, bottom in LIDS.values():
        src_top = np.interp(x+x0,xs,top[a])-y0
        src_bottom = np.interp(x+x0,xs,bottom[a])-y0
        dst_top = src_top*(1-p)+(np.interp(x+x0,xs,top[b])-y0)*p
        dst_bottom = src_bottom*(1-p)+(np.interp(x+x0,xs,bottom[b])-y0)*p
        above = y + (src_top-dst_top)*smooth((y-dst_top+18)/18)
        below = y + (src_bottom-dst_bottom)*smooth((dst_bottom+19-y)/19)
        inside = src_top+(src_bottom-src_top)*np.clip((y-dst_top)/np.maximum(1,dst_bottom-dst_top),0,1)
        remapped = np.where(y<dst_top,above,np.where(y>dst_bottom,below,inside))
        weight = smooth((x+x0-xs[0]+11)/11)*smooth((xs[-1]+11-x-x0)/11)
        result += (remapped-y)*weight
    return result


def tween_portraits(keys, clean):
    h,w = keys[0].shape[:2]
    y,x = np.indices((h,w),dtype=np.float32)
    # Freeze the solid foreground hair's motion. All color in every key is
    # from its complete aligned portrait; no skin patch is laid over the eyes.
    stiffness = smooth((clean[:,:,0].astype(np.float32)-142)/67)
    frames = []
    for a,b in ((0,1),(1,2)):
        for i in range(8):
            k = i/8
            if i==0:
                frames.append(keys[a].copy())
                continue
            # Draw one geometrically aligned painting at a time. Compositing
            # two lash/iris paints, even briefly, creates a second lid.
            use_destination = k >= (.625 if a==0 else .75)
            source,target,phase = (b,a,1-k) if use_destination else (a,b,k)
            rows = np.float32(y+(deform_y(x,y,source,target,phase)-y)*stiffness)
            frames.append(cv2.remap(keys[source],x,rows,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE))
    return [*frames,keys[-1].copy()]


def portrait_alpha(head, box=FACE_BOX):
    l,t,r,b = box
    y,x = np.indices((b-t,r-l),dtype=np.float32)
    # Taper at the outside of the entire head crop only, mostly through
    # the solid hair. Keep face edges and body pixels in their original layers.
    outer = smooth(x/10)*smooth((r-l-1-x)/7)*smooth(y/9)*smooth((b-t-1-y)/10)
    return outer*head[t:b,l:r,3]/255


def make_blink(original, head, clean_paint, half_paint, closed_paint, target):
    l,t,r,b = FACE_BOX
    neutral = original[t:b,l:r,:3].copy()
    clean, _ = register_mood(original,clean_paint)
    half, half_fit = register_mood(original,half_paint)
    closed, closed_fit = register_mood(original,closed_paint)
    neutral,half,closed = [match_complexion(key,complexion(key),target) for key in (neutral,half,closed)]
    frames = tween_portraits([neutral,half,closed],clean)
    silhouette = portrait_alpha(head)
    # Far-side wink uses a complete portrait too. The join runs through
    # the thick central hair, far from the original outer face contour.
    _,x = np.indices(silhouette.shape,dtype=np.float32)
    central_hair = smooth((x+l-661)/34)[:,:,None]
    wink = [rgba(np.rint(neutral*(1-central_hair)+step*central_hair),silhouette) for step in frames]
    both = [rgba(step,silhouette) for step in frames]
    return both,wink,{"half":half_fit,"closed":closed_fit}


def sleeping_plate(seated, closed, target):
    """Lay the matching closed portrait on the original independent seat."""
    l,t,r,b = FACE_BOX
    reference = seated[t:b,l:r,:3]
    generated = cv2.resize(closed[:,:,:3],(r-l,b-t),interpolation=cv2.INTER_AREA)
    mask = np.full((b-t,r-l),255,np.uint8)
    mask[39:182,40:352] = 0
    mask[180:,:] = 0
    grey = lambda image: cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)
    score,m = cv2.findTransformECC(
        grey(reference),grey(generated),np.eye(2,3,dtype=np.float32),cv2.MOTION_AFFINE,
        (cv2.TERM_CRITERIA_COUNT|cv2.TERM_CRITERIA_EPS,90,1e-5),mask,3)
    if score < .97:
        raise ValueError(f"Sleep portrait is misregistered: {score:.4f}")
    aligned = cv2.warpAffine(generated,m,(r-l,b-t),
                             flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REPLICATE)
    aligned = match_complexion(aligned,complexion(aligned),target)
    a = portrait_alpha(seated)[:,:,None]
    result = seated.copy()
    result[t:b,l:r,:3] = np.uint8(np.rint(reference*(1-a)+aligned*a))
    return result,float(score)
