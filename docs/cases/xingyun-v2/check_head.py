"""Recompose the packed head at the limits of its actual JavaScript deformer."""
import json
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw

from assemble import ROOT, OUT, REVIEW, art_masks, clean, compose_pose, read, warp
from build import draft_assets

HEAD_PARTS = ("backHair", "lockLeft", "lockRight", "face", "eyeLeft", "eyeRight", "frontHair")
POSES = [
    ("Neutral", 0, 0, 0),
    ("Yaw left", -1.2, 0, 0),
    ("Yaw right", 1.2, 0, 0),
    ("Pitch up", 0, -1.2, 0),
    ("Pitch down", 0, 1.2, 0),
    ("Turn and tilt", 1.2, -1.2, 6),
]


def main():
    model = json.loads(draft_assets()["model.json"])
    parts = {part["id"]: part for part in model["parts"]}
    defs = model["deformers"]
    moving = (*HEAD_PARTS, *(name for name in ("ahoge","ahogeSeat") if name in parts))
    for key in (*moving, "mouthTalk", *(("mouthExpression",) if model.get("mouthAtlas") else ())):
        current = parts[key]["parent"]
        while current != "head":
            assert current != "neck", (key, "missed shared head deformer")
            current = defs[current]["parent"]

    unit = model["unit"]
    gx, gy = model["ground"]
    l,t,r,b = defs["head"]["rect"]
    points = np.array([
        [gx+(l-128)/unit, gy+(t-256)/unit],
        [gx+(r-128)/unit, gy+(t-256)/unit],
        [gx+(l-128)/unit, gy+(b-256)/unit],
    ], dtype=np.float32)
    nx, ny = defs["neck"]["pivot"]
    pivot = (gx+(nx-128)/unit, gy+(ny-256)/unit)
    script = """
import { headDisplacement } from './pack/xingyun-v2/figure.js';
const cases = JSON.parse(process.argv[1]);
console.log(JSON.stringify(cases.map(([, yaw, pitch]) =>
  [[0,0], [1,0], [0,1], [.35,.6]].map(([u,v]) => headDisplacement(u,v,yaw,pitch)))));
"""
    samples = json.loads(subprocess.run(
        ["node", "--input-type=module", "-e", script, json.dumps(POSES)],
        cwd=ROOT, check=True, capture_output=True, text=True).stdout)

    record = json.loads((OUT / "parts.json").read_text(encoding="utf-8"))
    layers = {key: read(OUT / f"{key}.png") for key in record["stack"]}
    visible = art_masks(clean(read(ROOT / "source/master.png")))
    head_area = visible["frontHair"] | visible["backHair"] | visible["face"]
    outside = (layers["backHair"][...,3]>0) & ~head_area
    assert not outside.any(), int(outside.sum())

    board = Image.new("RGB", (1290, 852), "#363946")
    label = ImageDraw.Draw(board)
    for i, ((name, yaw, pitch, roll), sample) in enumerate(zip(POSES, samples)):
        delta = np.asarray(sample, dtype=np.float32)
        assert np.allclose(delta[3], .05*delta[0]+.35*delta[1]+.6*delta[2], atol=1e-6)
        destination = points+delta[:3]/unit
        turn = cv2.getAffineTransform(points,destination.astype(np.float32))
        neck = cv2.getRotationMatrix2D(pivot,-roll,1)
        neck[1,2] += pitch*.25/unit
        matrix = neck @ np.vstack((turn,[0,0,1]))
        frame = {key:warp(art,matrix,cv2.INTER_LINEAR) if key in moving else art
                 for key,art in layers.items()}
        tile = Image.fromarray(compose_pose(frame)).crop((234,39,996,822))
        tile.thumbnail((412,394),Image.Resampling.LANCZOS)
        x,y = (i % 3)*430+5, (i // 3)*426+24
        board.paste(tile,(x+(420-tile.width)//2,y),tile)
        label.text((x,y-17),name,fill="white")

    board.save(REVIEW/"head-turn-check.png")
    print(f"{len(POSES)} head poses, no secondary rear outline outside the master")


if __name__ == "__main__":
    main()
