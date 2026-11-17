"""Check expression seams against the aligned painting and original pose."""

import json
import re
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw

from assemble import ROOT, load
from repair_eye_art import complexion, expression_palette, match_complexion, register_mood


PACK = ROOT/"pack/star-witch"
REVIEW = ROOT/"review"


def main():
    model = json.loads((PACK/"model.json").read_text(encoding="utf8"))
    manifest = json.loads((PACK/"figure.json").read_text(encoding="utf8"))
    vocabulary = Counter(name for word in manifest["vocab"]
                         for name in [word["id"],*sum(word["names"].values(),[])])
    assert max(vocabulary.values()) == 1
    assert all(not re.search(r"[,，、\s【】<>＜＞]",n) for n in vocabulary)
    assert all(word["seconds"] > 0 for word in manifest["vocab"])

    parts = model["parts"]
    for name in ("moodPortrait","talkPortrait","blinkFace","winkFace"):
        info = parts[name]
        _,_,w,h = info["box"]
        slots = info["columns"]
        n = info["count"]
        with Image.open(PACK/info["file"]) as asset:
            pixels = np.array(asset)
        assert pixels.shape == (h*((n+slots-1)//slots),w*slots,4)
        start = pixels[:h,:w,3]
        for i in range(n):
            dx,dy = i%slots*w,i//slots*h
            sample = pixels[dy:dy+h,dx:dx+w]
            assert np.array_equal(start,sample[:,:,3]), name
            assert np.all(sample[sample[:,:,3]==0,:3]==0), name

    source = Image.open(REVIEW/"standing-reassembled.png").convert("RGBA")
    info = parts["moodPortrait"]
    x,y,w,h = info["box"]
    atlas = Image.open(PACK/info["file"]).convert("RGBA")

    def frame(name):
        i = model["expressions"][name]
        columns = info["columns"]
        dx,dy = i%columns*w,i//columns*h
        pose = source.copy()
        pose.alpha_composite(atlas.crop((dx,dy,dx+w,dy+h)),(x,y))
        return pose

    angry = frame("angry")
    new = np.array(angry)
    original = np.array(source)
    outside = np.ones(original.shape[:2],bool)
    outside[y:y+h,x:x+w] = False
    assert np.array_equal(new[outside],original[outside])

    master = load("source/master-right.png")
    target,_ = expression_palette(master,load)
    paint,_ = register_mood(master,load("work/face-repair/mood-annoyed.png"))
    paint = match_complexion(paint,complexion(paint),target)
    # Compare the old joins below the eyes and above/beside the mouth with
    # the aligned painting. Measure only visible skin, excluding lash and hair.
    rows = np.arange(y,y+h)
    cols = np.arange(x,x+w)
    seam_points = (((rows>=585)&(rows<=608))[:,None]&((cols>=550)&(cols<=737))[None,:]
                   | ((rows>=603)&(rows<=633))[:,None]&
                     (np.isin(cols,[627,628,629,630,709,710,711,712]))[None,:])
    skin = (paint[:,:,0]>=222)&(paint[:,:,1]>=168)
    error = np.abs(new[y:y+h,x:x+w,:3].astype(np.int16)-paint)
    p95 = float(np.percentile(error[seam_points&skin],95))
    assert p95<=2, f"The old cheek join is still visible ({p95})"
    neutral_cheeks = complexion(original[y:y+h,x:x+w])
    raw_cheeks = complexion(master[y:y+h,x:x+w])
    names = ("happy","angry","surprised","shy","sad","confused","sleepy","dragged")
    checks = {name:complexion(np.array(frame(name))[y:y+h,x:x+w]) for name in names}
    for name in ("sitBody","sleepBody"):
        checks[name] = complexion(load(f"parts/{name}.png")[y:y+h,x:x+w])
    offsets = {name:float(np.max(np.abs(sample-neutral_cheeks))) for name,sample in checks.items()}
    assert max(offsets.values()) <= 2, offsets
    assert np.max(np.abs(neutral_cheeks-target)) < np.max(np.abs(raw_cheeks-target))
    comparison = Image.new("RGB",(1200,620),"#e4dbe5")
    captions = ImageDraw.Draw(comparison)
    layout = [("Master",Image.fromarray(master)),("Neutral",source)]
    layout += [(name.title(),frame(name)) for name in ("happy","angry","shy","dragged")]
    for i,(label,pose) in enumerate(layout):
        crop = pose.crop((449,453,802,651)).resize((386,217),Image.Resampling.LANCZOS)
        tx,ty = 400*(i%3),310*(i//3)
        captions.text((tx+8,ty+12),label,fill="#201923")
        comparison.paste(crop,(tx+7,ty+35),crop)
        color = tuple(int(channel) for channel in complexion(np.array(pose)[y:y+h,x:x+w]))
        captions.rectangle((tx+10,ty+266,tx+45,ty+290),fill=color)
        captions.text((tx+54,ty+271),f"Cheeks RGB {color}",fill="#201923")
    comparison.save(REVIEW/"complexion-compare.jpg",quality=98)

    preview = Image.new("RGB",(1280,468),"#e4dbe5")
    draw = ImageDraw.Draw(preview)
    for i,name in enumerate(names):
        pose = frame(name).crop((467,448,800,654))
        pose = pose.resize((310,192),Image.Resampling.LANCZOS)
        tx,ty = 320*(i%4),234*(i//4)
        preview.paste(pose,(tx+5,ty+31),pose)
        draw.text((tx+7,ty+10),name,fill="black")
    preview.save(REVIEW/"portraits-verified.jpg",quality=98)

    talk = Image.open(PACK/parts["talkPortrait"]["file"])
    speech_safe = np.zeros((h,w),bool)
    speech_safe[594-y:634-y,641-x:703-x] = True
    speech_review = Image.new("RGB",(1040,456),"#e4dbe5")
    draw = ImageDraw.Draw(speech_review)
    for row in range(parts["talkPortrait"]["count"]//4):
        neutral = np.array(talk.crop((0,row*h,w,(row+1)*h)))
        for phase in range(4):
            portrait = talk.crop((phase*w,row*h,(phase+1)*w,(row+1)*h))
            pixels = np.array(portrait)
            assert np.array_equal(neutral[~speech_safe],pixels[~speech_safe]), (row,phase)
            if phase:
                chin = pixels[625-y:640-y,650-x:690-x,1]
                prior_chin = neutral[625-y:640-y,650-x:690-x,1]
                assert np.min(chin[prior_chin>205])>182, (row,phase,"Unexpected pigment below the mouth")
                assert np.any(neutral!=pixels), (row,phase,"Missing speech opening")
            caption = {0:"Neutral",1:"Happy",1+model["expressions"]["sleepy"]:"Sleepy"}.get(row)
            if caption:
                dy = {"Neutral":0,"Happy":152,"Sleepy":304}[caption]
                crop = portrait.crop((624-x,587-y,713-x,635-y)).resize((245,128),Image.Resampling.LANCZOS)
                speech_review.paste(crop,(260*phase+6,dy+18),crop)
                draw.text((260*phase+6,dy+3),f"{caption} / {phase}",fill="black")
    speech_review.save(REVIEW/"talk-atlas-check.jpg",quality=98)

    before_file = REVIEW/"angry-seam-before.png"
    if before_file.is_file():
        compare = Image.new("RGB",(1296,385),"#ded4e0")
        text = ImageDraw.Draw(compare)
        before = Image.open(before_file).resize((630,354),Image.Resampling.LANCZOS)
        after = angry.crop((449,453,802,651)).resize((630,354),Image.Resampling.LANCZOS)
        for i,(image,label) in enumerate([(before,"Before"),(after,"After")]):
            compare.paste(image,(9+648*i,24),image)
            text.text((15+648*i,7),label,fill="black")
        compare.save(REVIEW/"angry-seam-compare.jpg",quality=98)

    report = {"moodPortraits":info["count"],"speechPortraits":parts["talkPortrait"]["count"],
              "seamSkinRgbErrorP95":p95,"pixelsChangedOutsidePortrait":0,
              "rawCheeks":raw_cheeks.tolist(),"neutralCheeks":neutral_cheeks.tolist(),
              "maxComplexionShiftByExpression":offsets,
              "vocabularyEntries":len(manifest["vocab"])}
    (REVIEW/"portrait-qa.json").write_text(json.dumps(report,indent=2),encoding="utf8")
    print(report)


if __name__=="__main__":
    main()
