import * as kit from './vendor/kit/body.js';
const $=id=>document.getElementById(id),requested=new URLSearchParams(location.search).get('pack')||'packs/gpt-dragon-v005-r25';
if(!/^(packs|scratch\/candidates)\/[a-z0-9][a-z0-9-]{0,63}$/.test(requested))throw Error('Invalid local pack path');
const base=new URL('../'+requested+'/',import.meta.url),manifest=await(await fetch(new URL('figure.json',base))).json(),model=await(await fetch(new URL(manifest.model,base))).json();
if(!/^[a-zA-Z0-9_.-]+\.js$/.test(manifest.entry))throw Error('Entry must be a pack-local module');
const module=await import(new URL(manifest.entry,base)),factory=module[manifest.export];if(typeof factory!=='function')throw Error('Factory export missing');
let body,paused=false,facing=1,last=performance.now();const events=[];
async function reset(){body?.dispose();body=await factory(base,{kit,model,host:{root:$('root'),bounds:()=>({W:$('stage').clientWidth,H:800,floorY:775,S:3}),start:{x:$('stage').clientWidth/2,facing,enter:'stand'},emit:(kind,detail)=>events.push({kind,detail}),sound:()=>{}}});body.set({roam:'off',hold:999});for(let i=0;i<60;i++)body.step(1/60);}
await reset();$('identity').textContent=`${manifest.name.zh||manifest.id} · ${manifest.version} · ${manifest.author}`;
function raf(now){if(!paused)body.step(Math.min(.03,(now-last)/1000));last=now;requestAnimationFrame(raf)}requestAnimationFrame(raf);
for(const word of manifest.vocab){const b=document.createElement('button');b.textContent=word.names?.zh?.[0]||word.id;b.onclick=()=>{paused=false;$('status').textContent=JSON.stringify({word:word.id,accepted:body.do(word.id),layout:body.layout()});};$('actions').append(b);}
const point=e=>{const r=$('stage').getBoundingClientRect();return{x:e.clientX-r.left,y:e.clientY-r.top,t:performance.now()};};
$('stage').onpointerdown=e=>{body.pointer('down',point(e));$('stage').setPointerCapture(e.pointerId)};$('stage').onpointermove=e=>body.pointer('move',point(e));$('stage').onpointerup=e=>body.pointer('up',point(e));$('stage').onpointercancel=e=>body.pointer('cancel',point(e));
$('background').onclick=()=>$('stage').classList.toggle('dark');$('reset').onclick=async()=>{paused=true;await reset();paused=false;};$('turn').onclick=()=>{facing=-facing;body.place($('stage').clientWidth/2,facing);};
function download(data,name,type){const a=document.createElement('a'),u=URL.createObjectURL(new Blob([data],{type}));a.href=u;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1000)}
async function capture(){
 const source=$('root').querySelector('svg'),clone=source.cloneNode(true),width=$('stage').clientWidth;
 clone.setAttribute('xmlns','http://www.w3.org/2000/svg');clone.setAttribute('width',width);clone.setAttribute('height',800);
 for(const hidden of clone.querySelectorAll('[visibility="hidden"]'))hidden.remove();
 const style=document.createElementNS('http://www.w3.org/2000/svg','style');style.textContent='.tearf{fill:#6bbdf7}.shadow{fill:rgba(0,0,0,.16)}.eye{stroke:#a18acb}.p-dust{stroke:#877e97}.p-heart{stroke:#dd889f}';clone.prepend(style);
 const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(clone)],{type:'image/svg+xml'}));
 try{const im=await new Promise((ok,bad)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=bad;im.src=url;});const cv=document.createElement('canvas');cv.width=width;cv.height=800;cv.getContext('2d').drawImage(im,0,0);return cv.toDataURL();}finally{URL.revokeObjectURL(url);}
}
$('capture').onclick=async()=>{const blob=await(await fetch(await capture())).blob();download(blob,manifest.id+'-frame.png','image/png');};
$('qa').onclick=async()=>{paused=true;const samples=[],checks=[];try{for(const direction of [1,-1])for(const word of ['neutral','wave','flap','dance','sit','dizzy','turn']){facing=direction;await reset();const ok=body.do(word);checks.push({word,facing,accepted:ok});for(let i=0;i<180;i++){body.step(1/60);if(i%30===0){samples.push({word,frame:i,facing,layout:body.layout(),visual:body.visualState?.(),secondary:body.secondaryState?.(),png:await capture()});$('status').textContent=`采样 ${samples.length}/84`;}}}download(JSON.stringify({version:manifest.version,master:model.master_sha256,checks,samples,events}),manifest.id+'-qa.json','application/json');$('status').textContent='已导出 84 张左右动作采样；需人工视觉复核';}finally{facing=1;await reset();paused=false;}};
window.engineeringReady=true;window.engineeringState=()=>({manifest,layout:body.layout()});

// Tool-facing sampler: each case resets independently, each phase preserves its predecessor.
window.runEngineeringQA=async plan=>{
 paused=true;const samples=[],checks=[],random=Math.random;let seed=13841;
 Math.random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
 const advance=seconds=>{for(let t=0;t<seconds-1e-8;t+=1/60)body.step(Math.min(1/60,seconds-t));};
 const shot=async(key,phase)=>samples.push({key,phase,facing,layout:body.layout(),visual:body.visualState?.(),secondary:body.secondaryState?.(),arms:body.armLayerState?.(),png:await capture()});
 try{
  for(const direction of [1,-1])for(const test of plan.cases){
   facing=direction;await reset();
   if(test.pointer){
    let hit=body.layout().hit[0],point={x:hit.x,y:hit.y,t:1000};
    body.pointer('down',point);checks.push({key:`${direction}:pointer:press`,accepted:body.layout().pressing===true});
    body.pointer('up',{...point,t:1120});advance(.2);await shot(`${direction}:pointer:click`,'click');
    hit=body.layout().hit[0];point={x:hit.x,y:hit.y,t:2000};body.pointer('down',point);
    point={x:point.x+15,y:point.y-80,t:2120};body.pointer('move',point);advance(.4);
    checks.push({key:`${direction}:pointer:drag`,accepted:body.layout().mode==='drag'});await shot(`${direction}:pointer:held`,'held');
    body.pointer('up',{...point,t:2700});advance(.15);
    checks.push({key:`${direction}:pointer:release`,accepted:body.layout().mode!=='drag'});await shot(`${direction}:pointer:released`,'released');
    advance(3);await shot(`${direction}:pointer:recovery`,'recovery');
   }else for(const step of test.steps){
    checks.push({key:`${direction}:${test.id}:${step.phase}`,word:step.word,accepted:body.do(step.word)});
    let previous=0;
    for(const time of step.samples){advance(time-previous);previous=time;await shot(`${direction}:${test.id}:${step.phase}:${time}`,step.phase);}
    advance(step.seconds-previous);
   }
   $('status').textContent=`QA ${samples.length}/${plan.expected.length}`;
  }
  return {version:manifest.version,master:model.master_sha256,viewport:[$('stage').clientWidth,800],checks,samples,events};
 }finally{Math.random=random;facing=1;await reset();paused=false;}
};
