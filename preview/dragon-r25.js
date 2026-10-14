import * as kit from './vendor/kit/body.js';
import {createDragonBody} from '../packs/gpt-dragon-v005-r25/figure.js';
const base=new URL('../packs/gpt-dragon-v005-r25/',import.meta.url);
const stage=document.querySelector('#stage'),root=document.querySelector('#root'),status=document.querySelector('#status');
const model=await(await fetch(new URL('model.json',base))).json();
const manifest=await(await fetch(new URL('figure.json',base))).json();
const image=url=>new Promise((ok,bad)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=bad;im.src=url;});
let inspectScale=1.25;let body,paused=false,last=performance.now(),slowUntil=0;
const events=[];
async function reset(){body?.dispose();body=await createDragonBody(base,{kit,model,loadImage:image,host:{root,bounds:()=>({W:stage.clientWidth,H:stage.clientHeight,floorY:stage.clientHeight-22,S:inspectScale}),start:{x:stage.clientWidth/2,facing:1,enter:'stand'},emit:(kind,detail)=>events.push({kind,detail}),sound:()=>{}}});body.set({roam:'off',hold:999});}
await reset();
function raf(now){if(!paused)body.step(Math.min(.03,(now-last)/1000)*(now < slowUntil ? .2 : 1));last=now;requestAnimationFrame(raf);}requestAnimationFrame(raf);
for(const [id,name]of [["stand", "站起"], ["jump", "跳跃"], ["hop", "小跳"], ["look", "张望"], ["turn", "转身"], ["nod", "点头"], ["shake", "摇头"], ["spin", "转圈"], ["sit", "坐下"], ["sleep", "睡眠"], ["dizzy", "晕乎"], ["walk", "走路"], ["run", "跑步"], ["wave", "招手"], ["bow", "鞠躬"], ["shiver", "发抖"], ["flap", "振翅"], ["dance", "跳舞"]]){const b=document.createElement('button');b.textContent=name;b.onclick=()=>{paused=false;const ok=body.do(id);status.textContent=ok===false?'当前动作尚未结束，请稍后再试':name+' · v005-r25';};document.querySelector('#controls').append(b);}
document.querySelector('#reset').onclick=async()=>{paused=true;await reset();body.setSecondary(secondaryEnabled);paused=false;status.textContent='已复位：待机眨眼';};
document.querySelector('#blink').onclick=async()=>{paused=true;await reset();for(let i=0;i<70;i++)body.step(1/60);slowUntil=performance.now()+3500;paused=false;status.textContent='眨眼 0.2 倍慢放，观察眼睑与原画是否错位';};
document.querySelector('#background').onclick=()=>stage.classList.toggle('dark');
new ResizeObserver(()=>body?.resize()).observe(stage);
const point=e=>{const r=stage.getBoundingClientRect();return{x:e.clientX-r.left,y:e.clientY-r.top};};
stage.onpointerdown=e=>{body.pointer('down',point(e));stage.setPointerCapture(e.pointerId);};stage.onpointermove=e=>body.pointer('move',point(e));stage.onpointerup=e=>body.pointer('up',point(e));stage.onpointercancel=e=>body.pointer('cancel',point(e));stage.onpointerleave=()=>body.pointer('leave');
async function capture(sourceFilter){
 const svg=root.querySelector('svg').cloneNode(true);svg.setAttribute('xmlns','http://www.w3.org/2000/svg');svg.setAttribute('width',stage.clientWidth);svg.setAttribute('height',stage.clientHeight);
 for(const hidden of svg.querySelectorAll('[visibility="hidden"]'))hidden.remove();
 if(sourceFilter){for(const im of svg.querySelectorAll('image'))if(!im.matches(sourceFilter))im.remove();for(const path of svg.querySelectorAll('path,ellipse,circle'))if(!path.closest('defs'))path.remove();}
 const st=document.createElementNS('http://www.w3.org/2000/svg','style');st.textContent='.tearf{fill:#6bbdf7}.shadow{fill:rgba(0,0,0,.16)}.eye{stroke:#a18acb}.p-dust{stroke:#877e97}.p-heart{stroke:#dd889f}';svg.prepend(st);
 const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml'}));
 try{const im=await image(url);const cv=document.createElement('canvas');cv.width=stage.clientWidth;cv.height=stage.clientHeight;cv.getContext('2d').drawImage(im,0,0);return cv.toDataURL('image/png');}finally{URL.revokeObjectURL(url);}
}
function download(data,name,type){
 if(typeof data==='string'&&data.startsWith('data:')){const [header,encoded]=data.split(',');type=header.slice(5).split(';')[0];data=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));}
 const a=document.createElement('a'),u=URL.createObjectURL(new Blob([data],{type}));a.href=u;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),30000);
}
document.querySelector('#capture').onclick=async()=>download(await capture(),'dragon-v005-r25-frame.png');
const anatomyButton=document.createElement('button');anatomyButton.id='anatomyqa';anatomyButton.textContent='导出肩袖分层诊断';document.querySelector('#capture').after(anatomyButton);
anatomyButton.onclick=async()=>{paused=true;const layers={};for(const [name,selector] of Object.entries({torso:'[data-source="body-without-legs"]',arm:'[data-arm-slot="left"] image',head:'[data-part="head-components"] image',wings:'[data-part="dragon-wings"] image'}))layers[name]=await capture(selector);download(JSON.stringify({layers,whole:await capture(),arms:body.armLayerState()}),'dragon-r25-anatomy.json','application/json');status.textContent='肩袖分层诊断已导出';};
async function exportQA(words,filename,stride=10,count=120){
 paused=true;const oldWidth=stage.style.width;stage.style.width='960px';const buttons=[...document.querySelectorAll('button')];buttons.forEach(b=>b.disabled=true);const samples=[];
 try{for(const word of words){
  await reset();for(let i=0;i<60;i++)body.step(1/60);if(word==='stand-from-sit'){body.do('sit');for(let i=0;i<120;i++)body.step(1/60);}if(['walk','run','run-stop-wave'].includes(word)){body.place(130,1);body.walk(830,word!=='walk','qa-gait');}else if(word.startsWith('sit-')){body.do('sit');for(let j=0;j<120;j++)body.step(1/60);body.do(word.slice(4));}else body.do(word==='stand-from-sit'?'stand':word);
  for(let i=0;i<count;i++){if(word==='click-react'&&i===30){const p=body.layout().hit[0];body.pointer('down',{x:p.x,y:p.y,t:500});}if(word==='click-react'&&i===32){const p=body.layout().hit[0];body.pointer('up',{x:p.x,y:p.y,t:533});}if(word==='happy-release'){if(i===30)body.do('happy');if(i===115)body.do('neutral');}if(word==='run-stop-wave'){if(i===60)body.stopWalk('qa-gait');if(i===100)body.do('wave');}body.step(1/60);if(i%stride===0){status.textContent='检查帧导出：'+word+' '+i+'/'+count;samples.push({word,frame:i,t:(i+1)/60,layout:body.layout(),tail:body.tailState(),wingSignal:body.wingSignal(),wings:body.wingState(),secondary:body.secondaryState(),armLayers:body.armLayerState(),visual:body.visualState(),png:await capture()});}}
 }
 download(JSON.stringify({prototype:manifest.version,master:model.master_sha256,motionParameters:{legs:model.leg_rig,arms:model.motion_rig},samples,events}),filename,'application/json');status.textContent=`已导出 ${samples.length} 张动作检查帧`;
 }catch(e){status.textContent=String(e.stack);}finally{stage.style.width=oldWidth;await reset();paused=false;buttons.forEach(b=>b.disabled=false);}
}
document.querySelector('#qa').onclick=()=>exportQA(['neutral','nod','shake','sit','sleep','jump','hop','turn'],'dragon-v005-r25-qa.json');
document.querySelector('#jumpqa').onclick=()=>exportQA(['jump','hop'],'dragon-v005-r25-jump-qa.json',3,72);
document.querySelector('#limbqa').onclick=()=>exportQA(['walk','run','wave','jump'],'dragon-v005-r25-limbs-qa.json',6,120);
document.querySelector('#poseqa').onclick=()=>exportQA(['wave','sit','stand-from-sit'],'dragon-v005-r25-pose-qa.json',6,120);
document.querySelector('#seek').onclick=async()=>{paused=true;await reset();for(let i=0;i<60;i++)body.step(1/60);const word=document.querySelector('#inspect-motion').value;body.do(word);const frame=Math.max(0,Math.min(180,Number(document.querySelector('#frame').value)||0));for(let i=0;i<=frame;i++)body.step(1/60);status.textContent=`${word} 第 ${frame} 帧 · ${body.layout().mode} · 已暂停，可下载核验`;};
document.querySelector('#resume').onclick=()=>{paused=false;};
for(const [word,label]of [["neutral", "平静"], ["happy", "开心"], ["wink", "眨眼"], ["love", "喜欢"], ["shy", "害羞"], ["surprised", "惊讶"], ["angry", "生气"], ["sad", "难过"], ["sleepy", "犯困"], ["thinking", "思考"], ["smug", "得意"], ["pout", "嘟嘴"], ["worried", "担心"], ["determined", "认真"], ["flustered", "慌张"], ["scared", "害怕"], ["excited", "期待"], ["cry", "大哭"], ["confused", "疑惑"], ["working", "工作"], ["listening", "倾听"]]){const b=document.createElement('button');b.textContent=label;b.onclick=()=>{paused=false;body.do(word);status.textContent=label+' · v005-r25';};document.querySelector('#faces').append(b);}
document.querySelector('#faceqa').onclick=()=>exportQA(['dizzy','run-stop-wave','wave','neutral','sit'],'dragon-v005-r25-faces-qa.json',20,240);
status.textContent='v005-r25 已加载：等待视觉验收';

