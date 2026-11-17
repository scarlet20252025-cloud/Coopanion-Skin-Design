"""Register the left-arm paint donors to the approved right-facing master."""

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
W, H = 1163, 1352
PIVOT = (518, 732)
TEST_ANGLES = (-8, 0, 8)

# This curve traces the outside of the visible cuff, bracelet and glove.
ARM_START = (482, 851)
ARM_CURVES = [
    ((493, 849), (513, 846), (528, 849)),
    ((531, 857), (528, 868), (527, 876)),
    ((530, 881), (523, 887), (519, 891)),
    ((521, 896), (514, 903), (511, 907)),
    ((511, 912), (502, 913), (501, 919)),
    ((499, 921), (498, 925), (496, 928)),
    ((503, 940), (501, 957), (497, 971)),
    ((493, 981), (485, 986), (479, 984)),
    ((480, 993), (477, 999), (471, 1000)),
    ((466, 1000), (462, 995), (459, 992)),
    ((455, 990), (450, 984), (450, 979)),
    ((445, 972), (445, 961), (447, 949)),
    ((448, 939), (453, 929), (456, 922)),
    ((453, 918), (457, 915), (458, 911)),
    ((455, 908), (454, 905), (459, 904)),
    ((464, 902), (466, 899), (466, 896)),
    ((464, 891), (462, 885), (461, 880)),
    ((463, 876), (472, 874), (474, 871)),
    ((476, 865), (477, 857), ARM_START),
]

# Lower edge of the opaque capelet hem, in the fixed body coordinate space.
CAPE_EDGE = [(379, 911), (397, 889), (413, 872), (434, 863), (455, 857),
             (479, 852), (492, 850), (511, 848.5), (529, 850), (542, 854),
             (552, 861), (570, 866), (585, 872)]


def load(relative):
    with Image.open(ROOT / relative) as im:
        return np.array(im.convert("RGBA"))


def rasterize(start, curves):
    points = [start]
    for c1, c2, end in curves:
        for t in np.linspace(0, 1, 25)[1:]:
            s = 1 - t
            p = tuple(s**3 * a + 3*s*s*t * b + 3*s*t*t * c + t**3 * d
                      for a, b, c, d in zip(start, c1, c2, end))
            points.append(p)
        start = end
    im = Image.new("L", (4*W, 4*H))
    ImageDraw.Draw(im).polygon([(round(4*x), round(4*y)) for x, y in points], fill=255)
    return np.array(im.resize((W, H), Image.Resampling.BOX))


def warp_rgba(source, matrix):
    a = source[:, :, 3].astype(np.float32) / 255
    premul = np.dstack((source[:, :, :3] * a[:, :, None], a))
    result = cv2.warpAffine(premul, matrix, (W, H), flags=cv2.INTER_LINEAR)
    a = result[:, :, 3]
    return result[:, :, :3] / np.maximum(a[:, :, None], 1e-6), a


def register_lining(donor):
    donor_points = np.float32([(502, 784), (584, 888), (564, 964), (521, 908)])
    source_points = np.float32([(523, 739), (596, 837), (582, 906), (549, 854)])
    matrix, _ = cv2.estimateAffine2D(donor_points, source_points, method=cv2.LMEDS)
    predicted = cv2.transform(donor_points[None], matrix)[0]
    residual = np.linalg.norm(predicted - source_points, axis=1)
    if residual.max() > 9:
        raise ValueError(f"Lining landmarks do not agree: {residual.tolist()}")
    rgb, alpha = warp_rgba(donor, matrix)
    # A local horizontal registration seats the donor's two gold bands into
    # the two surviving diagonal bands under the glove. The global fit only
    # aligns the brooch and the upper edge of the cape.
    yy, xx = np.indices((H, W), dtype=np.float32)
    rows = [930, 950, 973, 990, 1000, 1020, 1035]
    source_left = [475, 483, 489, 485, 484, 480, 478]
    source_right = [525, 523, 520, 518, 517, 515, 514]
    target_left = [475, 468, 455, 449, 445, 439, 433]
    target_right = [521, 516, 507, 499, 495, 490, 485]
    remap_x = xx.copy()
    for y in range(931, 1035):
        fade = min(1, (y-930)/23, (1035-y)/17)
        a, b = [np.interp(y, rows, line) for line in (target_left, target_right)]
        c, d = [np.interp(y, rows, line) for line in (source_left, source_right)]
        correction = np.interp(xx[y], [a-25, a, b, b+25], [0, c-a, d-b, 0])
        remap_x[y] += fade*correction
    plate = np.dstack((rgb*alpha[:, :, None], alpha)).astype(np.float32)
    plate = cv2.remap(plate, remap_x, yy, cv2.INTER_LINEAR)
    alpha = plate[:, :, 3]
    rgb = plate[:, :, :3] / np.maximum(alpha[:, :, None], 1e-6)
    return rgb, alpha, matrix.tolist(), residual.tolist()


