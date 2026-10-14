"""Guided, restartable repair workflow. No deployment or production writes."""
from pathlib import Path
import argparse
import contextlib
import hashlib
import io
import json
import math
import shutil
import sys
import zipfile
from types import SimpleNamespace
import project

ROOT = project.ROOT
CHECKLIST = ['full_character', 'light_dark', 'both_directions', 'defect_closeup', 'transitions_and_recovery']

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def fingerprint(pack):
    h = hashlib.sha256()
    for p in sorted(pack.rglob('*')):
        if p.is_symlink(): raise ValueError('Symlinks are not allowed in a deliverable')
        if p.is_file():
            h.update(p.relative_to(pack).as_posix().encode()); h.update(b'\0'); h.update(p.read_bytes())
    return h.hexdigest()

def load(job):
    if not project.re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', job): raise ValueError('Invalid job id')
    directory = project.rooted('scratch/jobs/'+job)
    state = project.read(directory/'job.json')
    pack = project.rooted(state['pack'])
    if pack.parent != ROOT/'scratch/candidates': raise ValueError('Job can only edit an isolated candidate')
    return directory, state, pack

def validate(directory, state, pack):
    with contextlib.redirect_stdout(io.StringIO()) as output:
        code = project.check(SimpleNamespace(pack=state['pack'], contract=state['contract'], strict_assets=False))
    report = json.loads(output.getvalue())
    report['pack_fingerprint'] = fingerprint(pack)
    write(directory/'machine.json', report)
    return code, report

def start(args):
    cfg = project.contract()
    if args.part not in cfg['parts']: raise ValueError('Choose part: '+', '.join(cfg['parts']))
    if not project.re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', args.job): raise ValueError('Invalid job id')
    directory = project.rooted('scratch/jobs/'+args.job)
    pack = project.rooted('scratch/candidates/'+args.job)
    if directory.exists() or pack.exists(): raise ValueError('Job/candidate already exists; use next instead')
    shutil.copytree(project.rooted(cfg['pack']), pack)
    state = {'schema':1,'job':args.job,'request':args.request,'part':args.part,'kind':args.kind,
             'pack':pack.relative_to(ROOT).as_posix(),'contract':'engineering/current-project.json',
             'baseline_fingerprint':fingerprint(pack),'production_pack':cfg['pack'],
             'identity':'Repair keeps published id/version; folder name is only isolation',
             'files_to_read':cfg['parts'][args.part]['pack_files'],'pitfalls':cfg['parts'][args.part]['pitfalls']}
    write(directory/'job.json',state)
    write(directory/'review-template.json',{'reviewer':'','qa_sha256':'','pack_fingerprint':'','checks':{k:False for k in CHECKLIST},'evidence':[],'notes':'','decision':'needs-review'})
    (directory/'TASK.md').write_text(f'# {args.request}\n\n目标部件：{args.part}；路线：{args.kind}。\n先读 `{cfg["parts"][args.part]["guide"]}`，只编辑 `{state["pack"]}`。\n\n改动入口：'+', '.join(state['files_to_read'])+'\n\n运行 `python engineering/tools/flow.py next --job '+args.job+'` 获取当前缺项。\n',encoding='utf-8')
    print(json.dumps(state,ensure_ascii=False,indent=2))
    return next_step(args)

def current_evidence(directory, pack):
    now=fingerprint(pack); result={}
    for name in ['machine','qa','review','package']:
        p=directory/(name+'.json')
        if p.exists():
            value=project.read(p)
            current=value.get('pack_fingerprint')==now
            if name=='qa':
                raw=project.rooted(value.get('input_file','scratch/missing-qa'))
                current=current and raw.is_file() and project.sha(raw)==value.get('input_sha256')
            if name=='package':
                archive=project.rooted(value.get('zip','scratch/missing-zip'))
                current=current and archive.is_file() and project.sha(archive)==value.get('sha256')
            result[name]={'current':current,'data':value}
    return result

