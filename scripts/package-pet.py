"""Build a reproducible standalone preview ZIP."""
from pathlib import Path
import sys,json,hashlib,zipfile
R=Path(__file__).resolve().parents[1];name=sys.argv[1] if len(sys.argv)>1 else 'gpt-dragon-v005-r25';P=(R/'packs'/name).resolve();assert P.parent==R/'packs'
m=json.loads((P/'figure.json').read_text(encoding="utf-8"));model=json.loads((P/'model.json').read_text(encoding="utf-8"));lock=json.loads((R/'characters/original-01/production-lock.json').read_text(encoding="utf-8"))
assert m['id']==name and model['master_sha256']==lock['sha256']
assert hashlib.sha256((R/lock['active_master']).read_bytes()).hexdigest()==lock['sha256'], 'Locked master changed'
for key in ['entry','model','thumb']:assert (P/m[key]).is_file()
assert len({v['id'] for v in m['vocab']})==len(m['vocab'])
for v in m['vocab']:assert isinstance(v.get('seconds'),(int,float)) and v['seconds']>0, 'Each vocab word requires positive seconds (host API 2)'
D=R/'dist';D.mkdir(exist_ok=True);out=D/(name+'-'+m['version']+'.zip')
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(P.rglob('*')):
  if f.is_file():
   info=zipfile.ZipInfo(f.relative_to(P).as_posix(),date_time=(2026,10,13,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,f.read_bytes())
with zipfile.ZipFile(out) as z:assert z.testzip() is None
checksum=hashlib.sha256(out.read_bytes()).hexdigest()
(out.with_suffix('.zip.sha256')).write_text(checksum+'  '+out.name+'\n',encoding='ascii')
print(json.dumps({'file':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'declared_words':len(m['vocab']),'desktop_import':'not-tested'},indent=2))