def register_sleeve(donor):
    # Only the model's painted charcoal sleeve is used. The model's resized
    # hands, white cuffs and gold rim are excluded from the donor.
    source = donor.copy()
    source[882:, :, :] = 0
    src = np.float32([(572, 718), (515, 878), (573, 878)])
    dst = np.float32([(517, 734), (489, 856), (523, 856)])
    matrix = cv2.getAffineTransform(src, dst)
    rgb, a = warp_rgba(source, matrix)
    return rgb, a, matrix.tolist()


def separate(master, lining, lining_alpha, sleeve, sleeve_alpha, shape, cape_curve):
    rgb = master[:, :, :3].astype(np.float32)
    y, x = np.indices((H, W))
    original_arm = shape > 0
    distance = cv2.distanceTransform(np.uint8(~original_arm), cv2.DIST_L2, 5)
    # Replace the arm and its baked contact shadow with the painted garment.
    # The actual cape edge and the jewelry stay in the protected body pixels.
    below_cape = y >= cape_curve
    wear = np.clip((12 - distance) / 9, 0, 1)
    solid = master[:, :, 3] >= 247
    wear = (3 - 2*wear)*wear**2 * below_cape * solid
    if np.any((wear > 0) & (lining_alpha < .96)):
        raise ValueError("The lining donor does not cover the seam.")
    cloth_source = (rgb.max(axis=2) < 105)
    cloth_donor = (lining.max(axis=2) < 105)
    nearby = np.float32((distance >= 13) & (distance <= 32) & below_cape
                         & (lining_alpha >= .96) & solid & cloth_source & cloth_donor)
    support = cv2.GaussianBlur(nearby, (0, 0), 13)
    correction = cv2.GaussianBlur((rgb-lining)*nearby[:, :, None], (0, 0), 13)
    correction = np.clip(correction / np.maximum(support[:, :, None], .025), -17, 17)
    painted = np.clip(lining+correction*cloth_donor[:, :, None], 0, 255)
    body = master.copy()
    body[:, :, :3] = np.uint8(np.rint(rgb + wear[:, :, None]*(painted-rgb)))

    # Unmatte the original soft edge against the repainted cloth without
    # modifying the approved interior hand/cuff pixels or their placement.
    bg = body[:, :, :3].astype(np.float32)
    diff = rgb-bg
    required = np.max(np.where(diff >= 0, diff / np.maximum(255-bg, 1),
                               -diff / np.maximum(bg, 1)), axis=2)
    a = np.where(original_arm & below_cape, np.maximum(shape/255, np.ceil(required*255)/255), 0)
    visible = np.zeros_like(master)
    carried = rgb+diff*((1-a)/np.maximum(a, 1e-5))[:, :, None]
    visible[:, :, :3] = np.where(a[:, :, None] > 0, np.clip(np.rint(carried), 0, 255), 0)
    visible[:, :, 3] = np.uint8(np.rint(a*255))

    # Merge the complete hidden sleeve behind the original cuff. The very last
    # few donor rows are narrowed to the actual opening of the preserved cuff.
    junction = np.clip((y-831)/24, 0, 1)
    left = 447 + 33*junction
    right = 555 - 27*junction
    sleeve_a = sleeve_alpha*np.clip((x-left+1)/3, 0, 1)*np.clip((right-x+1)/3, 0, 1)
    sleeve_a *= np.where(below_cape, a, 1)
    shoulder = np.dstack((np.where(sleeve_a[:, :, None] > 0, np.clip(np.rint(sleeve), 0, 255), 0),
                          np.rint(sleeve_a*255))).astype(np.uint8)
    arm = Image.alpha_composite(Image.fromarray(shoulder), Image.fromarray(visible))
    return Image.fromarray(body), arm, wear > 0, a


