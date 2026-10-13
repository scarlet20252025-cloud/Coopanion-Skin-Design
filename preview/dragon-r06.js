import * as kit from './vendor/kit/body.js';
import {createDragonBody} from '../packs/gpt-dragon-v005-r06/figure.js';
const base=new URL('../packs/gpt-dragon-v005-r06/',import.meta.url);
const stage=document.querySelector('#stage'),root=document.querySelector('#root'),status=document.querySelector('#status');
const model=await(await fetch(new URL('model.json',base))).json();
const image=url=>new Promise((ok,bad)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=bad;im.src=url;});
let body,paused=false,last=performance.now(),slowUntil=0;
const events=[];
async function reset(){body?.dispose();body=await createDragonBody(base,{kit,model,loadImage:image,host:{root,bounds:()=>({W:stage.clientWidth,H:stage.clientHeight,floorY:stage.clientHeight-22,S:1.25}),start:{x:stage.clientWidth/2,facing:1,enter:'stand'},emit:(kind,detail)=>events.push({kind,detail}),sound:()=>{}}});body.set({roam:'off',hold:999});}
await reset();
function raf(now){if(!paused)body.step(Math.min(.03,(now-last)/1000)*(now < slowUntil ? .2 : 1));last=now;requestAnimationFrame(raf);}requestAnimationFrame(raf);
for(const [id,name]of [['stand','站起'],['sit','坐下'],['sleep','睡眠'],['nod','轻点头'],['shake','轻摇头'],['jump','跳跃'],['hop','小跳'],['turn','转身'],['walk','走路'],['run','跑步'],['wave','招手']]){const b=document.createElement('button');b.textContent=name;b.onclick=()=>{paused=false;const ok=body.do(id);status.textContent=ok===false?'当前动作尚未结束，请稍后再试':name+' · v005-r06';};document.querySelector('#controls').append(b);}
document.querySelector('#reset').onclick=async()=>{paused=true;await reset();body.setSecondary(secondaryEnabled);paused=false;status.textContent='已复位：待机眨眼';};
document.querySelector('#blink').onclick=async()=>{paused=true;await reset();for(let i=0;i<70;i++)body.step(1/60);slowUntil=performance.now()+3500;paused=false;status.textContent='眨眼 0.2 倍慢放，观察眼睑与原画是否错位';};
document.querySelector('#background').onclick=()=>stage.classList.toggle('dark');
new ResizeObserver(()=>body?.resize()).observe(stage);
const point=e=>{const r=stage.getBoundingClientRect();return{x:e.clientX-r.left,y:e.clientY-r.top};};
stage.onpointerdown=e=>{body.pointer('down',point(e));stage.setPointerCapture(e.pointerId);};stage.onpointermove=e=>body.pointer('move',point(e));stage.onpointerup=e=>body.pointer('up',point(e));stage.onpointercancel=e=>body.pointer('cancel',point(e));stage.onpointerleave=()=>body.pointer('leave');
async function capture(){
 const svg=root.querySelector('svg').cloneNode(true);svg.setAttribute('xmlns','http://www.w3.org/2000/svg');svg.setAttribute('width',stage.clientWidth);svg.setAttribute('height',stage.clientHeight);
 for(const hidden of svg.querySelectorAll('[visibility="hidden"]'))hidden.remove();
 const st=document.createElementNS('http://www.w3.org/2000/svg','style');st.textContent='.shadow{fill:rgba(0,0,0,.16)}.eye{stroke:#a18acb}.p-dust{stroke:#877e97}.p-heart{stroke:#dd889f}';svg.prepend(st);
 const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml'}));
 try{const im=await image(url);const cv=document.createElement('canvas');cv.width=stage.clientWidth;cv.height=stage.clientHeight;cv.getContext('2d').drawImage(im,0,0);return cv.toDataURL('image/png');}finally{URL.revokeObjectURL(url);}
}
function download(data,name,type){
 if(typeof data==='string'&&data.startsWith('data:')){const [header,encoded]=data.split(',');type=header.slice(5).split(';')[0];data=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));}
 const a=document.createElement('a'),u=URL.createObjectURL(new Blob([data],{type}));a.href=u;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),30000);
}
document.querySelector('#capture').onclick=async()=>download(await capture(),'dragon-v005-r06-frame.png');
async function exportQA(words,filename,stride=10,count=120){
 paused=true;const oldWidth=stage.style.width;stage.style.width='960px';const buttons=[...document.querySelectorAll('button')];buttons.forEach(b=>b.disabled=true);const samples=[];
 try{for(const word of words){
  await reset();for(let i=0;i<60;i++)body.step(1/60);if(word==='stand-from-sit'){body.do('sit');for(let i=0;i<120;i++)body.step(1/60);}if(['walk','run','run-stop-wave'].includes(word)){body.place(130,1);body.walk(830,word!=='walk','qa-gait');}else body.do(word==='stand-from-sit'?'stand':word);
  for(let i=0;i<count;i++){if(word==='run-stop-wave'){if(i===60)body.stopWalk('qa-gait');if(i===100)body.do('wave');}body.step(1/60);if(i%stride===0){status.textContent='检查帧导出：'+word+' '+i+'/'+count;samples.push({word,frame:i,t:(i+1)/60,layout:body.layout(),secondary:body.secondaryState(),armLayers:body.armLayerState(),png:await capture()});}}
 }
 download(JSON.stringify({prototype:'v005-r06',master:model.master_sha256,motionParameters:{legs:model.leg_rig,arms:model.motion_rig},samples,events}),filename,'application/json');status.textContent=`已导出 ${samples.length} 张动作检查帧`;
 }catch(e){status.textContent=String(e.stack);}finally{stage.style.width=oldWidth;await reset();paused=false;buttons.forEach(b=>b.disabled=false);}
}
document.querySelector('#qa').onclick=()=>exportQA(['neutral','nod','shake','sit','sleep','jump','hop','turn'],'dragon-v005-r06-qa.json');
document.querySelector('#jumpqa').onclick=()=>exportQA(['jump','hop'],'dragon-v005-r06-jump-qa.json',3,72);
document.querySelector('#limbqa').onclick=()=>exportQA(['walk','run','wave','jump'],'dragon-v005-r06-limbs-qa.json',6,120);
document.querySelector('#poseqa').onclick=()=>exportQA(['wave','sit','stand-from-sit'],'dragon-v005-r06-pose-qa.json',6,120);
document.querySelector('#seek').onclick=async()=>{paused=true;await reset();for(let i=0;i<60;i++)body.step(1/60);const word=document.querySelector('#inspect-motion').value;body.do(word);const frame=Math.max(0,Math.min(180,Number(document.querySelector('#frame').value)||0));for(let i=0;i<=frame;i++)body.step(1/60);status.textContent=`${word} 第 ${frame} 帧 · ${body.layout().mode} · 已暂停，可下载核验`;};
document.querySelector('#resume').onclick=()=>{paused=false;};
for(const [word,label]of [['neutral','平静'],['happy','笑眼'],['wink','单眼眨眼'],['sleepy','困倦'],['thinking','思考'],['working','工作'],['listening','倾听']]){const b=document.createElement('button');b.textContent=label;b.onclick=()=>{paused=false;body.do(word);status.textContent=label+' · v005-r06';};document.querySelector('#faces').append(b);}
document.querySelector('#faceqa').onclick=()=>exportQA(['happy','wink','sleepy','wave'],'dragon-v005-r06-faces-qa.json',10,100);
status.textContent='v005-r06 已加载：等待视觉验收';

