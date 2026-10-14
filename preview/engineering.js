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
