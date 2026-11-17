"""Prepare the registered seated dizzy portrait and its rotating eye marks."""

import cv2
import numpy as np
from PIL import Image

from assemble import ROOT
from matched_blink import portrait_alpha
from repair_eye_art import FACE_BOX, complexion, match_complexion, register_face_box, rgba


def isolate_spiral(portrait, window, near):
    l,t,_,_ = FACE_BOX
    x,y,r,b = window
    region = np.s_[y-t:b-t,x-l:r-l]
    colors = portrait[region].astype(np.int16)
    red,green,blue = colors.transpose(2,0,1)
    if near:
        ink = (green>67)&(green<166)&(blue-green>5)&(abs(red-blue)<36)
    else:
        ink = (green>72)&(green<174)&(red-blue>49)&(green-blue>19)
    _,labels,stats,_ = cv2.connectedComponentsWithStats(ink.astype(np.uint8))
    main = 1+np.argmax(stats[1:,cv2.CC_STAT_AREA])
    mask = np.zeros(portrait.shape[:2],np.uint8)
    mask[region] = labels==main
    assert 160<np.count_nonzero(mask)<1100
    margin = cv2.dilate(mask,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
    # Reconstruct the sclera from surrounding pale samples. A fill that
    # samples nearby black eyelashes drags their color into the eye.
    luminance = cv2.cvtColor(portrait,cv2.COLOR_RGB2GRAY)
    sampled = ((luminance>202)&(margin==0)).astype(np.float32)
    weight = cv2.GaussianBlur(sampled,(0,0),6)
    fill = cv2.GaussianBlur(portrait.astype(np.float32)*sampled[:,:,None],(0,0),6)
    fill = np.uint8(np.rint(np.clip(fill/np.maximum(.001,weight[:,:,None]),0,255)))
    repaired = (margin>0)&(luminance>63)
    erased = np.where(repaired[:,:,None],fill,portrait)
    color = np.median(portrait[mask>0],axis=0)
    pigment = color-erased
    residual = portrait.astype(np.float32)-erased
    alpha = np.clip((residual*pigment).sum(axis=2)/np.maximum(1,(pigment*pigment).sum(axis=2)),0,1)
    # Only retain the regenerated stroke and its antialiasing, excluding lash pixels.
    alpha *= repaired*np.clip((66-np.max(np.abs(residual-alpha[:,:,None]*pigment),axis=2))/39,0,1)
    alpha = cv2.morphologyEx(alpha.astype(np.float32),cv2.MORPH_CLOSE,
                             cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)))
    pixels = rgba(np.broadcast_to(color,portrait.shape),alpha)
    mark = Image.fromarray(pixels)
    dx,dy,dr,db = mark.getbbox()
    return erased,mark.crop((dx,dy,dr,db)),[dx+l,dy+t,dr-dx,db-dy]


def build_dizzy(parts,model,master,seated,donor,target):
    paint,fit,_ = register_face_box(master,donor)
    paint = match_complexion(paint,complexion(paint),target)
    clean,near,near_box = isolate_spiral(paint,(570,532,625,572),True)
    clean,far,far_box = isolate_spiral(clean,(710,541,747,575),False)
    seated_paint,seat_fit,matrix = register_face_box(seated,clean)
    seated_paint = match_complexion(seated_paint,complexion(seated_paint),target)
    l,t,r,b = FACE_BOX
    alpha = portrait_alpha(seated)[:,:,None]
    seat = seated.copy()
    seat[t:b,l:r,:3] = np.uint8(np.rint(seat[t:b,l:r,:3]*(1-alpha)+seated_paint*alpha))
    seat_image = Image.fromarray(seat)
    sx,sy,sr,sb = seat_image.getbbox()

    def save(name,image,box):
        file = f"tex/{name}.png"
        image.save(ROOT/"pack/star-witch"/file)
        parts[name] = {"file":file,"box":box,"count":1,"columns":1}

    save("dizzyNear",near,near_box)
    save("dizzyFar",far,far_box)
    save("dizzySeat",seat_image.crop((sx,sy,sr,sb)),[sx,sy,sr-sx,sb-sy])
    # Convert the face-window fit to an affine in the full master coordinates.
    offset = np.array([l,t])
    matrix[:,2] += offset-matrix[:,:2]@offset
    model["dizzySeatFit"] = matrix.T.reshape(-1).tolist()
    return {"stand":fit,"seat":seat_fit}
