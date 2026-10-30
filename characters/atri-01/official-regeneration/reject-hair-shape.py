from pathlib import Path
import json
P=Path(__file__).resolve().parent
rejected={'ponytail-left-02','ponytail-right-05','rear-complete-01'}
f=P/'progress.json';d=json.loads(f.read_text(encoding='utf-8'))
d['phase']='long-hair assembly rejected for shape drift; garment diagnostic pending; no runtime replacement'
d['provisional']=[x for x in d['provisional'] if x not in rejected]
d['diagnostic_sources']=[x for x in d.get('diagnostic_sources',[]) if x not in rejected]
d['rejected']=list(dict.fromkeys(d['rejected']+sorted(rejected)))
d['hair_review']='hair-shape-rejection.json'
f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
f=P/'assembly-report.json';d=json.loads(f.read_text(encoding='utf-8'));d['state']='REJECTED long-hair silhouette; retain images only as failure evidence';d['rejection']='hair-shape-rejection.json';f.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
f=P/'STATUS.md';s=f.read_text(encoding='utf-8');s+='\n## 2026-10-15 新长发造型否决（覆盖上文暂留状态）\n\n用户指出螺旋感。复核新源图及静态全身图发现：窄马尾 S 形弯曲及明暗翻转被夸大，宽后发增加回卷尖束，整体已偏离母版。`ponytail-left-02`、`ponytail-right-05`、`rear-complete-01` 全部退出暂留清单，不能接入。旧全身诊断图保留为失败证据，不再作为美术通过依据。先核对完整发型的发流、弯曲方向、分叉与明暗归属，禁止再仅靠端点配准判断。当前浏览器仍为旧 `atri-hair-junctions`，没有替换。详见 `hair-shape-rejection.json`。\n';f.write_text(s,encoding='utf-8')
print('Long-hair provisional acceptance revoked; existing browser candidate untouched.')
