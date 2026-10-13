import * as kit from './vendor/kit/body.js';
import {createDragonBody} from '../packs/gpt-dragon-v005-r04/figure.js';
const base=new URL('../packs/gpt-dragon-v005-r04/',import.meta.url);
const stage=document.querySelector('#stage'),root=document.querySelector('#root'),status=document.querySelector('#status');
const model=await(await fetch(new URL('model.json',base))).json();
const image=url=>new Promise((ok,bad)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=bad;im.src=url;});
let body,paused=false,last=performance.now(),slowUntil=0;
const events=[];
async function reset(){body?.dispose();body=await createDragonBody(base,{kit,model,loadImage:image,host:{root,bounds:()=>({W:stage.clientWidth,H:stage.clientHeight,floorY:stage.clientHeight-22,S:1.25}),start:{x:stage.clientWidth/2,facing:1,enter:'stand'},emit:(kind,detail)=>events.push({kind,detail}),sound:()=>{}}});body.set({roam:'off',hold:999});}
await reset();
function raf(now){if(!paused)body.step(Math.min(.03,(now-last)/1000)*(now < slowUntil ? .2 : 1));last=now;requestAnimationFrame(raf);}requestAnimationFrame(raf);
for(const [id,name]of [['stand','站起'],['sit','坐下'],['sleep','睡眠'],['nod','轻点头'],['shake','轻摇头'],['jump','跳跃'],['hop','小跳'],['turn','转身'],['walk','走路'],['run','跑步'],['wave','招手']]){const b=document.createElement('button');b.textContent=name;b.onclick=()=>{paused=false;const ok=body.do(id);status.textContent=ok===false?'当前动作尚未结束，请稍后再试':name+' · v005-r04';};document.querySelector('#controls').append(b);}
document.querySelector('#reset').onclick=async()=>{paused=true;await reset();paused=false;status.textContent='已复位：待机眨眼';};
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
document.querySelector('#capture').onclick=async()=>download(await capture(),'dragon-v005-r04-frame.png');
async function exportQA(words,filename,stride=10,count=120){
 paused=true;const buttons=[...document.querySelectorAll('button')];buttons.forEach(b=>b.disabled=true);const samples=[];
 try{for(const word of words){
  await reset();for(let i=0;i<60;i++)body.step(1/60);if(word==='stand-from-sit'){body.do('sit');for(let i=0;i<120;i++)body.step(1/60);}body.do(word==='stand-from-sit'?'stand':word);
  for(let i=0;i<count;i++){body.step(1/60);if(i%stride===0){status.textContent='检查帧导出：'+word+' '+i+'/'+count;samples.push({word,frame:i,t:(i+1)/60,layout:body.layout(),png:await capture()});}}
 }
 download(JSON.stringify({prototype:'v005-r04',master:model.master_sha256,motionParameters:{legs:model.leg_rig,arms:model.motion_rig},samples,events}),filename,'application/json');status.textContent=`已导出 ${samples.length} 张动作检查帧`;
 }catch(e){status.textContent=String(e.stack);}finally{await reset();paused=false;buttons.forEach(b=>b.disabled=false);}
}
document.querySelector('#qa').onclick=()=>exportQA(['neutral','nod','shake','sit','sleep','jump','hop','turn'],'dragon-v005-r04-qa.json');
document.querySelector('#jumpqa').onclick=()=>exportQA(['jump','hop'],'dragon-v005-r04-jump-qa.json',3,72);
document.querySelector('#limbqa').onclick=()=>exportQA(['walk','run','wave','jump'],'dragon-v005-r04-limbs-qa.json',6,120);
document.querySelector('#poseqa').onclick=()=>exportQA(['wave','sit','stand-from-sit'],'dragon-v005-r04-pose-qa.json',6,120);
document.querySelector('#seek').onclick=async()=>{paused=true;await reset();for(let i=0;i<60;i++)body.step(1/60);const word=document.querySelector('#inspect-motion').value;body.do(word);const frame=Math.max(0,Math.min(180,Number(document.querySelector('#frame').value)||0));for(let i=0;i<=frame;i++)body.step(1/60);status.textContent=`${word} 第 ${frame} 帧 · ${body.layout().mode} · 已暂停，可下载核验`;};
document.querySelector('#resume').onclick=()=>{paused=false;};
for(const [word,label]of [['neutral','平静'],['happy','笑眼'],['wink','单眼眨眼'],['sleepy','困倦']]){const b=document.createElement('button');b.textContent=label;b.onclick=()=>{paused=false;body.do(word);status.textContent=label+' · v005-r04';};document.querySelector('#faces').append(b);}
document.querySelector('#faceqa').onclick=()=>exportQA(['happy','wink','sleepy','wave'],'dragon-v005-r04-faces-qa.json',10,100);
status.textContent='v005-r04 已加载：等待视觉验收';
