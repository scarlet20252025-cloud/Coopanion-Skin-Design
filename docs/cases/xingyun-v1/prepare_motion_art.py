"""Prepare Xingyun's eye transition and flexible lock textures in master coordinates."""
import json

from prepare_art import HERE, W, H, X, Y, map_rgba, read, remove_detached_alpha

import cv2
import numpy as np
from PIL import Image

ART = HERE / "art-0.1.2"
PREVIOUS = HERE / "art-0.1.1/parts"
OUT = ART / "parts"
STEPS = 17


def write(path, image):
    Image.fromarray(image).save(OUT / path, optimize=True)


def smooth(value):
    k = np.clip(value, 0, 1)
    return k * k * (3 - 2 * k)


def matte(shape, polygon, origin, sigma=.8):
    mask = np.zeros(shape, np.uint8)
    cv2.fillPoly(mask, [np.asarray(polygon, np.int32)-origin], 255)
    return cv2.GaussianBlur(mask,(0,0),sigma)


def smooth_skin(image, excluded):
    rgb = image[...,:3].astype(np.float32)
    skin = (rgb[...,0]-rgb[...,2] > 10) & (rgb[...,0]>187) & (rgb[...,1]>139)
    clean = (skin & ~excluded).astype(np.float32)
    density = cv2.GaussianBlur(clean,(0,0),8)
    color = cv2.GaussianBlur(rgb*clean[...,None],(0,0),8)
    color = np.divide(color,density[...,None],out=rgb.copy(),where=density[...,None] > .01)
    return np.dstack((color,image[...,3]))


def flatten_eye(image, mask, source):
    fill = cv2.GaussianBlur(mask.astype(np.float32),(0,0),1.2)[...,None]
    return image*(1-fill) + source*fill, fill


def blink_images(open_head, closed_head, box, anchors, aperture, closed_lash, crease):
    l, t, r, b = box
    op = open_head[t:b,l:r]
    cl = closed_head[t:b,l:r]
    yy, xx = np.indices(op.shape[:2],dtype=np.float32)
    origin = np.array([l,t],np.int32)
    x = np.arange(l,r)
    nodes = np.asarray(anchors)
    upper, shut = [np.interp(x,nodes[:,0],nodes[:,i]) - t for i in (1,3)]
    aperture_alpha = matte(op.shape[:2],aperture,origin)

    # Isolate only the painted eye opening. Hair, brows, cheek shading and
    # the other eye are fixed while this paint deforms.
    eye = op.copy()
    eye[...,3] = np.minimum(eye[...,3],aperture_alpha)
    lash = matte(op.shape[:2],closed_lash,origin, .65)
    remove = cv2.dilate((lash>8).astype(np.uint8),np.ones((7,5),np.uint8))
    creases = matte(op.shape[:2],crease,origin,1.55).astype(np.float32)[...,None]/255
    same = np.abs(op[...,:3].astype(np.float32)-cl[...,:3]).max(axis=2)<9
    cool = (cl[...,0].astype(int)-cl[...,2].astype(int))<10
    fixed = same & cool & (lash<180)
    repair = (remove > 0) & ~fixed
    smoothed = smooth_skin(cl,repair | (creases[...,0]>.2))
    closed_clean, fill_alpha = flatten_eye(cl,repair,smoothed)
    neutral = smoothed
    # The apertures need an opaque skin bed. Outside their sweep the original
    # face remains byte-identical, including the hair that overlaps both tips.
    band = cv2.dilate(np.maximum(aperture_alpha,lash),np.ones((17,15),np.uint8))
    use_skin = np.maximum(cv2.GaussianBlur(band,(0,0),1.35).astype(np.float32)[...,None]/255,
                          creases)

    frames = [op.copy()]
    for i in range(1,STEPS-1):
        p = i / (STEPS-1)
        deform = min(1.,p/.88)
        eye_height = 1 - .975*deform
        eyelid = upper + (shut-upper)*deform
        source_y = upper + (yy-eyelid)/eye_height
        samples = [map_rgba(eye,xx,source_y + offset/eye_height).astype(np.float32)
                   for offset in (-.30,-.10,.10,.30)]
        opacity = np.mean([sample[...,3:] for sample in samples],axis=0) / 255
        sample_rgb = np.mean([sample[...,:3]*(sample[...,3:]/255) for sample in samples],axis=0)
        visible = (1-smooth((p-.66)/.23)) * (~fixed)[...,None]
        # Fade the single open fold to bare skin, then reveal the painted
        # closed fold. Their weights are never positive at the same time.
        hide_fold = smooth((p-.12)/.38)
        show_fold = smooth((p-.65)/.28)
        clear_fold = creases*(1-show_fold)*(~fixed)[...,None]
        skin = closed_clean*(1-clear_fold) + neutral*clear_fold
        base = op * (1-use_skin) + skin * use_skin
        open_fold = creases * (1-hide_fold) * smooth((upper-yy-3)/4)[...,None]
        base = base*(1-open_fold) + op*open_fold
        faint_lash = fill_alpha * smooth((p-.70)/.22)
        base = base*(1-faint_lash) + cl*faint_lash
        base[fixed] = cl[fixed]
        base[...,:3] = base[...,:3]*(1-opacity*visible) + sample_rgb*visible
        frames.append(np.rint(base).astype(np.uint8))
    frames.append(cl.copy())
    return frames


