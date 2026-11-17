"""Recreate the part montage, source comparison and occlusion probes."""
from PIL import Image, ImageDraw
import numpy as np
from assemble import ROOT, PIVOTS, W, H, over


def part(name):
    return Image.open(ROOT/"parts"/f"{name}.png").convert("RGBA")


def rotation(im, pivot, angle):
    return im.rotate(angle, Image.Resampling.BICUBIC, center=tuple(PIVOTS[pivot])) if angle else im


def arm(name, angle):
    pose = rotation(part(name+"Arm"), name+"Shoulder", angle)
    a = np.array(pose.getchannel("A"), np.uint16)
    cover = np.array(part(name+"Cover").getchannel("A"), np.uint16)
    pose.putalpha(Image.fromarray(np.uint8((a*(255-cover)+127)//255)))
    return pose


def composite(head=0, left=0, right=0, left_leg=0, right_leg=0):
    head_parts = [rotation(part(n), "neck", head) for n in ("hat","lockLeft","lockRight","face","frontHair","hatRim")]
    return over(rotation(part("backHair"), "neck", head*.35), part("skirtBack"),
                rotation(part("legRight"), "rightLeg", right_leg),
                rotation(part("legLeft"), "leftLeg", left_leg), part("body"),
                arm("left",left),arm("right",right),*head_parts)


def main():
    master = Image.open(ROOT/"source/master-right.png").convert("RGBA")
    stand = composite()
    stand.save(ROOT/"review/standing-reassembled.png")
    poses = [master, stand, composite(-3.3,-6,5,4,-4), composite(3.3,6,-5,-4,4),
             part("sitBody"), part("body"), part("backHair"), over(part("legLeft"),part("legRight")),
             over(part("leftArm"),part("rightArm"))]
    names = ["Approved master", "Reassembled", "Pose A", "Pose B","Independent sit",
             "Clothing base", "Back hair", "Completed legs", "Completed sleeves"]
    page = Image.new("RGB",(1250,840),"#e6e0e7")
    draw = ImageDraw.Draw(page)
    for i, (label, frame) in enumerate(zip(names, poses)):
        x,y = 250*(i%5), 420*(i//5)
        frame = frame.crop((155,35,1010,1330))
        frame.thumbnail((247,391))
        page.paste(frame,(x+(250-frame.width)//2,y+25),frame)
        draw.text((x+11,y+7),label,fill="#261d2a")
    page.save(ROOT/"review/full-motion-check.jpg",quality=94)


if __name__=="__main__":
    main()
