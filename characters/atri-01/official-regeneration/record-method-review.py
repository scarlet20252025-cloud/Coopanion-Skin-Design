from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
f=P/'progress.json';d=json.loads(f.read_text(encoding='utf-8'))
d['phase']='method audit complete; continuous garment diagnostic exists; art and animation integration incomplete'
d['diagnostic_sources']=['garment-connected-01','ponytail-right-05']
d['review']='garment-method-review.json'
d['pending']=['near-cuff-geometry-and-fingertip-check','far-hair-contour','derive-motion-arms-only-after-garment-pass','preserved-expression-integration','seated-regeneration','motion-QA']
f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
f=P/'attempt-30.json';d=json.loads(f.read_text(encoding='utf-8'));d['review']=['Connected shoulder no longer has the pointed isolated cap.','32 inliers span collar, far cuff and hem, but ZERO near-cuff inliers. This is NOT a full sleeve acceptance.','Near cuff position and fingertip outline still differ and need direct mother verification.','Not integrated; no dynamic acceptance.'];f.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
f=P/'STATUS.md';s=f.read_text(encoding='utf-8');s+='\n## 2026-10-15 用户否决手臂后的方法复核\n\n已核对龙娘生产源：双臂由完整母版成对生成、等比配准，领口肩窝使用母版像素。它是露肩分离袖，不能把接缝方式照搬到连肩水手服。ATRI 原单袖只靠袖口四个特征点配准，再延长肩根，未约束整臂比例，`arm-left-01/02` 均排除。当前诊断组装已撤下两者。\n\n新 `garment-connected-01` 从唯一母版生成连续衣身及双袖，用于先验证全局连接。32 个内点覆盖领口、远侧袖口和下摆；近侧袖口为零内点，且指尖形状仍有差异，因此不能宣布完整通过。`garment-method-review.png` 与 `assembly-connected-review.png` 为深浅底母版对照。只作为诊断源，未替换当前预览，未接入动作。\n\n远侧 `ponytail-right-04` 混入脸旁短发，排除；`05` 已去掉该内侧尖瓣，但整个远侧轮廓仍待核对。表情锁保持不变。\n';f.write_text(s,encoding='utf-8')
# Record actual current expression lock format, checking every path and hash without rewriting it.
lock=json.loads((P/'expression-lock.json').read_text(encoding='utf-8'))
print(json.dumps({'lock_keys':list(lock),'state':'source audit recorded; diagnostic only'}))
