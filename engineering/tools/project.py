"""Portable engineering helpers. Standard library except optional QA contact sheets."""
from pathlib import Path
import argparse
import base64
import hashlib
import importlib.util
import io
import json
import math
import re
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def rooted(path):
    p = (ROOT / path).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError('Path must stay within repository: ' + str(path))
    return p

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def png_info(path):
    b = Path(path).read_bytes()
    if b[:8] != b'\x89PNG\r\n\x1a\n' or b[12:16] != b'IHDR':
        raise ValueError('Invalid PNG: ' + str(path))
    width, height = struct.unpack('>II', b[16:24])
    return {'width': width, 'height': height, 'bit_depth': b[24], 'color_type': b[25]}

def contract(path='engineering/current-project.json'):
    return read(rooted(path))

def pack_path(args, cfg):
    return rooted(args.pack or cfg['pack'])

def doctor(args):
    tools = {name: shutil.which(name) for name in ['python', 'node', 'ffmpeg', 'uv', 'git']}
    tools['running_python'] = sys.executable
    modules = {name: importlib.util.find_spec(name) is not None for name in ['PIL', 'numpy', 'cv2']}
    print(json.dumps({'tools': tools, 'art_modules': modules, 'basic_requirements': 'Python + Node; ffmpeg/uv only for video'}, ensure_ascii=False, indent=2))
    return 1 if not tools['node'] or (args.art and not all(modules.values())) else 0

