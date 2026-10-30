from pathlib import Path
import hashlib,json,shutil
P=Path(__file__).resolve().parent;ROOT=P.parents[2];base=ROOT/'scratch/candidates/atri-hair-junctions'
model=json.loads((base/'model.json').read_text());frozen=P/'preserved-expressions';frozen.mkdir(exist_ok=True)
selected=[p for p in model['parts'] if any(t in p['id'] for t in ['eye','closed','brow','forehead','pinch-mouth'])]
files={p['file'] for p in selected}|{'figure.js','model.json','part-registration.json'}
hashes={}
for file in sorted(files):
 src=base/file;dst=frozen/file;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);hashes[file]=hashlib.sha256(src.read_bytes()).hexdigest()
manifest={'user_instruction':'表情动态是合格的可以保留','baseline':str(base.relative_to(ROOT)).replace('\\','/'),'scope':'Preserve current expression assets, expression rig and blink/expression/recovery behavior. Other body and hair regeneration continues.','files':hashes,'expression_rig':model['expression_rig'],'parts':selected,'status':'user approved expression dynamics; integration with new art not yet tested'}
(P/'expression-lock.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
c=json.loads((P/'contract.json').read_text());c['scope_exception']={'expressions':'Preserve user-approved current expression dynamics and supporting textures/rig. Do not regenerate expression variants.','lock':'expression-lock.json'};(P/'contract.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
d=P.parent/'design-selection.json';obj=json.loads(d.read_text());obj['expression_status']='2026-10-15 user approved current expression dynamics; preserve blink, expression switching and recovery. New component integration remains untested.';obj['protected_expressions']['current_dynamics']='official-regeneration/expression-lock.json';d.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
progress=json.loads((P/'progress.json').read_text());progress['pending']=[x for x in progress['pending'] if x!='expression-variants'];progress['preserved']='expression-lock.json';(P/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for update in progress.get('attempt_corrections',[]):
 dst=P/update['file'];old=json.loads(dst.read_text()) if dst.exists() else {};old.update({k:v for k,v in update.items() if k!='file'});dst.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'locked_files':len(files),'expression_parts':len(selected),'base':str(base)}))