let secondaryEnabled=true;document.querySelector("#secondary").onclick=e=>{secondaryEnabled=!secondaryEnabled;body.setSecondary(secondaryEnabled);e.target.textContent=secondaryEnabled?"关闭附属动态（对比）":"开启附属动态（对比）";};
document.querySelector("#secondaryqa").onclick=()=>exportQA(["neutral","walk","run","jump","wave","sit"],"dragon-v005-r25-secondary-qa.json",10,100);

document.querySelector("#layerqa").onclick=()=>exportQA(["run-stop-wave"],"dragon-v005-r25-layer-qa.json",6,240);

// Repeatable transitions use the public kit API and timestamps, never internal state writes.
async function interactionQA(scenarios=['rest-wave','run-stop','drag-release','attention']){
 paused=true;const oldWidth=stage.style.width;stage.style.width='960px';const samples=[],checks=[];
 const buttons=[...document.querySelectorAll('button')];buttons.forEach(b=>b.disabled=true);
 try{for(const facing of [1,-1])for(const scenario of scenarios){
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
   if(i%10===0){status.textContent=word+' '+i+'/240';samples.push({word,frame:i,t:(i+1)/60,layout:body.layout(),armLayers:body.armLayerState(),visual:body.visualState(),wings:body.wingState(),wingSignal:body.wingSignal(),png:await capture()});}
  }
 }
 download(JSON.stringify({prototype:manifest.version,master:model.master_sha256,samples,checks,events}),'dragon-r25-interactions-070.json','application/json');status.textContent='已导出左右朝向 '+(scenarios.length*2)+' 组交互检查';
 }finally{stage.style.width=oldWidth;await reset();paused=false;buttons.forEach(b=>b.disabled=false);}
}
document.querySelector('#interactionqa').onclick=()=>interactionQA();
const dragQA=document.createElement('button');dragQA.id='dragqa';dragQA.textContent='检查拎起挣扎与恢复';document.querySelector('#detailsqa').after(dragQA);dragQA.onclick=()=>interactionQA(['drag-release']);
const waveQA=document.createElement('button');waveQA.id='waveqa';waveQA.textContent='检查左右招手与袖口';dragQA.after(waveQA);waveQA.onclick=()=>interactionQA(['rest-wave']);
const browQA=document.createElement('button');browQA.id='browqa';browQA.textContent='检查独立眉毛与慌张';waveQA.after(browQA);browQA.onclick=()=>exportQA(['neutral','happy','love','shy','surprised','angry','sad','sleepy','thinking','smug','pout','worried','determined','flustered','scared','excited','cry','confused','working','listening','sit-flustered','sit-angry'],'dragon-r25-brows.json',30,60);