def assemble(body, arm, mask, angle):
    moved = arm.rotate(angle, Image.Resampling.BICUBIC, center=PIVOT) if angle else arm.copy()
    alpha = np.asarray(moved.getchannel("A"), dtype=np.uint16)
    front = np.uint8((alpha*(255-mask.astype(np.uint16))+127)//255)
    moved.putalpha(Image.fromarray(front))
    return Image.alpha_composite(body, moved)


def review_grid(master, body, arm, results):
    crop = (376, 690, 596, 1037)
    titles = ["Master", "Painted lining", "Complete arm", "-8 deg", "0 deg", "+8 deg"]
    images = [master, body, arm, *results]
    tile_w, tile_h = 264, 416
    page = Image.new("RGB", (tile_w*3, (tile_h+31)*2), "#e7e3e8")
    draw = ImageDraw.Draw(page)
    for i, (title, im) in enumerate(zip(titles, images)):
        ox, oy = i%3*tile_w, i//3*(tile_h+31)
        patch = im.crop(crop).resize((tile_w, tile_h), Image.Resampling.LANCZOS)
        page.paste(patch, (ox, oy+31), patch)
        draw.text((ox+12, oy+8), title, fill="#241e2b")
    page.save(ROOT / "review/left-arm-motion.png")


def main():
    master = load("source/master-right.png")
    assert master.shape == (H, W, 4)
    y, x = np.indices((H, W))
    cape_curve = np.interp(x, *np.array(CAPE_EDGE).T)
    cape = np.uint8((y <= cape_curve) & (x >= 375) & (x <= 585))*255
    shape = rasterize(ARM_START, ARM_CURVES)
    lining, lining_a, lining_matrix, residuals = register_lining(load("work/body-left-lining-donor.png"))
    sleeve, sleeve_a, sleeve_matrix = register_sleeve(load("work/arm-left-donor.png"))
    body, arm, edited, visible = separate(master, lining, lining_a, sleeve, sleeve_a, shape, cape_curve)
    results = [assemble(body, arm, cape, angle) for angle in TEST_ANGLES]
    assembled = np.array(results[1])
    alpha = np.asarray(arm.getchannel("A"))
    count, _, stats, _ = cv2.connectedComponentsWithStats(np.uint8(alpha >= 96))
    significant = int(np.count_nonzero(stats[1:, cv2.CC_STAT_AREA] >= 20))
    edit_zone = edited | (visible > 0)
    assert np.array_equal(assembled[~edit_zone], master[~edit_zone])
    alpha_delta = np.abs(assembled[:, :, 3].astype(np.int16)-master[:, :, 3])
    assert np.array_equal(assembled[:, :, 3] > 0, master[:, :, 3] > 0)
    assert alpha_delta.max() <= 8
    assert significant == 1, "The completed sleeve and cuff must form one piece."

    body.save(ROOT / "parts/body-left-pass.png")
    arm.save(ROOT / "parts/arm-viewer-left.png")
    matte = Image.new("RGBA", (W, H), "white")
    matte.putalpha(Image.fromarray(cape))
    matte.save(ROOT / "masks/cape-left-occlusion.png")
    results[1].save(ROOT / "review/left-arm-reassembled.png")
    review_grid(Image.fromarray(master), body, arm, results)

    audit = {
        "canvas": [W, H],
        "side_convention": "viewer, after mirror",
        "master_sha256": hashlib.sha256((ROOT / "source/master-right.png").read_bytes()).hexdigest(),
        "viewer_left_shoulder": {"xy": PIVOT, "status": "candidate, left-arm range check only"},
        "angles_degrees": TEST_ANGLES,
        "lining_affine": lining_matrix,
        "lining_landmark_residuals_px": residuals,
        "sleeve_affine": sleeve_matrix,
        "arm_significant_alpha_components": significant,
        "arm_other_alpha_components": count-1-significant,
        "arm_hidden_core_pixels": int(np.count_nonzero((alpha >= 128) & (cape == 255))),
        "assembly_changed_pixels": int(np.count_nonzero(np.any(assembled != master, axis=2))),
        "assembly_alpha_coverage_changed_pixels": 0,
        "assembly_max_alpha_delta": int(alpha_delta.max()),
        "assembly_changed_pixels_outside_seam": 0,
    }
    (ROOT / "review/left-arm-audit.json").write_text(json.dumps(audit, indent=2), encoding="utf8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