let secondaryEnabled=true;document.querySelector("#secondary").onclick=e=>{secondaryEnabled=!secondaryEnabled;body.setSecondary(secondaryEnabled);e.target.textContent=secondaryEnabled?"关闭附属动态（对比）":"开启附属动态（对比）";};
document.querySelector("#secondaryqa").onclick=()=>exportQA(["neutral","walk","run","jump","wave","sit"],"dragon-v005-r06-secondary-qa.json",10,100);

document.querySelector("#layerqa").onclick=()=>exportQA(["run-stop-wave"],"dragon-v005-r06-layer-qa.json",6,240);

// Repeatable transitions use the public kit API and timestamps, never internal state writes.
async function interactionQA(){
 paused=true;const oldWidth=stage.style.width;stage.style.width='960px';const samples=[],checks=[];
 const buttons=[...document.querySelectorAll('button')];buttons.forEach(b=>b.disabled=true);
 try{for(const facing of [1,-1])for(const scenario of ['rest-wave','run-stop','drag-release','attention']){
  await reset();body.place(480,facing);for(let n=0;n<60;n++)body.step(1/60);
  const word=scenario+(facing===1?'-right':'-left');let point=body.layout().hit[0];
  for(let i=0;i<240;i++){
   const at=(frame,fn)=>{if(i===frame)checks.push({word,frame,result:fn()??null});};
   if(scenario==='rest-wave'){at(30,()=>body.do('wave'));}
   if(scenario==='run-stop'){at(0,()=>body.walk(facing===1?830:130,true,'transition'));at(60,()=>body.stopWalk('transition'));at(100,()=>body.do('wave'));}
   if(scenario==='drag-release'){
    at(20,()=>body.pointer('down',{x:point.x,y:point.y,t:0}));
    if(i>20&&i<=60)body.pointer('move',{x:point.x+facing*Math.min(60,(i-20)*3),y:point.y-Math.min(65,(i-20)*3),t:(i-20)*1000/60});
    at(61,()=>body.pointer('up',{x:point.x+facing*60,y:point.y-65,t:700}));
   }
   if(scenario==='attention'){at(0,()=>body.do('thinking'));at(60,()=>body.do('working'));at(120,()=>body.do('listening'));at(180,()=>body.do('neutral'));}
   body.step(1/60);
   if(i%20===0){status.textContent=word+' '+i+'/240';samples.push({word,frame:i,t:(i+1)/60,layout:body.layout(),armLayers:body.armLayerState(),png:await capture()});}
  }
 }
 download(JSON.stringify({prototype:'0.6.6-preview',master:model.master_sha256,samples,checks,events}),'dragon-r06-interactions-066.json','application/json');status.textContent='已导出左右朝向 8 组交互检查';
 }finally{stage.style.width=oldWidth;await reset();paused=false;buttons.forEach(b=>b.disabled=false);}
}
document.querySelector('#interactionqa').onclick=interactionQA;