document.querySelector("#remainingqa").onclick=()=>exportQA(["neutral", "happy", "wink", "love", "shy", "surprised", "angry", "sad", "sleepy", "thinking", "smug", "pout", "worried", "determined", "flustered", "scared", "excited", "cry", "confused", "stand", "jump", "hop", "look", "turn", "nod", "shake", "spin", "sit", "sleep", "dizzy", "walk", "run", "wave", "bow", "shiver", "flap", "dance", "working", "listening"],"dragon-r25-complete-qa.json",20,120);

document.querySelector('#lifecycleqa').onclick=async()=>{
 paused=true;const checks=[];try{for(const word of body.words){await reset();for(let i=0;i<60;i++)body.step(1/60);const accepted=body.do(word);const modes=new Set();for(let i=0;i<420;i++){body.step(1/60);modes.add(body.layout().mode);if(i%60===0){status.textContent='状态检查：'+word+' '+i+'/420';await new Promise(r=>setTimeout(r,0));}}checks.push({word,accepted,modes:[...modes],final:body.layout(),arms:body.armLayerState()});}download(JSON.stringify({version:manifest.version,master:model.master_sha256,checks}),'dragon-r25-lifecycle.json','application/json');status.textContent='39 个标签生命周期检查已完成';}finally{await reset();paused=false;}
};
// A user-stoppable tour; each tag starts from a known pose.
let tourToken=0;
const originalReset=document.querySelector('#reset').onclick;
document.querySelector('#reset').onclick=async()=>{tourToken++;await originalReset();};
document.querySelector('#tour').onclick=async()=>{
 const token=++tourToken;const button=document.querySelector('#tour');button.textContent='停止自动演示';
 if(button.dataset.running==='yes'){button.dataset.running='no';button.textContent='自动演示全部标签';return;}
 button.dataset.running='yes';
 try{for(const word of body.words){if(token!==tourToken)break;paused=true;await reset();body.setSecondary(secondaryEnabled);body.do(word);paused=false;status.textContent='自动演示：'+word;await new Promise(r=>setTimeout(r,4200));}}
 finally{if(token===tourToken){button.dataset.running='no';button.textContent='自动演示全部标签';}}
};
document.querySelector('#expressionqa').onclick=async()=>{
 paused=true;const buttons=[...document.querySelectorAll('button')];buttons.forEach(b=>b.disabled=true);const samples=[],checks=[];let frames=0,irisViolations=0,closedIrisFrames=0;
 try{for(const facing of [1,-1])for(const seated of [false,true]){
  await reset();body.place(stage.clientWidth/2,facing);for(let n=0;n<60;n++)body.step(1/60);if(seated){body.do('sit');for(let n=0;n<90;n++)body.step(1/60);}
  for(const word of ['love','excited','cry','neutral']){
   checks.push({word,seated,facing,accepted:body.do(word)});
   for(let i=0;i<120;i++){
    body.step(1/60);frames++;
    for(const n of root.querySelectorAll('[data-expression-iris]')){const eye=n.parentNode.getAttribute('data-eye-state');if(eye!=='open'){closedIrisFrames++;if(n.getAttribute('visibility')!=='hidden')irisViolations++;}}
    if(i%30===0){const id=word+'-'+(seated?'sit':'stand')+'-'+(facing===1?'right':'left');status.textContent='表情切换：'+id;samples.push({word:id,frame:i,t:(i+1)/60,layout:body.layout(),png:await capture()});}
   }
  }
 }
 download(JSON.stringify({prototype:manifest.version,master:model.master_sha256,checks,frames,closedIrisFrames,irisViolations,samples}),'dragon-r25-expressions-071.json','application/json');status.textContent=`表情切换检查完成：${frames} 帧，眼内装饰违规 ${irisViolations} 次`;
 }finally{await reset();paused=false;buttons.forEach(b=>b.disabled=false);}
};

