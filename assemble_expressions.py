"""Assemble matched whole-portrait expression and blink textures."""

import json
import numpy as np
from PIL import Image

from assemble import ROOT, load, write_part
from dizzy_art import build_dizzy
from matched_blink import make_blink, portrait_alpha, sleeping_plate
from repair_eye_art import (FACE_BOX, MOODS, complexion, expression_palette, match_complexion,
                            register_mood, rgba, speech_frames)
OLD_TEXTURES = (
    "faceEyesBase","frontHairEyes","eyeLeftBed","eyeLeftNeutral","eyeRightBed",
    "eyeRightNeutral","eyeLeft","eyeRight","eyeLeftMood","eyeRightMood",
    "moodEyeLeft","moodEyeRight","moodFringeLeft","moodFringeRight","moodBrows","moodMouth",
    "mouth","browLeft","browRight","browLeftClean","browRightClean","dizzyPortrait",
)


def out_atlas(parts, name, frames, columns):
    l,t,r,b = FACE_BOX
    w,h = r-l,b-t
    rows = (len(frames)+columns-1)//columns
    output = Image.new("RGBA",(w*columns,h*rows))
    for i,frame in enumerate(frames):
        output.paste(Image.fromarray(frame),(w*(i%columns),h*(i//columns)))
    file = f"tex/{name}.png"
    output.save(ROOT/"pack/star-witch"/file)
    parts[name] = {"box":[l,t,w,h],"count":len(frames),"columns":columns,"file":file}


def main():
    path = ROOT/"pack/star-witch/model.json"
    model = json.loads(path.read_text(encoding="utf8"))
    parts = model["parts"]
    master = load("source/master-right.png")
    face,fringe = [Image.fromarray(load(f"parts/{name}.png")) for name in ("face","frontHair")]
    head = np.array(Image.alpha_composite(face,fringe))
    alpha = portrait_alpha(head)
    target,registered = expression_palette(master,load)
    mood_paints = [(match_complexion(paint,complexion(paint),target),score) for paint,score in registered]
    mood_frames = [rgba(paint,alpha) for paint,_ in mood_paints]
    model["expressions"] = {face:i for i,(_,faces) in enumerate(MOODS) for face in faces}

    talk,talk_fit = register_mood(master,load("work/face-repair/mood-talk.png"))
    l,t,r,b = FACE_BOX
    neutral_source = master[t:b,l:r,:3]
    neutral = match_complexion(neutral_source,complexion(neutral_source),target)
    speeches = [rgba(frame,alpha)
                for source in [neutral,*(paint for paint,_ in mood_paints)]
                for frame in speech_frames(source,talk)]

    face_paint = load("work/face-repair/face-opaque-painted.png")
    half_paint = load("work/face-repair/blink-half-matched.png")
    closed_paint = load("work/face-repair/blink-closed-matched.png")
    blink_frames,wink_frames,blink_fit = make_blink(master,head,face_paint,half_paint,closed_paint,target)
    seated = load("parts/sitBody.png")
    sleeping,sleep_fit = sleeping_plate(seated,closed_paint,target)
    dizzy_fit = build_dizzy(parts,model,master,seated,load("work/face-repair/mood-dizzy.png"),target)

    out_atlas(parts,"moodPortrait",mood_frames,4)
    out_atlas(parts,"talkPortrait",speeches,4)
    out_atlas(parts,"blinkFace",blink_frames,5)
    out_atlas(parts,"winkFace",wink_frames,5)
    write_part("sleepBody",Image.fromarray(sleeping),parts)
    obsolete = [parts.pop(name)["file"] for name in OLD_TEXTURES if name in parts]
    path.write_text(json.dumps(model,indent=2),encoding="utf8")
    for file in obsolete:
        (ROOT/"pack/star-witch"/file).unlink(missing_ok=True)

    w,h = r-l,b-t
    page = Image.new("RGB",(w*3,h*3),"#e4dfe7")
    for i,phase in enumerate(range(0,17,2)):
        background = Image.fromarray(np.dstack((neutral,master[t:b,l:r,3])))
        background.alpha_composite(Image.fromarray(blink_frames[phase]))
        page.paste(background,(w*(i%3),h*(i//3)),background)
    page.save(ROOT/"review/blink-atlases.png")
    report = {
        "seatFaceEcc":sleep_fit,
        "moodEcc":{name:quality for (name,_),(_,quality) in zip(MOODS,mood_paints)},
        "talkEcc":talk_fit,
        "blinkEcc":blink_fit,
        "dizzyEcc":dizzy_fit,
        "blinkFullFaceBox":FACE_BOX,
        "complexion":{"originalCheeks":complexion(neutral_source).tolist(),"targetCheeks":target.tolist()},
        "sourceCanvas":model["canvas"],
    }
    (ROOT/"review/eye-registration.json").write_text(json.dumps(report,indent=2),encoding="utf8")


if __name__ == "__main__":
    main()
