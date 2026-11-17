"""Render and verify extreme walk/run poses from the finished transparent layers."""
import json
from math import cos, sin, tau
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from assemble import ROOT, OUT, REVIEW, SIZE, compose_pose, read, warp

MODEL = ROOT / "pack/xingyun-v2/model.json"
KEYS = ("leftArm", "rightArm", "leftLeg", "rightLeg", "tail", "staff", "lockLeft", "lockRight")


def area(alpha):
    return int(np.count_nonzero(alpha))


def connected(alpha):
    _,_,stats,_=cv2.connectedComponentsWithStats((alpha>96).astype(np.uint8))
    return [tuple(map(int,row)) for row in stats[1:] if row[-1]>75]


def main():
    model=json.loads(MODEL.read_text(encoding="utf-8"))
    pack=json.loads((OUT/"parts.json").read_text(encoding="utf-8"))
    images={name:read(OUT/f"{name}.png") for name in pack["stack"]}
    parts={part["id"]:part for part in model["parts"]}
    assert parts["skirtLining"]["parent"]==parts["body"]["parent"]=="body"
    assert parts["skirtLining"]["z"]<parts["leftLeg"]["z"]<parts["body"]["z"]
    original=read(ROOT/"source/master.png")
    # These fully exposed panels must retain the master's actual paint.
    for region in (np.s_[950:978,561:607],np.s_[945:975,641:725]):
        check=images["body"][region]
        match=np.all(check[...,:3]==original[region][...,:3],axis=-1)
        assert np.mean(match)>.98, float(np.mean(match))
    # The hidden right shoulder must stay anatomically full in its own PNG.
    right_upper_core=(images["rightArm"][...,3]>=180)
    right_widths={y:area(right_upper_core[y]) for y in range(722,827,8)}
    assert min(right_widths.values())>=47,right_widths
    root_overlaps={name:area((images[name][:661,:,3]>180)&(images["backHair"][:661,:,3]>180))
                   for name in ("lockLeft","lockRight")}
    assert min(root_overlaps.values())>400,root_overlaps
    shoulder_alpha=images["shoulderCover"][...,3]
    shoulder_inside=cv2.distanceTransform((shoulder_alpha>96).astype(np.uint8),cv2.DIST_L2,5)>3
    assert np.all(shoulder_alpha[shoulder_inside]==255)
    for key in KEYS:
        blobs=connected(images[key][...,3])
        if key!="staff":
            assert len(blobs)==1,(key,blobs)
        else:
            main=max(blobs,key=lambda row:row[-1])
            x,y,w,h,_=main
            assert w>280 and h>420,main
    gx,gy=model["ground"]
    scale=model["unit"]
    joints=model["deformers"]
    points={name:(gx+(joints[name]["pivot"][0]-128)/scale,
                  gy+(joints[name]["pivot"][1]-256)/scale)
            for name in ("leftArm","rightArm","leftLeg","rightLeg","staff")}
    board=Image.new("RGB",(1320,770),"#303541")
    d=ImageDraw.Draw(board)
    minima={}
    visible_copper=[]
    cape_covers=[]
    opaque_cape_covers=[]
    rows_y=np.arange(SIZE[1])[:,None]

    def palm(art,lower):
        r0,g0,b0,alpha=np.moveaxis(art.astype(np.int16),-1,0)
        pixels=(alpha>96)&(r0>170)&(r0-b0>14)&(b0>145)&(rows_y>lower)
        rows,columns=np.where(pixels)
        return {"area":len(columns),"width":int(np.ptp(columns)+1),
                "height":int(np.ptp(rows)+1)}

    left=palm(images["leftArm"],880)
    right=palm(images["rightArm"],871)
    for row,mode in enumerate(("walk","run")):
        for col,phase in enumerate((0,.25,.5,.75)):
            stride=sin(tau*phase)
            swing=cos(tau*phase)
            run=mode=="run"
            a=12 if run else 6.3
            poses={
                "leftArm":(stride*(10 if run else 6.8),0),
                "rightArm":(-stride*(9 if run else 6.1),0),
                "leftLeg":(-stride*a,-max(0,swing)*6),
                "rightLeg":(stride*a,-max(0,-swing)*6),
                "staff":(stride*.8,0),
            }
            layers=images.copy()
            for name,(angle,lift) in poses.items():
                rt=cv2.getRotationMatrix2D(points[name],-angle,1)
                rt[1,2]+=lift
                layers[name]=warp(images[name],rt)
                if name!="staff":
                    touch=area((layers[name][...,3]>96)&(images["body"][...,3]>96))
                    minima[name]=min(minima.get(name,touch),touch)
            rr,gg,bb,aa=np.moveaxis(layers["rightArm"].astype(np.int16),-1,0)
            copper=(aa>96)&(rr-gg>11)&(gg-bb>22)&(rows_y>=707)&(rows_y<=799)
            copper &= (images["body"][...,3]<98)&(images["lockRight"][...,3]<98)
            visible_copper.append(area(copper))
            cape_covers.append(area((layers["leftArm"][...,3]>96)&(images["shoulderCover"][...,3]>96)))
            opaque_cape_covers.append(area((layers["leftArm"][...,3]>96)&(images["shoulderCover"][...,3]==255)))
            pose=Image.fromarray(compose_pose(layers))
            pose=pose.crop((180,44,985,1204))
            pose.thumbnail((316,349),Image.Resampling.LANCZOS)
            x=col*330+6
            y=row*385+30
            board.paste(pose,(x+(314-pose.width)//2,y),pose)
            d.text((x+6,y-12),f"{mode} / {phase:.2f}",fill="white")
    assert all(value>200 for value in minima.values()),minima
    assert min(visible_copper)>100 and min(cape_covers)>800,(visible_copper,cape_covers)
    board.save(REVIEW/"motion-check.jpg",quality=94)
    (REVIEW/"motion-audit.json").write_text(json.dumps(
        {"minimum_interior_alpha_overlap":minima,"staff_continuous_largest_core":main,
         "palm_bounds_pixels":{"viewerLeft":left,"viewerRight":right},
         "minimum_exposed_copper_pixels":min(visible_copper),
         "minimum_overlaid_cape_flap_pixels":min(cape_covers),
         "minimum_fully_opaque_cape_overlap":min(opaque_cape_covers),
         "solid_hair_root_overlap":root_overlaps,
         "right_upper_arm_width_pixels_by_row":right_widths,
         "tested":["walk","run"],"quarter_cycle_samples":[0,.25,.5,.75]},
        indent=2)+"\n",encoding="utf-8")
    print(minima)

if __name__=="__main__":
    main()
