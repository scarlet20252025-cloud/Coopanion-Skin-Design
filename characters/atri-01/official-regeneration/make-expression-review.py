"""Copy the accepted face renderer byte-for-byte into an isolated static review."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;R=P.parents[2];base=R/'scratch/candidates/atri-hair-junctions'
source=(base/'figure.js').read_text(encoding='utf-8')
face=source[source.index(' function buildFace('):source.index(' const figure=')]
prefix="""const NS='http://www.w3.org/2000/svg';
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const n=(tag,attrs={})=>{const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);return e;};
const base='/scratch/candidates/atri-hair-junctions/';
const model=await(await fetch(base+'model.json')).json(),parts=new Map(model.parts.map(p=>[p.id,p])),textures=new Map(model.parts.map(p=>[p.file,base+p.file]));
const [W,H]=model.canvas,faceNodes=new Map();let clipPrefix='';
"""
suffix="""
const cases=[['neutral',0],['happy',0],['scared',0],['flustered',0],['neutral',.4],['neutral',.76],['neutral',1],['neutral',0]];
for(const [idx,[mood,blink]] of cases.entries()){
 const row=document.createElement('section');document.body.append(row);
 for(const type of ['accepted','new']){
  clipPrefix=type+'-'+idx;
  const cell=document.createElement('div'),caption=document.createElement('p');caption.textContent=type+' / '+mood+' / blink '+blink;cell.append(caption);row.append(cell);
  const svg=n('svg',{viewBox:'430 330 385 310',width:300,height:242});cell.append(svg);
  svg.append(n('image',{href:type==='accepted'?base+parts.get('head-clean').file:'/characters/atri-01/official-regeneration/registered/head-blank-01.png',width:W,height:H}));
  const state=buildFace('standing',svg);paintFace(state,mood,{blink});
 }
}
document.body.dataset.ready='true';
"""
(P/'expression-review.js').write_text(prefix+face+suffix,encoding='utf-8')
(P/'expression-review.html').write_text('<!doctype html><meta charset="utf-8"><title>ATRI 原表情兼容性诊断</title><style>body{font:14px system-ui;background:#24242b;color:white;margin:16px}section{display:inline-flex;margin:4px;gap:4px}section div{background:#e8e2ef;color:#403842}p{margin:4px}svg{display:block}</style><h3>左：已认可头部＋原表情　右：新空脸头部＋完全相同的原表情</h3><p>仅验证表情贴合，不代表身体、发型或动画整体验收。</p><script type="module" src="expression-review.js"></script>',encoding='utf-8')
report={'renderer_sha256':hashlib.sha256(face.encode()).hexdigest(),'source':'scratch/candidates/atri-hair-junctions/figure.js','method':'buildFace and paintFace copied verbatim; original assets and rig untouched','scope':'eight static standing samples; not timing or host acceptance'}
(P/'expression-review-source.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
