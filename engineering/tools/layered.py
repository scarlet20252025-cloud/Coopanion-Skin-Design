"""Compile prepared original RGBA layers into a small Coopanion kit adapter and guided job."""
from pathlib import Path
import argparse
import json
import math
import shutil
import sys
import project
import flow

def compile_spec(spec_path,job):
    from PIL import Image
    spec=project.read(spec_path);master=project.rooted(spec['master'])
    with Image.open(master) as im:
        canvas=im.size
        if im.mode!='RGBA' or im.format!='PNG':raise ValueError('Master must be RGBA PNG')
    if not project.re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',job):raise ValueError('Invalid job id')
    if not project.re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',spec['id']) or spec['id'] in ['coo','whale',project.contract()['id']]:raise ValueError('New character requires its own nonreserved id')
    for key in ['name','author','repository','version','provenance']:
        if not isinstance(spec.get(key),str) or not spec[key].strip() or '填写' in spec[key]:raise ValueError('Fill '+key)
    if not spec['repository'].startswith(('https://','http://')):raise ValueError('Provide actual repository URL')
    if not project.re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.+-]{0,63}',spec['version']):raise ValueError('Invalid version filename')
    if not spec['parts']:raise ValueError('Supply prepared semantic layers first')
    pack=project.rooted('scratch/candidates/'+job);directory=project.rooted('scratch/jobs/'+job)
    if pack.exists() or directory.exists():raise ValueError('Job exists; build with a new job id')
    parts=spec['parts'];ids=[p['id'] for p in parts]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate part id')
    thumbnail=project.rooted(spec['thumbnail'])
    with Image.open(thumbnail) as im:
        if im.mode!='RGBA' or im.format!='PNG':raise ValueError('Thumbnail must be a prepared RGBA PNG upper-body crop')
    files={master,thumbnail};roles=set();poses=set()
    def finite(values):return all(type(v) in (int,float) and math.isfinite(v) for v in values)
    for p in parts:
        if not project.re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',p['id']):raise ValueError('Invalid part id')
        if p['role'] not in ['fixed','head','wave-arm','wing','leg']:raise ValueError('Invalid role: '+p['id'])
        roles.add(p['role']);poses.update(p['poses'])
        if not p['poses'] or not set(p['poses'])<= {'standing','seated','dizzy'}:raise ValueError('Invalid poses')
        if len(p['pivot'])!=2 or not finite([*p['pivot'],p['z'],p.get('wave_z',p['z'])]):raise ValueError('Finite pivot/depth required')
        if not (0<=p['pivot'][0]<=canvas[0] and 0<=p['pivot'][1]<=canvas[1]):raise ValueError('Pivot outside master: '+p['id'])
        if not p.get('owner') or not p.get('reveals_when_moved') or '填写' in p['owner']+p['reveals_when_moved']:raise ValueError('Record pixel owner and revealed area (use "none" where appropriate)')
        if p['role'] in ['wave-arm','wing','leg']:
            motion=p['motion'];keys=['degrees','swing'] if p['role']=='wave-arm' else ['degrees','hz']
            if not finite([motion[k] for k in keys]):raise ValueError('Finite motion parameters required')
        if p['role']=='head' and not {'happy','dizzy','flustered','blink'}<=set(p.get('variants',{})):raise ValueError('Head needs happy/dizzy/flustered/blink art')
        for name in [p['file'],*p.get('variants',{}).values()]:
            path=project.rooted(name)
            with Image.open(path) as im:
                if im.format!='PNG' or im.mode!='RGBA' or im.size!=canvas or im.getbbox() is None or im.getchannel('A').getextrema()[0]!=0:raise ValueError('Transparent RGBA, nonempty full-master canvas required: '+name)
            files.add(path)
    if poses!={'standing','seated','dizzy'} or not {'head','wave-arm','leg'}<=roles:raise ValueError('Starter requires standing/seated/dizzy art and head/wave-arm/leg roles')
    if not finite([spec['center_x'],spec['feet_y'],spec['logo_scale'],*spec['bounds']]) or spec['logo_scale']<=0 or len(spec['bounds'])!=4:raise ValueError('Invalid source geometry')
    if not (0<=spec['center_x']<=canvas[0] and 0<spec['feet_y']<=canvas[1]):raise ValueError('Invalid center/feet')
    if not spec['hits'] or any(len(h)!=3 or not finite(h) or h[2]<=0 for h in spec['hits']):raise ValueError('Provide finite source-space hit circles')
    if not {'gaze','bubble'}<=set(spec['anchors']):raise ValueError('Provide gaze/bubble anchors in source pixels')
    for value in spec['anchors'].values():
        if len(value)<2 or not finite(value):raise ValueError('Invalid anchor')
    pack.mkdir(parents=True);directory.mkdir(parents=True);(pack/'tex').mkdir()
    mapping={};inventory=[];sources=[]
    for i,path in enumerate(sorted(files)):
        target=f'tex/source-{i:03d}.png';shutil.copyfile(path,pack/target);mapping[path.relative_to(project.ROOT).as_posix()]=target
        with Image.open(path) as im:size=im.size
        inventory.append({'path':target,'sha256':project.sha(path),'width':size[0],'height':size[1]})
        sources.append({'path':path.relative_to(project.ROOT).as_posix(),'sha256':project.sha(path)})
    for p in parts:
        p['file']=mapping[p['file']];p['variants']={k:mapping[v] for k,v in p.get('variants',{}).items()}
    words=['neutral','happy','stand','wave','walk','run','jump','sit','dizzy','turn','dance']
    reg={p['id']:[1,0,0,1,0,0] for p in parts};model={k:spec[k] for k in ['center_x','feet_y','logo_scale','bounds','hits','anchors']}
    model.update(canvas=list(canvas),master_sha256=project.sha(master),parts=parts,words=words,part_registration=reg,accent=spec.get('accent','#a18acb'))
    manifest={'manifest':2,'api':2,'id':spec['id'],'name':{'zh':spec['name']},'version':spec['version'],'author':spec['author'],'homepage':spec['repository'],'entry':'figure.js','export':'createLayeredBody','model':'model.json','thumb':mapping[spec['thumbnail']],
              'vocab':[{'id':w,'kind':'expression' if w in ['neutral','happy'] else 'motion','seconds':4,'names':{'zh':[w]}} for w in words]}
    flow.write(pack/'figure.json',manifest);flow.write(pack/'model.json',model);flow.write(pack/'part-registration.json',reg)
    shutil.copyfile(project.ROOT/'engineering/templates/layered-figure.js',pack/'figure.js')
    shutil.copyfile(project.ROOT/'packs/gpt-dragon-v005-r25/LICENSE',pack/'LICENSE')
    flow.write(pack/'SOURCE.json',{'author':spec['author'],'version':spec['version'],'repository':spec['repository'],'provenance':spec['provenance'],'runtime':'repository layered-figure.js and Coopanion host kit; preserve bundled license'})
    (pack/'README.md').write_text(f'# {spec["name"]}\n\n作者：{spec["author"]}\n\n仓库：{spec["repository"]}\n\nCoopanion 形象包，装扮 → 导入 ZIP。当前为未经宿主验收的刚性分层候选。\n',encoding='utf-8')
    flow.write(directory/'source-lock.json',{'active_master':spec['master'],'sha256':project.sha(master),'canvas':list(canvas)})
    flow.write(directory/'assets.json',{'textures':inventory});flow.write(directory/'sources.json',{'assets':sources})
    rel=directory.relative_to(project.ROOT).as_posix();cfg={'profile':'layered-v1','id':spec['id'],'author':spec['author'],'version':spec['version'],'pack':pack.relative_to(project.ROOT).as_posix(),'source_lock':rel+'/source-lock.json','declared_words':len(words),
         'uniform_registration':ids,'parts':{'body':{'pack_files':['figure.js','model.json']}},'required_pack_files':['README.md','LICENSE','SOURCE.json'],'asset_inventory':rel+'/assets.json','source_assets':rel+'/sources.json'}
    flow.write(directory/'contract.json',cfg)
    flow.write(directory/'job.json',{'schema':1,'job':job,'request':'Build '+spec['name'],'part':'body','kind':'new-character','pack':cfg['pack'],'contract':rel+'/contract.json','baseline_fingerprint':flow.fingerprint(pack)})
    flow.write(directory/'review-template.json',{'reviewer':'','qa_sha256':'','pack_fingerprint':'','checks':{k:False for k in flow.CHECKLIST},'evidence':[],'notes':'','decision':'needs-review'})
    print('Built isolated candidate. Next: python engineering/tools/flow.py validate --job '+job)
    return cfg

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--spec',required=True);p.add_argument('--job',required=True);args=p.parse_args()
    try:compile_spec(args.spec,args.job);return 0
    except (ValueError,OSError,KeyError,TypeError) as e:print('ERROR: '+str(e),file=sys.stderr);return 1
    except ImportError:print('Install tools: uv sync --project engineering',file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