def next_step(args):
    directory,state,pack=load(args.job);e=current_evidence(directory,pack)
    cmd='python engineering/tools/'
    if not e.get('machine',{}).get('current'):
        step='编辑候选后执行机器检查'; command=f'{cmd}flow.py validate --job {args.job}'
    elif not e['machine']['data']['passed']:
        step='修复 machine.json 列出的错误';command=f'{cmd}flow.py validate --job {args.job}'
    elif not e.get('qa',{}).get('current') or not e['qa']['data'].get('machine_passed'):
        step='采样动作、恢复过程和拖拽；需要 Playwright + Pillow'; command=f'uv run --project engineering python engineering/tools/collect_qa.py --job {args.job}'
    elif not e.get('review',{}).get('current') or e['review']['data'].get('decision')!='pass':
        step='打开 qa/contact.jpg 和问题区完整帧，填写 review-template.json；机器通过不等于美术通过'
        command=f'{cmd}flow.py review --job {args.job} --file scratch/jobs/{args.job}/review-template.json'
    elif not e.get('package',{}).get('current'):
        step='打包候选；保持生产目录与安装版不变';command=f'{cmd}flow.py package --job {args.job}'
    else:
        step='本地交付包就绪；按用户授权导入真实宿主并记录复核，之后再发布';command=f'{cmd}flow.py installed --job {args.job} --directory <实际安装目录>'
    print(json.dumps({'next':step,'command':command,'request':state['request'],'changed_from_baseline':fingerprint(pack)!=state['baseline_fingerprint'],'evidence':{k:v['current'] for k,v in e.items()}},ensure_ascii=False,indent=2))
    return 0

def check_job(args):
    directory,state,pack=load(args.job);code,report=validate(directory,state,pack)
    print(json.dumps(report,ensure_ascii=False,indent=2));return code

def registration(args):
    directory,state,pack=load(args.job)
    if not all(math.isfinite(v) for v in [args.dx,args.dy,args.scale,args.angle]) or args.scale<=0: raise ValueError('Use finite positive uniform scale')
    reg=project.read(pack/'part-registration.json')
    if args.part not in reg or len(reg[args.part])!=6: raise ValueError('Unknown registration part')
    a,b,c,d,e,f=reg[args.part]
    if abs(a*c+b*d)>1e-6 or abs(math.hypot(a,b)-math.hypot(c,d))>1e-6: raise ValueError('Existing transform is not a similarity; diagnose first')
    angle=math.radians(args.angle);u=args.scale*math.cos(angle);v=args.scale*math.sin(angle)
    # Local scale/rotation about source origin. Explicit translation remains in destination pixels.
    reg[args.part]=[a*u+c*v,b*u+d*v,-a*v+c*u,-b*v+d*u,e+args.dx,f+args.dy]
    model=project.read(pack/'model.json');model['part_registration']=reg
    backup=directory/'registration-history.json';history=project.read(backup) if backup.exists() else []
    history.append({'part':args.part,'before':[a,b,c,d,e,f],'after':reg[args.part]});write(backup,history)
    write(pack/'part-registration.json',reg);write(pack/'model.json',model)
    print(json.dumps(history[-1],indent=2));return next_step(args)

def review(args):
    directory,state,pack=load(args.job);qa=project.read(directory/'qa.json');r=project.read(Path(args.file))
    current=fingerprint(pack)
    if not qa.get('machine_passed') or qa['pack_fingerprint']!=current: raise ValueError('QA missing, failed or stale; resample current candidate')
    if r.get('qa_sha256')!=qa['input_sha256'] or r.get('pack_fingerprint')!=current: raise ValueError('Copy current qa_sha256 and pack_fingerprint from qa.json after viewing its frames')
    if not r.get('reviewer','').strip() or not r.get('notes','').strip(): raise ValueError('Record actual reviewer and concrete findings')
    if r.get('decision') not in ['pass','fail']: raise ValueError('Use pass or fail decision')
    if r['decision']=='pass' and not all(r.get('checks',{}).get(k) is True for k in CHECKLIST): raise ValueError('Each visual check must be reviewed; missing checklist')
    paths=r.get('evidence',[])
    if len(paths)<2: raise ValueError('Link full character/contact sheet and defect-detail evidence')
    qa_root=(directory/'qa').resolve()
    for path in paths:
        file=project.rooted(path)
        if not file.is_relative_to(qa_root) or not file.is_file(): raise ValueError('Evidence must be a current QA file in this job')
    r['evidence_hashes']={p:project.sha(project.rooted(p)) for p in paths}
    write(directory/'review.json',r)
    return next_step(args)

