"""Assemble the right-facing standing parts from the master and paint donors."""

import json

import cv2
import numpy as np
from PIL import Image

from assemble_left_arm import ROOT, W, H, load, warp_rgba
from repair_eye_art import FACE_BOX, complexion, expression_palette, match_head_skin


XX, YY = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
PIVOTS = {
    "neck": [604, 650], "leftShoulder": [518, 732], "rightShoulder": [695, 726],
    "leftLeg": [561, 1014], "rightLeg": [666, 1018],
    "lockLeft": [502, 625], "lockRight": [747, 623], "mouth": [671, 616],
}

GARMENT = [
    (548,642),(618,643),(649,671),(681,686),(723,723),(738,799),(756,833),
    (766,868),(755,915),(774,946),(785,985),(799,1016),(784,1025),(796,1043),
    (777,1061),(748,1067),(745,1087),(707,1098),(685,1114),(620,1127),
    (588,1133),(534,1148),(506,1165),(478,1238),(437,1228),(370,1190),
    (355,1130),(310,1102),(311,1086),(329,1046),(354,989),(379,935),
    (396,912),(390,884),(408,860),(446,827),(474,760),(480,727),(513,683),
]
HEAD = [
    (125,4),(1054,4),(1054,596),(851,608),(809,625),(779,658),(746,660),
    (728,638),(700,648),(659,655),(627,647),(621,665),(566,661),(559,638),
    (533,636),(520,620),(470,629),(408,632),(379,600),(290,603),(186,577),
]
HAT = [
    (113,0),(1063,0),(1063,552),(869,556),(877,426),(841,435),(825,457),
    (804,419),(799,388),(775,352),(751,339),(729,340),(704,362),(668,375),
    (635,388),(605,400),(579,417),(549,429),(512,447),(490,483),(466,497),
    (420,532),(396,556),(380,577),(372,667),(319,677),(308,594),(226,601),
    (213,537),(178,478),
]
LOCK_LEFT = [(479,598),(514,607),(535,660),(549,681),(563,719),(576,760),
             (583,800),(575,829),(562,851),(546,855),(549,813),(544,770),
             (531,726),(509,688),(497,652)]
LOCK_RIGHT = [(739,596),(773,587),(775,625),(765,671),(763,719),(769,768),
              (763,816),(753,853),(732,889),(710,888),(715,868),(728,838),
              (737,790),(731,750),(721,707),(720,662)]
RIGHT_ARM = [(720,883),(740,870),(767,866),(771,881),(767,897),(773,900),
             (778,908),(776,915),(778,924),(785,939),(790,953),(788,968),
             (781,982),(774,987),(766,981),(759,972),(759,960),(753,950),
             (747,936),(750,923),(744,916),(738,908),(729,901)]
LEG_LEFT = [(535,1070),(552,1067),(558,1061),(561,1054),(577,1052),(593,1045),
            (597,1045),(591,1092),(585,1129),(581,1149),(594,1154),(604,1172),(604,1206),(596,1220),
            (596,1238),(611,1260),(613,1326),(508,1329),(506,1231),(510,1170),
            (530,1150),(537,1148),(541,1130),(538,1090)]
LEG_RIGHT = [(628,1056),(649,1050),(659,1044),(664,1039),(683,1037),(689,1042),(687,1062),(679,1099),
             (672,1138),(672,1149),(687,1155),(704,1177),(703,1215),(687,1224),
             (693,1241),(712,1257),(722,1304),(709,1326),(608,1326),(608,1228),
             (610,1170),(623,1151),(630,1146),(630,1122),(628,1081)]


def polygon(points, blur=0):
    plane = np.zeros((H, W), np.uint8)
    cv2.fillPoly(plane, [np.rint(np.array(points) * 8).astype(np.int32)], 255, shift=3)
    if blur:
        plane = cv2.GaussianBlur(plane, (0, 0), blur)
    return plane.astype(np.float32)/255


def alpha_layer(rgb, alpha):
    return Image.fromarray(np.dstack((np.where(alpha[:, :, None] > 0, np.rint(np.clip(rgb, 0, 255)), 0),
                                      np.rint(np.clip(alpha, 0, 1)*255))).astype(np.uint8))


def take(source, mask):
    return alpha_layer(source[:, :, :3], source[:, :, 3]/255*mask)


