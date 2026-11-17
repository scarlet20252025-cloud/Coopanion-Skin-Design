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


def split_skirt_depth():
    raw = np.array(part("body"))
    mask = np.array(part("skirtDepth"))[:,:,3].astype(np.float32)/255
    alpha = raw[:,:,3].astype(np.float32)
    front = np.rint(alpha*(1-mask))
    rear = np.rint(255*(alpha-front)/np.maximum(1,255-front))
    planes = []
    for opacity in (rear,front):
        plane = raw.copy()
        plane[:,:,3] = opacity.astype(np.uint8)
        planes.append(Image.fromarray(plane))
    return planes,mask


def composite(head=0, left=0, right=0, left_leg=0, right_leg=0, depth=None):
    head_parts = [rotation(part(n), "neck", head) for n in ("hat","lockLeft","lockRight","face","frontHair","hatRim")]
    rear,front = depth or (Image.new("RGBA",(W,H)),part("body"))
    return over(rotation(part("backHair"), "neck", head*.35), part("skirtBack"),rear,
                rotation(part("legRight"), "rightLeg", right_leg),
                rotation(part("legLeft"), "leftLeg", left_leg),front,
                arm("left",left),arm("right",right),*head_parts)


def review_skirt_depth(depth,mask,master):
    body = np.array(part("body"))
    alpha = np.array(over(*depth))[:,:,3]
    assert np.max(np.abs(alpha.astype(np.int16)-body[:,:,3]))<=1
    area = (mask>0)&(body[:,:,3]>0)
    assert mask[:1040].max()==0
    pose_pairs = [(0,0),(-10,10),(10,-10)]
    sheet = Image.new("RGB",(1332,1218),"#e5dce5")
    labels = ImageDraw.Draw(sheet)

    def cell(frame,index,row,title):
        patch = frame.crop((395,970,783,1315)).resize((424,377),Image.Resampling.LANCZOS)
        x,y = 444*index,405*row
        sheet.paste(patch,(x+10,y+28),patch)
        labels.text((x+10,y+7),title,fill="black")

    cell(master,0,0,"Approved master")
    for row,(left,right) in enumerate(pose_pairs):
        before = composite(left_leg=left,right_leg=right)
        after = composite(left_leg=left,right_leg=right,depth=depth)
        old,new = np.array(before),np.array(after)
        assert np.array_equal(old[~area],new[~area])
        legs = over(rotation(part("legRight"),"rightLeg",right),
                    rotation(part("legLeft"),"leftLeg",left))
        moving_legs = np.array(legs)
        clear_shins = (mask==1)&(body[:,:,3]>230)&(moving_legs[:,:,3]>240)
        if row:
            expected = np.array(over(part("backHair"),part("skirtBack"),depth[0],legs))
            assert np.count_nonzero(clear_shins)>200
            assert np.array_equal(new[clear_shins],expected[clear_shins])
        cell(before,1,row,"Previous layer order" if row==0 else f"Previous, hips {left}/{right}")
        cell(after,2,row,"Corrected layer order" if row==0 else f"Corrected, hips {left}/{right}")
    sheet.save(ROOT/"review/skirt-leg-depth.jpg",quality=96)


def main():
    master = Image.open(ROOT/"source/master-right.png").convert("RGBA")
    depth,mask = split_skirt_depth()
    stand = composite(depth=depth)
    stand.save(ROOT/"review/standing-reassembled.png")
    review_skirt_depth(depth,mask,master)
    poses = [master, stand, composite(-3.3,-6,5,4,-4,depth), composite(3.3,6,-5,-4,4,depth),
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