def check(args):
    cfg = contract(args.contract)
    p = pack_path(args, cfg)
    errors, notices = [], []
    def require(ok, message):
        if not ok:
            errors.append(message)
    try:
        m, model = read(p / 'figure.json'), read(p / 'model.json')
        lock = read(rooted(cfg['source_lock']))
        require(sha(rooted(lock['active_master'])) == lock['sha256'] == model['master_sha256'], 'Master hash mismatch')
        require(model['canvas'] == lock['canvas'], 'Master canvas mismatch')
        require(m['manifest'] == 2 and m['api'] == 2, 'Requires Coopanion API 2 manifest')
        require(bool(re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', m['id'])) and m['id'] not in ['coo', 'whale'], 'Invalid/custom reserved id')
        require(bool(m.get('author')) and bool(m.get('name')), 'Missing author/name')
        source = read(p / 'SOURCE.json')
        require(source['version'] == m['version'] and source['author'] == m['author'] and source['repository'] == m['homepage'], 'SOURCE/manifest attribution mismatch')
        for key in ['entry', 'model', 'thumb']:
            value = Path(m[key])
            require(not value.is_absolute() and (p / value).resolve().is_relative_to(p) and (p / value).is_file(), 'Missing/unsafe entry: ' + key)
        ids = [v['id'] for v in m['vocab']]
        require(len(ids) == len(set(ids)) == cfg['declared_words'], 'Duplicate or unexpected vocab count')
        for v in m['vocab']:
            require(isinstance(v.get('seconds'), (int, float)) and math.isfinite(v['seconds']) and v['seconds'] > 0, 'Invalid duration: ' + v['id'])
        reg = read(p / 'part-registration.json')
        require(reg == model['part_registration'], 'Embedded registration does not match editable registration')
        for name in ['arm-left', 'arm-right']:
            a,b,c,d,e,f = reg[name]
            require(all(math.isfinite(x) for x in reg[name]), 'Nonfinite registration: ' + name)
            require(abs(a*c+b*d) < 1e-6 and abs(math.hypot(a,b)-math.hypot(c,d)) < 1e-6 and a*d-b*c > 0, 'Arm shear/nonuniform scale/reflection: ' + name)
        for key, value in cfg['elasticity'].items():
            require(model['leg_rig']['elasticity'][key] == value, 'Accepted elasticity changed: ' + key)
        require(model['sitting_feet_y'] == cfg['sitting_feet_y'], 'Seated feet baseline changed')
        entry = (p / m['entry']).read_text(encoding='utf-8')
        require('model.part_registration' in entry, 'Missing CSP-safe embedded registration load')
        require(not re.search(r'fetch\s*\([^\n;]*part-registration', entry), 'Extra registration fetch is blocked by host CSP')
        for module in p.glob('*.js'):
            text = module.read_text(encoding='utf-8')
            for dep in re.findall(r'\bfrom\s*[\'"]([.][^\'"]+)[\'"]', text):
                require((module.parent / dep).resolve().is_relative_to(p) and (module.parent / dep).is_file(), 'Missing module dependency: ' + dep)
        for file in cfg['required_pack_files']:
            require((p / file).is_file(), 'Missing release file: ' + file)
        for part in cfg['parts'].values():
            for file in part['pack_files']:
                require((p / file).is_file(), 'Missing part file: ' + file)
        inventory = read(rooted('engineering/asset-inventory.json'))
        changes = []
        for asset in inventory['textures']:
            f = p / asset['path']
            require(f.is_file(), 'Missing baseline texture: ' + asset['path'])
            if f.is_file():
                info = png_info(f)
                require(info['color_type'] == 6, 'Texture must be RGBA: ' + asset['path'])
                if sha(f) != asset['sha256']:
                    changes.append(asset['path'])
        if changes:
            (errors if args.strict_assets else notices).append('Changed baseline textures (require visual evidence): ' + ', '.join(changes))
        if p == rooted(cfg['pack']):
            require(m['id'] == cfg['id'] and m['version'] == cfg['version'] and m['author'] == cfg['author'], 'Current-project identity drift')
        failures = read(rooted('engineering/cases/failures.json'))
        for case in failures['cases']:
            for file in case['evidence']:
                require(rooted(file).is_file(), 'Missing case evidence: ' + file)
        for asset in read(rooted('engineering/source-assets.json'))['assets']:
            require(rooted(asset['path']).is_file(), 'Missing production source: ' + asset['path'])
            if rooted(asset['path']).is_file():
                require(sha(rooted(asset['path'])) == asset['sha256'], 'Production source hash mismatch: ' + asset['path'])
        skill = rooted('.agents/skills/coopanion-image-pack/SKILL.md')
        for match in re.findall(r'\]\(([^)]+)\)', skill.read_text(encoding='utf-8')):
            if not match.startswith('http'):
                require((skill.parent / match).resolve().is_file(), 'Broken skill reference: ' + match)
    except (KeyError, ValueError, OSError, TypeError) as exc:
        errors.append(str(exc))
    result = {'passed': not errors, 'pack': str(p.relative_to(ROOT)), 'errors': errors, 'notices': notices, 'scope': 'machine contracts only; visual/native-host acceptance is separate'}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(bool(errors))

def inspect(args):
    cfg = contract()
    if args.part not in cfg['parts']:
        print('Parts: ' + ', '.join(cfg['parts']))
        return 1
    print(json.dumps(cfg['parts'][args.part], ensure_ascii=False, indent=2))
    return 0

def case(args):
    rows = read(rooted('engineering/cases/failures.json'))['cases']
    selected = [c for c in rows if args.id in c['id'] or args.id in c['symptom']]
    if not selected:
        print('Cases: ' + ', '.join(c['id'] for c in rows))
        return 1
    print(json.dumps(selected, ensure_ascii=False, indent=2))
    return 0

def candidate(args):
    cfg = contract()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', args.id) or args.id in ['coo','whale',cfg['id']]:
        raise ValueError('Choose a new nonreserved id')
    out = rooted('scratch/candidates/' + args.id)
    if out.exists():
        raise ValueError('Candidate exists; leave unchanged: ' + str(out))
    shutil.copytree(rooted(cfg['pack']), out)
    m = read(out / 'figure.json')
    original = {'id': m['id'], 'author': m['author'], 'version': m['version']}
    m.update(id=args.id, name={'zh': args.name}, author=args.author, version='0.1.0-candidate')
    (out / 'figure.json').write_text(json.dumps(m, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    source = read(out / 'SOURCE.json')
    source.update(name=args.name, author=args.author, version=m['version'], derived_from=original)
    (out / 'SOURCE.json').write_text(json.dumps(source, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (out / 'README.md').write_text(f'# {args.name}\n\n实验副本，作者 {args.author}。结构与素材来源：{original["author"]} 的 GPT 龙娘 {original["version"]}。尚未改为新的原创角色，也未安装或发布。\n', encoding='utf-8')
    print(str(out))
    print('Preview: http://127.0.0.1:4319/preview/engineering.html?pack=scratch/candidates/' + args.id)
    return 0

def compare(args):
    cfg = contract();p = pack_path(args, cfg);installed = Path(args.installed).resolve()
    if not (installed / 'figure.json').is_file():
        raise ValueError('Point to the exact installed pack directory')
    mismatches = []
    for source in p.rglob('*'):
        if source.is_file():
            rel = source.relative_to(p);target = installed / rel
            if not target.is_file() or sha(source) != sha(target):
                mismatches.append(str(rel))
    print(json.dumps({'read_only': True, 'installed': str(installed), 'match': not mismatches, 'mismatches': mismatches}, ensure_ascii=False, indent=2))
    return int(bool(mismatches))

def qa(args):
    from PIL import Image, ImageDraw
    data = read(Path(args.input));samples = data.get('samples', []);out = rooted(args.out)
    if not samples:
        raise ValueError('QA must include sampled frames')
    out.mkdir(parents=True, exist_ok=True)
    colors = [('light','#e9e4f1'), ('dark','#202124')]
    sheet = Image.new('RGB',(960,320*math.ceil(len(samples)/3)), '#202124')
    draw = ImageDraw.Draw(sheet)
    def finite(value):
        if isinstance(value,float):return math.isfinite(value)
        if isinstance(value,dict):return all(finite(v) for v in value.values())
        if isinstance(value,list):return all(finite(v) for v in value)
        return True
    bad = []
    for i,sample in enumerate(samples):
        if not finite({k:v for k,v in sample.items() if k!='png'}):bad.append(i)
        png = sample['png'];raw = base64.b64decode(png.split(',',1)[1], validate=True)
        im = Image.open(io.BytesIO(raw)).convert('RGBA')
        for label,color in colors:
            bg=Image.new('RGBA',im.size,color);bg.alpha_composite(im);bg.convert('RGB').save(out/f'{i:03d}-{label}.png')
            thumb=bg.convert('RGB');thumb.thumbnail((160,270));sheet.paste(thumb,((i%3)*320+(label=='dark')*160,(i//3)*320))
        text=f'{i} {sample.get("word","frame")} f={sample.get("frame","")} facing={sample.get("facing",sample.get("layout",{}).get("facing",""))}'
        draw.text(((i%3)*320+8,(i//3)*320+277),text,fill='#eee9f5')
    sheet.save(out/'contact.jpg')
    rejected=[x for x in data.get('checks',[]) if x.get('accepted') is False]
    report={'samples':len(samples),'nonfinite_samples':bad,'rejected_actions':rejected,'machine_passed':not bad and not rejected,'visual_review':'required','input':str(Path(args.input).resolve())}
    (out/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2));return int(bool(bad or rejected))

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    d=sub.add_parser('doctor');d.add_argument('--art',action='store_true');d.set_defaults(run=doctor)
    c=sub.add_parser('check');c.add_argument('--pack');c.add_argument('--contract',default='engineering/current-project.json');c.add_argument('--strict-assets',action='store_true');c.set_defaults(run=check)
    i=sub.add_parser('inspect');i.add_argument('part');i.set_defaults(run=inspect)
    f=sub.add_parser('case');f.add_argument('id');f.set_defaults(run=case)
    b=sub.add_parser('candidate');b.add_argument('--id',required=True);b.add_argument('--name',required=True);b.add_argument('--author',required=True);b.set_defaults(run=candidate)
    m=sub.add_parser('compare');m.add_argument('--pack');m.add_argument('--installed',required=True);m.set_defaults(run=compare)
    q=sub.add_parser('qa');q.add_argument('--input',required=True);q.add_argument('--out',required=True);q.set_defaults(run=qa)
    args=parser.parse_args()
    try:return args.run(args)
    except (ValueError,OSError,ImportError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
