from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;root=P.parents[2]
lock=json.loads((P/'expression-lock.json').read_text(encoding='utf-8'))
changed=[f for f,h in lock['files'].items() if hashlib.sha256((root/lock['baseline']/f).read_bytes()).hexdigest()!=h]
assert not changed,changed
report={'date':'2026-10-15','status':'eight static samples visually reviewed; no duplicate eyes or mouth seen','samples':['neutral-open','happy','scared','flustered','blink-.4','blink-.76','blink-1','neutral-open-recovery'],'renderer':'original buildFace/paintFace copied verbatim','original_files_checked':len(lock['files']),'original_files_changed':changed,'limits':['Static integration only; real timing not retested','Standing only; seated integration pending','Not whole-character acceptance','New hairstyle is NOT accepted']}
(P/'expression-compatibility-review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
f=P/'progress.json';d=json.loads(f.read_text(encoding='utf-8'))
d['phase']='independent hair generation failed strict contour check; official visible-pixel workflow clarification pending'
d['rejected']=list(dict.fromkeys(d['rejected']+['ponytails-pair-01','pony-pair-right-01']))
d['diagnostic_sources']=list(dict.fromkeys(d.get('diagnostic_sources',[])+['hair-system-02','rear-system-01']))
d['pending_user_choice']='Allow official mother-visible-pixels plus generated hidden fill and computed masks, or continue all-new-pixels generations. No consent inferred.'
d['expression_review']='expression-compatibility-review.json'
f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for n in [33]:
 f=P/f'attempt-{n}.json';a=json.loads(f.read_text(encoding='utf-8'));a['status']='rejected-for-integration';a['review']=['Far middle gap approximately 56px versus mother 8px at y600. Endpoint fit is insufficient.','Do not promote paired narrow locks; original correspondence fit has only 1 reliable feature.'];f.write_text(json.dumps(a,indent=2)+'\n',encoding='utf-8')
hashes={str(f.relative_to(P)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for folder in ['raw','registered','references','rejected'] for f in (P/folder).glob('*.png')}
(P/'source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
f=P/'STATUS.md';s=f.read_text(encoding='utf-8');s+='\n## 最新进展：方法选择待回复\n\n整体长发 `hair-system-01/02` 与宽后发 `rear-system-01` 为新的诊断源，尚未通过整体美术验收。按同一源成对生成的窄马尾仍改变了远侧中段曲线，y600 处间隙约 56px，母版为 8px，故 `ponytails-pair-01` 不能接入。没有重复使用已否决的螺旋长发。\n\n已向用户确认是否允许官方“保留母版可见像素＋生成隐藏区域＋计算分件遮罩”流程；因为此前明确要求不要抠图、全部生成，在回复前不执行该路线。此项不是工具报错或自动审批拒绝。\n\n独立完成新空脸与原表情兼容性诊断：8 个站姿静态样本已看，未见重复五官，29 个原表情相关文件哈希未变。`expression-review.html` 为并排浏览页；`expression-compatibility-review.json` 写明只验证静态贴合，未完成坐姿和全身动作验收。当前旧预览保持不变。\n';f.write_text(s,encoding='utf-8');print(json.dumps(report))