document.addEventListener('click',e=>{const b=e.target.closest('button');if(b&&b.id!=='tour'&&document.querySelector('#tour').dataset.running==='yes'){tourToken++;document.querySelector('#tour').dataset.running='no';document.querySelector('#tour').textContent='自动演示全部标签';}},true);
document.querySelector('#blinkcontract').onclick=async()=>{
 paused=true;const checks=[];try{for(const word of ['neutral','wink']){await reset();for(let n=0;n<60;n++)body.step(1/60);body.do(word);const frames=[];for(let n=0;n<720;n++){body.step(1/60);frames.push({n,...body.visualState(),secondary:body.secondaryState()});if(n%120===0)await new Promise(r=>setTimeout(r,0));}checks.push({word,frames});}download(JSON.stringify({version:manifest.version,checks}),'dragon-r25-blink-contract.json','application/json');status.textContent='已导出 24 秒眨眼与动态记录';}finally{await reset();paused=false;}
};
document.querySelector('#dynamicsqa').onclick=async()=>{
 paused=true;const samples=[];try{for(const pose of ['neutral','sit']){await reset();body.do(pose);for(let i=0;i<180;i++)body.step(1/60);for(let j=0;j<8;j++){for(let i=0;i<15;i++)body.step(1/60);const values=body.secondaryState();const on=await capture();body.setSecondary(false);body.step(0);const off=await capture();body.setSecondary(true);body.step(0);samples.push({pose,frame:j*15,values,on,off});}}download(JSON.stringify({version:manifest.version,samples}),'dragon-r25-dynamics-pairs.json','application/json');status.textContent='已导出站坐动态开关对比';}finally{await reset();paused=false;}
};

