"""Synthetic geometric art for adapter protocol tests; never a finished pet or art reference."""
from pathlib import Path
import json
from PIL import Image,ImageDraw

def make(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    repo=Path(__file__).resolve().parents[2]
    def png(name,kind,color):
        im=Image.new('RGBA',(160,160));d=ImageDraw.Draw(im)
        if kind=='head':d.ellipse((45,15,115,85),fill=color);d.ellipse((65,38,71,46),fill='#202124');d.ellipse((88,38,94,46),fill='#202124')
        elif kind=='body':d.rectangle((57,82,104,126),fill=color)
        elif kind=='arm':d.rectangle((108,86,123,123),fill=color)
        elif kind=='leg':d.rectangle((62,124,76,150),fill=color)
        else:d.ellipse((35,105,127,150),fill=color)
        im.save(root/(name+'.png'));return (root/(name+'.png')).relative_to(repo).as_posix()
    head=png('head','head','#c6aae0');variants={k:png(k,'head',c) for k,c in [('happy','#d6bcea'),('dizzy','#b4aadf'),('flustered','#efb7c8'),('blink','#b8a1d0')]}
    body=png('body','body','#8592cc');arm=png('arm','arm','#ccaacb');leg=png('leg','leg','#baaade');seated=png('seated','seat','#9a8ebe')
    composite=Image.new('RGBA',(160,160))
    for f in [leg,body,arm,head]:composite.alpha_composite(Image.open(repo/f))
    composite.save(root/'master.png')
    def part(id,file,role,poses,pivot,z,**kw):return {'id':id,'file':file,'role':role,'poses':poses,'pivot':pivot,'z':z,'owner':id,'reveals_when_moved':'diagnostic geometry only',**kw}
    spec={'id':'geometry-fixture','name':'Synthetic protocol fixture','author':'Test fixture','repository':'https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design','version':'0.0.1-test','provenance':'Synthetic rectangles/circles; protocol testing only','master':(root/'master.png').relative_to(repo).as_posix(),'center_x':80,'feet_y':150,'logo_scale':1.5,'bounds':[30,10,130,150],'hits':[[80,52,36],[80,110,30]],'anchors':{'gaze':[80,50],'bubble':[80,8]},'parts':[
        part('leg',leg,'leg',['standing'],[70,123],0,motion={'degrees':10,'hz':2}),
        part('body',body,'fixed',['standing'],[80,100],1),
        part('seat',seated,'fixed',['seated','dizzy'],[80,120],1),
        part('arm',arm,'wave-arm',['standing'],[112,85],2,motion={'degrees':-65,'swing':8}),
        part('head',head,'head',['standing','seated','dizzy'],[80,75],3,variants=variants)]}
    composite.crop((35,5,135,95)).save(root/'thumbnail.png');spec['thumbnail']=(root/'thumbnail.png').relative_to(repo).as_posix()
    target=root/'spec.json';target.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8');return target

if __name__=='__main__':
    print(make(Path(__file__).resolve().parents[2]/'scratch/layered-fixture'))
