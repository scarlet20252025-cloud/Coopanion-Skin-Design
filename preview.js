import * as kit from '/upstream/kit/body.js';
import { createStarWitchBody } from '/pack/star-witch/figure.js';

const stage=document.getElementById('stage'), status=document.getElementById('status');
const sliders=[document.getElementById('lookX'),document.getElementById('lookY')];
const base=new URL('/pack/star-witch/',location.href);
const controls={};
const bounds=()=>({W:stage.clientWidth,H:stage.clientHeight,floorY:stage.clientHeight-30,
  S:Math.min(2.12,(stage.clientHeight-48)/235,stage.clientWidth/218)});
const labels={idle:'待机',walk:'走路',run:'跑步',air:'腾空',land:'落地',drag:'被拎起',sit:'坐下',
  sleep:'睡觉',wake:'起身',dizzy:'眩晕',crouch:'蓄力'};
let body, side=1, speaking=0, syllable=0, revision;
let updates=[];
const readRevision=async()=>(await fetch('/revision',{cache:'no-store'})).text();

async function newBody() {
  const current=await readRevision();
  const model=await (await fetch(new URL('model.json',base),{cache:'no-store'})).json();
  const fullCanvas=new Map();
  for (const [name,part] of Object.entries(model.parts)) {
    if(part.count===undefined){
      fullCanvas.set(part.file,'/parts/'+name+'.png');
      part.box=[0,0,...model.canvas];
    }
  }
  const x=body?.layout().x??stage.clientWidth/2;
  const facing=body?.layout().facing??1;
  const content=document.createElement('div');
  content.style.cssText='position:absolute;inset:0';
  stage.append(content);
  try {
    const factory=await import('/pack/star-witch/figure.js?v='+encodeURIComponent(current));
    const next=await factory.createStarWitchBody(base,{
      kit,model,controls,host:{root:content,bounds,start:{x,facing},
        emit(event,detail){
          if(event==='mode') status.textContent=labels[detail.mode]??detail.mode;
          updates.push([event,detail]);
          if(updates.length>80) updates.shift();
        },sound(){}},
      asset:path=>new URL((fullCanvas.get(path)??path)+'?v='+encodeURIComponent(current),base),
    });
    body?.dispose();
    for(const old of stage.querySelectorAll(':scope > div:not(#floor)')) if(old!==content) old.remove();
    body=next;
    revision=current;
    body.set({roam:'off'});
    body.step(0);
    document.documentElement.dataset.ready='true';
    status.textContent='待机';
  }catch(error){
    content.remove();
    throw error;
  }
}

function action(name) {
  if(!body) return;
  const button=document.querySelector(`[data-action="${name}"]`);
  if(['walk','run'].includes(name)) {
    body.walk(bounds().W*(side>0?.77:.23),name==='run',name+'-preview');
    side=-side;
  }else if(name==='talk'){
    speaking=performance.now()+1800;
    syllable=0;
  }else if(name==='listen'){
    body.set({listening:true});setTimeout(()=>body.set({listening:false}),1800);
  }else if(name==='follow'){
    delete controls.look;
    sliders.forEach(el=>el.value='0');
  }else if(['closed','anchors','compare','theme'].includes(name)){
    const on=button.getAttribute('aria-pressed')!=='true';
    button.setAttribute('aria-pressed',String(on));
    if(name==='theme') document.documentElement.dataset.theme=on?'dark':'light';
    else controls[{closed:'closedEyes',anchors:'showJoints',compare:'still'}[name]]=on;
  }else body.do(name);
}

for(const slider of sliders) slider.addEventListener('input',()=>controls.look=sliders.map(input=>+input.value));
for(const button of document.querySelectorAll('[data-action]')) button.addEventListener('click',()=>action(button.dataset.action));
for(const event of ['down','move','up','cancel','leave']) stage.addEventListener('pointer'+event,e=>{
  if(!body)return;
  const r=stage.getBoundingClientRect();
  body.pointer(event,{x:e.clientX-r.left,y:e.clientY-r.top,t:e.timeStamp});
  if(event==='down'&&body.layout().pressing) stage.setPointerCapture(e.pointerId);
});
new ResizeObserver(()=>body?.resize()).observe(stage);

function tick(time) {
  if(body) {
    if(time<speaking&&time>=syllable) {body.talk();syllable=time+180;}
    body.step(Math.min((time-last)/1000,.045));
  }
  last=time;
  requestAnimationFrame(tick);
}
let last=performance.now();
try {
  await newBody();
  requestAnimationFrame(tick);
  let loading=false;
  setInterval(async()=>{
    if(loading) return;
    try {
      loading=true;
      if((await readRevision())!==revision) await newBody();
    } catch(error) {status.textContent='热更新失败 '+error.message;}
    finally {loading=false;}
  },3000);
  window.witchPreview={get body(){return body;},controls,action,get events(){return updates;}};
}catch(error){
  status.textContent='加载失败 '+error.message;
  document.documentElement.dataset.ready='error';
  console.error(error);
}
