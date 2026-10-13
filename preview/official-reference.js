import * as kit from '/official/kit/body.js';
import {createWhaleFigure} from '/official/whale/figure.js';
const base=new URL('/official/whale/',location.href);
const model=await(await fetch(new URL('model.json',base))).json();
const manifest=await(await fetch(new URL('figure.json',base))).json();
const stage=document.querySelector('#stage'),status=document.querySelector('#status');
const W=448,H=448,FPS=60;
const figure=await createWhaleFigure(base,{kit,model,scheme:'deepseek-maid',raster:true});
let body,clock=0,live=true,last=performance.now(),rng=1;
const nativeRandom=Math.random;
function seed(n){rng=n>>>0;Math.random=()=>{rng=(Math.imul(rng,1664525)+1013904223)>>>0;return rng/4294967296;};}
function reset(id){body?.dispose();figure.reset();stage.replaceChildren();clock=0;
 body=kit.createBody({root:stage,bounds:()=>({W,H,floorY:H-22,S:.8}),start:{x:W/2,facing:1,enter:'stand'},emit:()=>{},sound:()=>{}},{figure});
 body.set({roam:'off',hold:100});for(let i=0;i<60;i++)body.step(1/FPS);
 if(id==='stand'){body.do('sit');for(let i=0;i<120;i++)body.step(1/FPS);}
}
function raf(now){if(live)body.step(Math.min(.03,(now-last)/1000));last=now;requestAnimationFrame(raf);}
reset();requestAnimationFrame(raf);
const buttons=[...document.querySelectorAll('button')];buttons.forEach(b=>b.disabled=false);status.textContent=`已加载 ${manifest.vocab.length} 项词表。先检查小样，再批量采样。`;
const image=url=>new Promise((ok,bad)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=bad;im.src=url;});
async function frameBlob(){
 await figure.painted;
 const svg=stage.querySelector('svg').cloneNode(true);svg.setAttribute('xmlns','http://www.w3.org/2000/svg');svg.setAttribute('width',W);svg.setAttribute('height',H);svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
 const styles=document.createElementNS('http://www.w3.org/2000/svg','style');styles.textContent='.shadow{fill:rgba(0,0,0,.18)}.eye{stroke:#4d6bfe}.tearf{fill:#67bfff}.p-heart{stroke:#ff6f93}.p-dust{stroke:#5b6472}';svg.prepend(styles);
 const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml'}));
 try{const im=await image(url);const cv=document.createElement('canvas');cv.width=W;cv.height=H;cv.getContext('2d').drawImage(im,0,0);return await new Promise(ok=>cv.toBlob(ok,'image/png'));}finally{URL.revokeObjectURL(url);}
}
async function save(path,data){const r=await fetch('/export/'+path,{method:'POST',body:data});if(!r.ok)throw Error(await r.text());}
function finite(o){if(typeof o==='number')return Number.isFinite(o);return !o||typeof o!=='object'||Object.values(o).every(finite);}
const extras=[{id:'idle_blink',kind:'interaction'},{id:'talk',kind:'interaction'},{id:'listening',kind:'interaction'},{id:'working',kind:'interaction'},{id:'walk_left',kind:'interaction'},{id:'run_left',kind:'interaction'}];
const supplemental=['walk_right','run_right','drag_release','sleep_wake','cursor_gaze'].map(id=>({id,kind:'interaction'}));
async function exportActions(words){
 live=false;buttons.forEach(b=>b.disabled=true);
 try{for(const [index,word] of words.entries()){
  seed(20261013);reset(word.id);
  const seconds=word.id==='sleep'?8:word.id==='sleepy'?6:word.kind==='interaction'?6:4.8;
  const count=Math.round(seconds*FPS),timeline=[];
  let accepted=true,grabPoint=null;
  if(word.id==='listening')body.set({listening:true});else if(word.id==='working')body.set({thinking:true});else if(word.id==='walk_left'||word.id==='run_left'){body.place(W-110,1);body.walk(95,word.id==='run_left',word.id);}else if(word.id==='walk_right'||word.id==='run_right'){body.place(110,-1);body.walk(W-95,word.id==='run_right',word.id);}else if(word.id==='drag_release'){grabPoint=body.layout().hit[0];body.pointer('down',{...grabPoint,t:0});}else if(word.id==='sleep_wake'){body.do('sleep');for(let j=0;j<180;j++)body.step(1/FPS);}else if(!['idle_blink','talk','cursor_gaze'].includes(word.id))accepted=body.do(word.id);
  if(accepted===false)throw Error('动作被拒绝: '+word.id);
  for(let i=0;i<count;i++){
   if(word.id==='talk'&&i%6===0)body.talk();
   if(word.id==='drag_release'&&i<90)body.pointer('move',{x:grabPoint.x+35*Math.sin(i/25),y:grabPoint.y-50*Math.min(1,i/30),t:i*1000/FPS});
   if(word.id==='drag_release'&&i===90)body.pointer('up',{t:i*1000/FPS});
   if(word.id==='sleep_wake'&&i===60)body.do('stand');
   if(word.id==='cursor_gaze')body.pointer('move',{x:W/2+180*Math.sin(i/50),y:H/2+160*Math.cos(i/50),t:i*1000/FPS});
   body.step(1/FPS);
   const layout=body.layout();if(!finite(layout))throw Error('无效坐标: '+word.id);
   const blob=await frameBlob();await save(`${word.id}/${String(i).padStart(4,'0')}.png`,blob);
   timeline.push({frame:i,t:(i+1)/FPS,layout});
   if(i%30===0)status.textContent=`${index+1}/${words.length} · ${word.names?.zh?.[0]||word.id} · ${i+1}/${count} 帧`;
  }
  await save(`${word.id}/timeline.json`,JSON.stringify({id:word.id,kind:word.kind,names:word.names,sourceCommit:'91293b3e31b94397a8f2eb79dffec40f4c6d8817',fps:FPS,count,seconds,seed:20261013,width:W,height:H,scale:.8,frames:timeline}));
 }
 status.textContent=`完成：${words.length} 项，逐帧 PNG 与时间轴已保存到 tools-local/whale-reference-91293b3。`;
 }catch(e){status.textContent='导出失败：'+e.stack;}finally{Math.random=nativeRandom;buttons.forEach(b=>b.disabled=false);}
}
document.querySelector('#sample').onclick=()=>exportActions([manifest.vocab.find(w=>w.id==='wave')]);
document.querySelector('#all').onclick=()=>exportActions([...manifest.vocab,...extras,...supplemental]);
document.querySelector('#supplement').onclick=()=>exportActions(supplemental);