def package(args):
    directory,state,pack=load(args.job)
    code,report=validate(directory,state,pack)
    if code: raise ValueError('Machine check failed; see machine.json')
    e=current_evidence(directory,pack)
    for name in ['qa','review']:
        if not e.get(name,{}).get('current'): raise ValueError(name+' evidence is stale or missing')
    qa=e['qa']['data'];review=e['review']['data']
    if not qa.get('machine_passed') or review.get('decision')!='pass' or review.get('qa_sha256')!=qa['input_sha256']: raise ValueError('Current visual review required')
    if not all(review.get('checks',{}).get(k) is True for k in CHECKLIST) or not review.get('notes') or not review.get('reviewer'): raise ValueError('Incomplete review')
    for path,digest in review['evidence_hashes'].items():
        if project.sha(project.rooted(path))!=digest: raise ValueError('Reviewed evidence changed')
    manifest=project.read(pack/'figure.json');out=directory/'artifacts';out.mkdir(exist_ok=True)
    name=manifest['id']+'-'+manifest['version']+'.zip'
    if Path(name).name!=name or '/' in name or '\\' in name: raise ValueError('Invalid filename metadata')
    target=out/name
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for file in sorted(pack.rglob('*')):
            if file.is_file():
                info=zipfile.ZipInfo(file.relative_to(pack).as_posix(),date_time=(2026,10,13,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,file.read_bytes())
    with zipfile.ZipFile(target) as z:
        if z.testzip() is not None: raise ValueError('ZIP CRC failure')
    receipt={'pack_fingerprint':fingerprint(pack),'zip':target.relative_to(ROOT).as_posix(),'sha256':project.sha(target),'bytes':target.stat().st_size,'native_host':'not-tested','published':False}
    write(directory/'package.json',receipt);(out/'SHA256.txt').write_text(receipt['sha256']+'  '+name+'\n',encoding='ascii')
    print(json.dumps(receipt,ensure_ascii=False,indent=2));return 0

def installed(args):
    directory,state,pack=load(args.job);target=Path(args.directory).resolve()
    expected=project.read(pack/'figure.json')['id']
    if project.read(target/'figure.json')['id']!=expected: raise ValueError('Installed id differs from candidate')
    mismatch=[p.relative_to(pack).as_posix() for p in pack.rglob('*') if p.is_file() and (not (target/p.relative_to(pack)).is_file() or project.sha(p)!=project.sha(target/p.relative_to(pack)))]
    extras=[p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file() and not (pack/p.relative_to(target)).is_file()]
    report={'pack_fingerprint':fingerprint(pack),'directory':str(target),'files_match':not mismatch and not extras,'mismatches':mismatch,'extra_files':extras,'runtime_visual':'not-tested','restart_dpi_multimonitor':'not-tested'}
    write(directory/'installed.json',report);print(json.dumps(report,ensure_ascii=False,indent=2));return int(bool(mismatch or extras))

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    for command,fn in [('start',start),('next',next_step),('validate',check_job),('registration',registration),('review',review),('package',package),('installed',installed)]:
        p=sub.add_parser(command);p.add_argument('--job',required=True);p.set_defaults(run=fn)
        if command=='start':
            p.add_argument('--part',required=True);p.add_argument('--kind',choices=['motion','art','occlusion'],required=True);p.add_argument('--request',required=True)
        if command=='registration':
            p.add_argument('--part',required=True)
            for name,default in [('dx',0),('dy',0),('scale',1),('angle',0)]:p.add_argument('--'+name,type=float,default=default)
        if command=='review':p.add_argument('--file',required=True)
        if command=='installed':p.add_argument('--directory',required=True)
    args=parser.parse_args()
    try:return args.run(args)
    except (ValueError,OSError,KeyError,TypeError) as e: print('ERROR: '+str(e),file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