document.querySelector('#wingqa').onclick=()=>exportQA(['flap','jump'],'dragon-r25-grounded-flap-qa.json',6,120);

document.querySelector('#tailqa').onclick=()=>exportQA(['neutral','sit','run-stop-wave','flap'],'dragon-r25-tail-qa.json',12,240);

document.querySelector('#mappingqa').onclick=()=>exportQA(['neutral','happy','sad','sit','sleep','dizzy','run-stop-wave','flap'],'dragon-r25-wing-mapping-qa.json',12,180);

document.querySelector('#seatwingqa').onclick=()=>exportQA(['sit-happy','sit-flap','sit-sad'],'dragon-r25-seated-wings-qa.json',12,180);

document.querySelector('#appendageqa').onclick=()=>exportQA(['neutral','shake','confused','sleep','sit-flap','run-stop-wave'],'dragon-r25-appendages-final.json',8,120);

const perfButton=document.createElement('button');perfButton.id='performanceqa';perfButton.textContent='测量实际帧间隔';document.querySelector('#controls').after(perfButton);
perfButton.onclick=async()=>{paused=false;const rows=[];for(const enabled of [true,false]){body.setSecondary(enabled);const times=[];let prev=performance.now();await new Promise(resolve=>{function frame(now){times.push(now-prev);prev=now;if(times.length<120)requestAnimationFrame(frame);else resolve();}requestAnimationFrame(frame);});const sorted=times.slice(5).sort((a,b)=>a-b);rows.push({secondary:enabled,fps:1000/(sorted.reduce((a,b)=>a+b,0)/sorted.length),p50:sorted[Math.floor(sorted.length*.5)],p95:sorted[Math.floor(sorted.length*.95)],over33:sorted.filter(v=>v>33.4).length});}body.setSecondary(true);status.textContent=JSON.stringify({performance:rows});};

document.querySelector('#detailsqa').onclick=()=>exportQA(['neutral','flap','wave','shake','sit','sit-flap','stand-from-sit','turn','run-stop-wave'],'dragon-r25-details.json',20,120);

document.querySelector('#zoom').onclick=async()=>{paused=true;inspectScale=inspectScale===1.25?3:1.25;stage.style.height=inspectScale===3?'800px':'440px';stage.style.width=inspectScale===3?'960px':'';await reset();paused=false;status.textContent='检查缩放 '+inspectScale;};

const livelyQA=document.createElement('button');livelyQA.id='livelyqa';livelyQA.textContent='检查点击呆毛与情绪振翅';document.querySelector('#detailsqa').after(livelyQA);livelyQA.onclick=()=>exportQA(['click-react','happy-release','flap','dizzy','sit-happy'],'dragon-r25-lively.json',15,180);

const dizzyQA=document.createElement('button');dizzyQA.id='dizzyqa';dizzyQA.textContent='检查晕乎表情与恢复';document.querySelector('#detailsqa').after(dizzyQA);dizzyQA.onclick=()=>exportQA(['dizzy','sit'],'dragon-r25-seated-open-arms.json',10,210);

const seatedNewQA=document.createElement('button');seatedNewQA.id='seatednewqa';seatedNewQA.textContent='检查重绘坐姿';document.querySelector('#detailsqa').after(seatedNewQA);seatedNewQA.onclick=()=>exportQA(['sit','stand-from-sit','sit-happy','sit-flap','dizzy'],'dragon-r25-seated-rebuilt.json',15,150);

const releaseQA=document.createElement("button");releaseQA.id="releaseqa";releaseQA.textContent="检查呆毛与音符";document.querySelector("#detailsqa").after(releaseQA);releaseQA.onclick=()=>exportQA(["dizzy","click-react","dance","turn"],"dragon-release-101.json",12,192);