def sheet(name, frames, box):
    cols = 5
    height, width = frames[0].shape[:2]
    atlas = Image.new("RGBA", (width*cols, height*((len(frames)+cols-1)//cols)))
    for i, frame in enumerate(frames):
        atlas.paste(Image.fromarray(frame), (i%cols*width, i//cols*height))
    atlas.save(OUT / f"{name}.png", optimize=True)
    return {"box": [*box[:2], width, height], "count": len(frames), "columns": cols}


def paint_eye_sheets():
    op = read(PREVIOUS / "head-open.png")
    cl = read(PREVIOUS / "head-closed.png")
    # Use the full bounds of the artwork difference so the same baseline
    # blends into the face on every frame.
    bounds = [(430, 472, 662, 624), (682, 472, 838, 618)]
    guides = [
        [(448,525,529,554,558),(469,526,534,558,564),(489,528,553,563,573),
         (513,528,576,569,580),(537,525,584,574,585),(561,526,586,577,589),
         (585,529,584,576,588),(607,534,582,571,583),(628,543,566,570,580),
         (644,552,558,577,580)],
        [(701,558,564,568,573),(718,545,565,565,572),(733,533,576,570,580),
         (749,527,578,571,584),(765,526,575,569,584),(779,527,568,565,579),
         (794,527,544,559,570),(802,529,534,556,563)],
    ]
    creases = [
        [(512,511),(548,510),(579,514),(601,522),(618,539),
         (622,549),(614,547),(595,534),(566,525),(530,523),(512,522)],
        [(737,529),(748,518),(763,515),(774,517),(775,528),(765,533),(744,540)],
    ]
    open_shapes = [
        [(465,523),(483,526),(515,525),(539,522),(573,524),(596,528),(614,535),
         (633,548),(633,556),(622,576),(609,585),(579,589),(550,591),(525,587),
         (509,576),(494,559),(480,538)],
        [(713,549),(720,540),(735,529),(750,525),(767,523),(785,527),(792,524),
         (790,534),(776,546),(772,568),(759,578),(742,582),(725,577),(715,566)],
    ]
    shut_shapes = [
        [(474,556),(487,558),(512,568),(539,575),(566,576),(591,573),(613,568),
         (625,571),(631,577),(611,578),(587,589),(560,593),(537,591),(512,585),(490,572)],
        [(708,570),(718,564),(736,570),(751,572),(772,568),(786,560),(792,560),
         (786,569),(772,580),(754,587),(739,584),(723,575),(709,575)],
    ]
    result = {}
    for side, box, points, aperture, lash, crease in zip(("eyeLeft","eyeRight"),
            bounds, guides, open_shapes, shut_shapes, creases):
        frames = blink_images(op, cl, box, points, aperture, lash, crease)
        result[side] = sheet(side, frames, box)
    return result


def paint_locks():
    original = remove_detached_alpha(read(ART / "input/locks.png"), 2)
    data = (
        ("lockLeft", (420,560), (438,749), (480,685), (.89,.75), -.038, (448,680,578,997)),
        ("lockRight",(670,790), (708,753), (737,696), (.84,.755), -.018, (692,692,812,1017)),
    )
    result = {}
    for name, span, start, pos, scale, lean, box in data:
        donor = original.copy()
        donor[:, :span[0]] = 0
        donor[:, span[1]:] = 0
        x0, y0 = start
        x1, y1 = pos
        sx, sy = scale
        l,t,r,b = box
        dy = Y[t:b,l:r] - y1
        dx = X[t:b,l:r] - x1
        # Base placement is a single affine transform of the approved lock.
        # Each swing frame adds continuous curvature, pinned under its cuff.
        f = np.clip(dy / (b-y1),0,1)
        frames = []
        for step in np.linspace(-1, 1, STEPS):
            bend = 11 * step * f ** 2
            frames.append(map_rgba(donor, x0 + (dx-lean*dy-bend)/sx, y0 + dy/sy))
        neutral = np.zeros((H,W,4),np.uint8)
        neutral[t:b,l:r] = frames[STEPS//2]
        write(f"{name}.png", neutral)
        result[name+"Motion"] = sheet(name+"Motion",frames,box)
    return result


def warp_sprite(donor,points,box):
    source, dest = points[:,0] / 200, points[:,1] / 200

    def radial(x):
        r2 = ((x[:,None,:]-dest[None,:,:])**2).sum(axis=2)
        return r2 * np.log(np.maximum(r2,1e-12))

    affine = np.column_stack((np.ones(len(dest)),dest))
    coeff = np.linalg.solve(np.block([[radial(dest),affine],[affine.T,np.zeros((3,3))]]),
                            np.vstack((source,np.zeros((3,2)))))
    l,t,r,b = box
    positions = np.column_stack((X[t:b,l:r].ravel(),Y[t:b,l:r].ravel()))/200
    basis = np.column_stack((radial(positions),np.ones(len(positions)),positions))
    maps = (basis @ coeff * 200).reshape(b-t,r-l,2)
    return map_rgba(donor,maps[...,0],maps[...,1])


def paint_snake():
    base = read(PREVIOUS / "body.png")
    donor = read(ART / "input/snake-paint.png")
    # Anchor the painted coil at its dark outline, neck seam and shoulder.
    points = np.array([
        ((800,298),(795,717)), ((948,336),(824,725)),
        ((735,424),(777,747)), ((510,470),(730,757)),
        ((410,578),(709,778)), ((444,679),(701,802)),
        ((693,647),(749,796)), ((865,682),(787,799)),
        ((913,810),(808,829)), ((765,908),(790,850)),
        ((493,941),(731,845)), ((375,1113),(704,890)),
        ((276,878),(686,848)), ((322,740),(685,823)),
        ((205,574),(680,788)), ((298,536),(694,774))
    ],np.float64)
    box = l,t,r,b = 660,737,835,909
    patch = warp_sprite(donor,points,box)
    original = base[t:b,l:r]
    # Use the new painting inside the existing snake silhouette. The donor is
    # resampled only in the coil, away from the original shoulder and hand.
    local = lambda im: cv2.cvtColor(im[...,:3],cv2.COLOR_RGB2HSV)
    hsv = local(original)
    ink = (hsv[...,0] > 37) & (hsv[...,0] < 103) & (hsv[...,1] > 26)
    ink &= (original[...,3]>245) & (hsv[...,2] > 68)
    ink = cv2.morphologyEx(ink.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    valid = local(patch)
    valid = (valid[...,0]>37) & (valid[...,0]<105) & (valid[...,1]>25) & (valid[...,2]>75) & (patch[...,3]>250)
    dist, nearest = cv2.distanceTransformWithLabels((~valid).astype(np.uint8),cv2.DIST_L2,5,
                                                     labelType=cv2.DIST_LABEL_PIXEL)
    colors = np.zeros((int(nearest.max())+1,3),np.uint8)
    colors[nearest[valid]] = patch[valid,:3]
    clean = cv2.GaussianBlur(colors[nearest],(0,0),1.65)
    edge = cv2.distanceTransform(ink,cv2.DIST_L2,5)
    weight = smooth((edge-.9)/3.4)*smooth((Y[t:b,l:r]-777)/19)
    weight *= (1-.38*smooth((dist-5)/18))
    weight = cv2.GaussianBlur(weight,(0,0),1.2)
    original[...,:3] = np.rint(original[...,:3]*(1-weight[...,None]) +
                               clean*weight[...,None]).astype(np.uint8)
    return base


def place_crow():
    output = HERE / "art-0.1.3/parts"
    output.mkdir(parents=True, exist_ok=True)
    donor = remove_detached_alpha(read(ART / "input/crow-paint.png"),1)
    source_perch = (820,875)
    target_perch = (396,778)
    # One rotation and uniform scale preserve the painter's head, wing and
    # tail proportions. The feet fix the shoulder position.
    matrix = cv2.getRotationMatrix2D(source_perch,5.0,.235)
    matrix[:,2] += np.asarray(target_perch)-source_perch
    l,t,r,b = 210,590,485,850
    matrix[:,2] -= [l,t]
    pixels = donor.astype(np.float32)/255
    pixels[...,:3] *= pixels[...,3:]
    enlarged = matrix*2
    enlarged[:,2] += .5
    patch = cv2.warpAffine(pixels,enlarged,((r-l)*2,(b-t)*2),
                           flags=cv2.INTER_LINEAR)
    patch = cv2.resize(patch,(r-l,b-t),interpolation=cv2.INTER_AREA)
    np.divide(patch[...,:3],patch[...,3:],out=patch[...,:3],where=patch[...,3:]>0)
    crow = np.zeros((H,W,4),dtype=np.uint8)
    crow[t:b,l:r] = np.rint(np.clip(patch,0,1)*255).astype(np.uint8)
    Image.fromarray(crow).save(output/"crow.png",optimize=True)


def repair_cape(body):
    l,t,r,b = 210,595,491,838
    cape = remove_detached_alpha(read(ART / "input/cape-paint.png"),1)
    # Registration of the clean blue cape to the original shoulder and gold
    # piping. The broad torso below the bird keeps its existing painting.
    donor = map_rgba(cape,(X[t:b,l:r]-219)/.205,(Y[t:b,l:r]-577)/.212)
    region = np.array([(213,598),(464,598),(465,710),(470,740),
                       (429,756),(416,774),(369,800),(340,830),
                       (213,835)],np.int32)
    weight = matte((b-t,r-l),region,[l,t],2.8).astype(np.float32)[...,None]/255
    base = body[t:b,l:r]
    alpha = base[...,3:] / 255
    incoming = donor[...,3:] / 255
    out = alpha * (1-weight) + incoming * weight
    colors = base[...,:3]*alpha*(1-weight) + donor[...,:3]*incoming*weight
    np.divide(colors,out,out=colors,where=out>0)
    body[t:b,l:r] = np.rint(np.concatenate((colors,out*255),axis=2)).astype(np.uint8)
    write("body.png",body)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    parts = paint_eye_sheets()
    parts.update(paint_locks())
    repair_cape(paint_snake())
    place_crow()
    (OUT / "sheets.json").write_text(json.dumps(parts, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