def remove_edge_spill(image):
    """Remove disconnected haze and decontaminate faint antialiased pixels."""
    clean = image.copy()
    a = image[:, :, 3]
    edge = (a > 0) & (a < 118)
    interior = np.uint8(a >= 178)
    distance, labels = cv2.distanceTransformWithLabels(1-interior,cv2.DIST_L2,5,
                                                       labelType=cv2.DIST_LABEL_PIXEL)
    palette = np.zeros((labels.max()+1,3),np.uint8)
    palette[labels[interior > 0]] = image[:, :, :3][interior > 0]
    cleaned_rgb = clean[:, :, :3]
    weak = edge & (distance <= 3.1)
    cleaned_rgb[weak] = palette[labels[weak]]
    clean[edge & ~weak] = 0
    return clean


def over(*images):
    result = Image.new("RGBA", (W, H))
    for image in images:
        result.alpha_composite(image)
    return result


def keep_main_piece(image):
    art = np.array(image)
    _, labels, stats, _ = cv2.connectedComponentsWithStats(np.uint8(art[:, :, 3] >= 32))
    main = np.uint8(labels == 1+np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    with_edge = cv2.dilate(main,np.ones((3,3),np.uint8)) > 0
    art[~with_edge] = 0
    return Image.fromarray(art)


def affine(source, src_pts, dst_pts):
    return warp_rgba(source, cv2.getAffineTransform(np.float32(src_pts), np.float32(dst_pts)))


def donor_patch(donor, input_marks, output_marks):
    """Register cloth using several landmarks, with a local fit near occlusions."""
    c = np.array(output_marks, np.float32)
    s = np.array(input_marks, np.float32)
    init, *_ = np.linalg.lstsq(np.c_[c, np.ones(len(c))], s, rcond=None)
    inv = np.array(init, np.float32)
    residual = s - np.c_[c, np.ones(len(c))]@inv
    dx = np.zeros_like(XX)
    dy = np.zeros_like(YY)
    total = np.zeros_like(XX)
    for (x, y), (delta_x, delta_y) in zip(c, residual):
        weight = 1/(36**2+(XX-x)**2+(YY-y)**2)**1.8
        dx += weight*delta_x
        dy += weight*delta_y
        total += weight
    map_x = XX*inv[0, 0]+YY*inv[1, 0]+inv[2, 0]+dx/total
    map_y = XX*inv[0, 1]+YY*inv[1, 1]+inv[2, 1]+dy/total
    a = donor[:, :, 3].astype(np.float32)/255
    data = np.dstack((donor[:, :, :3]*a[:, :, None], a)).astype(np.float32)
    result = cv2.remap(data, map_x, map_y, cv2.INTER_LINEAR)
    a = result[:, :, 3]
    return result[:, :, :3]/np.maximum(a[:, :, None], 1e-5), a


def nearest_body_fill(plate, alpha, source, needs):
    rgb = source[:, :, :3].copy()
    target = needs > 0
    if np.any(target):
        good = np.uint8(alpha > .88)
        _, ids = cv2.distanceTransformWithLabels(1-good, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
        lookup = np.empty((ids.max()+1, 3), dtype=np.float32)
        lookup[ids[good > 0]] = plate[good > 0]
        painted = np.where(good[:, :, None] > 0, plate, lookup[ids])
        rgb[target] = np.uint8(np.rint(np.clip(painted[target], 0, 255)))
    return rgb


def back_hair(master, occupied):
    donor = load("work/back-hair-donor.png")
    rgb, alpha = affine(donor, [(220,946),(951,945),(596,223)],
                        [(263,957),(908,956),(593,321)])
    # Fill behind the head and torso. The outer visible strands are restored
    # from the master, so the donor silhouette never controls the stand pose.
    hidden = polygon([(369,508),(465,329),(646,316),(742,394),(842,572),
                      (815,823),(845,997),(735,1049),(511,1062),(346,1054),
                      (296,1009),(334,935),(408,748)], .85)
    contact = cv2.dilate(np.uint8(master[:, :, 3]>100),np.ones((9,9),np.uint8))
    occupied_interior = cv2.dilate(np.uint8(occupied>.6),np.ones((7,7),np.uint8))
    under = alpha_layer(rgb, alpha*hidden*occupied_interior*contact)
    art = np.array(over(under, take(master, (1-occupied)*(YY < 1070))))
    _, labels, stats, _ = cv2.connectedComponentsWithStats(np.uint8(art[:, :, 3] > 40))
    keep = labels == 1+np.argmax(stats[1:, cv2.CC_STAT_AREA])
    keep = cv2.dilate(np.uint8(keep),np.ones((5,5),np.uint8)) > 0
    art[~keep] = 0
    return Image.fromarray(art)


def paint_lock(master, visible, left):
    brush = load("work/front-locks-donor.png")
    if left:
        brush[:,800:,:] = 0
        s = [(508,201),(526,323),(557,340)]
        t = [(489,594),(503,635),(530,648)]
        limit = polygon([(476,577),(511,578),(543,634),(546,658),(501,670),(487,632)], .72)
        join_y = 650
    else:
        brush[:,:800,:] = 0
        s = [(1045,210),(1007,327),(1060,344)]
        t = [(746,589),(735,635),(765,643)]
        limit = polygon([(722,573),(775,582),(780,621),(767,667),(723,668),(718,623)], .72)
        join_y = 653
    rgb, alpha = affine(brush,s,t)
    return expanded_paint(master,visible,rgb,alpha,limit,join_y,11)


def paint_hat(master, visible, head):
    brush = load("work/hat-donor.png")
    rgb, a = affine(brush, [(665,28),(1388,425),(287,834)],
                   [(488,52),(964,291),(249,553)])
    brim = polygon([(368,503),(485,445),(593,399),(708,352),(812,360),
                   (825,416),(798,486),(711,554),(565,598),(421,600)], .65)
    # The repaired brim is hidden under the fringe at rest.
    return over(alpha_layer(rgb,a*brim*head*(master[:, :, 3]>100)),
                take(master,visible))


def expanded_paint(source, visible, rgb, alpha, upper, seam_y, join):
    extension = np.clip((seam_y+join-YY)/max(join, .01), 0, 1)*upper
    # The repaired seam includes the donor and the original detail. The
    # original garment, jewelry, boots and glove interiors retain their scale.
    under = alpha_layer(rgb, alpha*extension)
    return over(under, take(source, visible))


def paint_right_arm(master, visible):
    donor = load("work/arm-right-donor.png")
    donor[728:,:,:] = 0
    rgb, alpha = affine(donor, [(419,166),(577,698),(689,708)],
                        [(689,710),(727,884),(758,881)])
    upper = polygon([(660,698),(704,689),(734,741),(762,818),(770,876),
                     (760,902),(735,902),(717,881),(684,800),(660,742)], .55)
    return expanded_paint(master, visible, rgb, alpha, upper, 885, 10)


def paint_leg(master, donor, visible, near):
    if near:
        sx = [(689,183),(832,184),(750,476)]
        dst = [(533,973),(601,974),(564,1089)]
        edge_y = 1091
        bound = polygon([(525,963),(598,963),(607,1037),(590,1092),
                         (536,1093),(528,1045)], .7)
        donor[:,877:,:] = 0
    else:
        sx = [(927,182),(1071,186),(973,475)]
        dst = [(624,973),(696,976),(652,1081)]
        edge_y = 1081
        bound = polygon([(628,962),(699,967),(693,1043),(681,1090),
                         (623,1080),(627,1035)], .7)
        donor[:,:878,:] = 0
    donor[492:,:,:] = 0
    rgb, alpha = affine(donor, sx, dst)
    # Tone match at skin, before the donor disappears under the original.
    sample = (visible > .98) & (alpha > .98) & (YY > edge_y-16) & (YY < edge_y+4)
    if np.any(sample):
        delta = np.median(master[:, :, :3][sample]-rgb[sample], axis=0)
        rgb = np.clip(rgb+np.clip(delta, -18, 18), 0, 255)
    coat_shade = np.clip((YY-(edge_y-21))/20, 0, 1)
    natural = ((1-alpha)*visible + alpha*visible*coat_shade)
    return keep_main_piece(expanded_paint(master, natural, rgb, alpha, bound, edge_y, 11))


def face_parts(master, head, hat):
    face_outline = polygon([(453,556),(496,489),(530,426),(597,395),(659,406),
                            (729,435),(769,481),(762,580),(756,606),(723,632),
                            (678,648),(630,652),(622,670),(564,667),(558,637),
                            (517,630),(481,612),(461,596)], .55)
    rgb, a = affine(load("work/head-base-donor.png"),
                   [(428,698),(997,600),(749,860)],
                   [(462,582),(755,541),(627,642)])
    under = alpha_layer(rgb, a*face_outline)
    face_visible = polygon([(462,568),(473,565),(480,580),(506,584),(511,569),
                            (502,524),(538,501),(587,441),(610,411),(629,452),
                            (651,497),(677,538),(706,561),(716,519),(745,481),
                            (758,463),(768,509),(761,554),(743,579),(741,599),
                            (751,603),(736,626),(696,642),(651,647),(628,645),
                            (622,663),(561,656),(558,641),(533,635),(508,618),
                            (479,608),(459,592)], .45)*head*(1-hat)
    # The upper forehead comes only from the painted donor. This plane is
    # occluded by the rigid front hair at rest and during head movement.
    face = over(under, take(master, face_visible))
    hair_donor = load("work/back-hair-donor.png")
    painted, painted_alpha = affine(hair_donor, [(400,337),(787,337),(590,231)],
                                   [(468,445),(813,427),(622,333)])
    forelock_root = polygon([(481,366),(684,314),(795,357),(816,433),
                            (746,467),(548,494),(494,467)], .75)
    fringe = over(alpha_layer(painted,painted_alpha*forelock_root*hat),
                  take(master, head*(1-hat)*(1-face_visible)))
    return face, fringe


def write_part(name, im, parts):
    im.save(ROOT/"parts"/f"{name}.png")
    bounds = im.getchannel("A").getbbox()
    if not bounds:
        raise ValueError(f"Empty layer: {name}")
    x,y,r,b = bounds
    im.crop(bounds).save(ROOT/"pack/star-witch/tex"/f"{name}.png")
    parts[name] = {"file": f"tex/{name}.png", "box": [x,y,r-x,b-y]}


def main():
    master = remove_edge_spill(load("source/master-right.png"))
    body_source = remove_edge_spill(load("parts/body-left-pass.png"))
    star = polygon([(346,548),(353,548),(354,587),(361,604),(380,622),
                    (363,634),(350,672),(337,640),(318,624),(338,607),(344,587)])
    head_mask = np.maximum(polygon(HEAD), star)
    hat_mask = np.maximum(polygon(HAT)*head_mask, star)
    red,_,blue = [master[:,:,i].astype(np.int16) for i in range(3)]
    gold = np.clip((red-132)/23,0,1)*np.clip((red-blue-30)/18,0,1)
    locks = [polygon(outline,.63)*(1-head_mask)*(1-gold) for outline in (LOCK_LEFT,LOCK_RIGHT)]
    lock_zone = np.maximum(*locks)
    arm_mask = polygon(RIGHT_ARM, .6)*(1-lock_zone)
    legs_mask = [polygon(LEG_LEFT, .52), polygon(LEG_RIGHT, .52)]
    leg_zone = np.maximum(*legs_mask)
    garment = polygon(GARMENT, .5)*(1-head_mask)
    occupied = np.maximum.reduce([head_mask, lock_zone, arm_mask, leg_zone, garment])

    rgb_cloth, alpha_cloth = donor_patch(
        load("work/body-clean-donor.png"),
        [(423,280),(643,194),(591,486),(674,463),(653,535),(550,650),
         (811,295),(936,500),(1022,911),(172,971),(322,1174),(335,1408)],
        [(524,737),(626,697),(596,838),(636,819),(631,850),(581,908),
         (703,736),(744,854),(791,1014),(391,1046),(455,1133),(465,1234)])
    fill = garment*np.maximum(lock_zone, arm_mask)
    painted_body = nearest_body_fill(rgb_cloth, alpha_cloth, body_source, fill)
    seam_rgb = np.rint(body_source[:, :, :3]*(1-fill[:, :, None])+painted_body*fill[:, :, None])
    body_alpha = body_source[:, :, 3]/255*garment*(1-leg_zone)
    # Continuous cloth above the collar and behind both chest locks. These
    # insertions stay under the rotating face and under the protected collar.
    neck = polygon([(553,624),(617,624),(640,650),(630,676),
                    (550,696),(532,675)], .82)
    neck_paint = alpha_layer(rgb_cloth, alpha_cloth*neck)
    body = over(neck_paint, alpha_layer(seam_rgb, body_alpha))
    lining_area = polygon([(507,1030),(584,1030),(708,1030),(736,1072),
                          (718,1092),(673,1115),(621,1129),(516,1147)], .85)
    backing = alpha_layer(rgb_cloth, alpha_cloth*lining_area)
    # Follow the lower seams of the front ruffles, then include only the
    # visible back-facing panels the shins can pass in front of.
    back_hem = np.maximum.reduce([
        polygon([(498,1087),(507,1081),(517,1075),(536,1071),(568,1064),
                 (580,1082),(580,1172),(507,1199),(488,1210),(488,1123)],.85),
        polygon([(581,1070),(597,1064),(613,1061),(628,1058),(639,1057),
                 (656,1136),(571,1150)],.85),
        polygon([(665,1065),(675,1055),(684,1052),(695,1053),(706,1054),
                 (717,1052),(728,1048),(744,1044),(758,1045),(774,1056),
                 (778,1120),(668,1150)],.85),
    ])
    skirt_depth = alpha_layer(np.full_like(master[:,:,:3],255),back_hem)

    face, front_hair = face_parts(master, head_mask, hat_mask)
    target,_ = expression_palette(master,load)
    l,t,r,b = FACE_BOX
    skin = complexion(master[t:b,l:r])
    face,front_hair = [Image.fromarray(match_head_skin(np.array(layer),skin,target))
                       for layer in (face,front_hair)]
    left_arm = Image.fromarray(load("parts/arm-viewer-left.png"))
    cover_l = Image.fromarray(load("masks/cape-left-occlusion.png"))
    cape_r = polygon([(633,682),(789,682),(798,833),(779,855),(766,872),(748,879),
                      (724,894),(711,890),(686,844),(652,812)], .65)
    cover_r = alpha_layer(np.full_like(master[:, :, :3],255), cape_r)
    seat = load("work/sit-donor.png")
    seat_rgb, seat_alpha = affine(seat, [(490,52),(822,413),(650,1325)],
                                 [(490,65),(822,423),(650,1313)])

    sitting = remove_edge_spill(np.array(alpha_layer(seat_rgb, seat_alpha)))
    sitting = match_head_skin(sitting,complexion(sitting[t:b,l:r]),target)
    layers = {
        "backHair": back_hair(master, occupied), "skirtBack": backing, "skirtDepth": skirt_depth,
        "legLeft": paint_leg(master, load("work/legs-donor.png"), legs_mask[0], True),
        "legRight": paint_leg(master, load("work/legs-donor.png"), legs_mask[1], False),
        "body": body, "leftArm": left_arm, "rightArm": paint_right_arm(master, arm_mask),
        "leftCover": cover_l, "rightCover": cover_r,
        "lockLeft": paint_lock(master, locks[0], True), "lockRight": paint_lock(master, locks[1], False),
        "face": face, "frontHair": front_hair, "hat": paint_hat(master, hat_mask, head_mask),
        "sitBody": Image.fromarray(sitting),
    }
    (ROOT/"pack/star-witch/tex").mkdir(parents=True, exist_ok=True)
    parts = {}
    over(backing,body).save(ROOT/"review/body-unified-source.png")
    for name, im in layers.items():
        write_part(name, im, parts)
    # The original brim pixels sit in front of the restored hair roots.
    # This is a draw-order sublayer of the hat, not another painted object.
    write_part("hatRim",take(master,hat_mask*polygon(
        [(435,350),(737,280),(864,322),(841,473),(532,531),(430,508)])),parts)
    model = {"canvas":[W,H],"view":[143,12,883,1331],"ground":[611,1313],
             "unitsPerPixel":.176,"joints":PIVOTS,"parts":parts}
    (ROOT/"pack/star-witch/model.json").write_text(json.dumps(model,indent=2),encoding="utf8")
    (ROOT/"review/anchors.json").write_text(json.dumps(
        {"canvas":[W,H],"sides":"viewer","status":"motion-preview candidates","anchors":PIVOTS},indent=2),encoding="utf8")


if __name__ == "__main__":
    main()
