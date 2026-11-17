import * as kit from '/xingyun-v2/vendor/Coopanion-web/kit/body.js';

export const fps = 30;
export const frames = 1056;
const W = 1440, H = 810;
const S = 1.18;
// The extra pixel seats the antialiased sole against the taskbar edge.
const floorY = document.querySelector('.taskbar').offsetTop+1.25;
const bounds = () => ({W, H, floorY, S});
const desktop = document.querySelector('#desktop');
const pointer = document.querySelector('#pointer');
const ring = document.querySelector('#ring');
const title = document.querySelector('#title');
const shade = document.querySelector('#endShade');
const fade = document.querySelector('#fade');
const windows = [...document.querySelectorAll('.window')];

const clamp = x => Math.max(0, Math.min(1, x));
const ease = x => (x=clamp(x), x*x*(3-2*x));
const interpolate = (a,b,k) => a+(b-a)*k;
function curve(keys,t) {
  const next = keys.findIndex(k => t<k[0]);
  if(next===-1) return keys.at(-1).slice(1);
  if(next===0) return keys[0].slice(1);
  const a=keys[next-1], b=keys[next], k=ease((t-a[0])/(b[0]-a[0]));
  return a.slice(1).map((value,i)=>interpolate(value,b[i+1],k));
}

// Keeping the native animation clocks makes frame captures repeatable.
let random=712634;
Math.random=()=>((random=(Math.imul(random,1664525)+1013904223)>>>0)/2**32);
let mian, yun;
let dragging=false, lastFrame=-1;
let sawDrag=false, sawDrop=false, sawRun=false, sawWalk=false, stageNow=0;
let click=null;
const touches={mian:[],yun:[]};
const wakeClick=5.70, rubStart=7.40, rubEnd=9.57;
const grabClick=18.17, letGo=22.10;
const cursorKeys=[
  [0,740,563],[3.30,725,566],[4.65,550,565],[5.47,500,558],[5.96,500,558],
  [6.58,563,516],[7.40,476,521],[9.57,476,521],[11.29,590,565],
  [12.23,628,655],[13.67,730,646],[14.59,735,611],[15.47,844,515],
  [16.74,956,524],[17.86,1037,524],[18.17,1037,524],
  [18.97,1082,354],[19.63,1039,333],[20.32,1079,346],[21.31,1054,381],
  [21.79,1054,396],[22.18,1054,396],[23.07,1145,512],[24.38,1166,548],
  [26.80,1188,583],
];
const cameraKeys=[
  [0,1,720,405],[3.34,1,720,405],[5.27,1.62,489,574],
  [7.52,1.83,485,572],[10.96,1.86,495,571],
  [12.32,1.65,540,578],[14.27,1.60,598,577],
  [17.34,1.65,1029,561],[18.18,1.65,1038,553],
  [19.20,1.98,1061,505],[21.35,1.98,1056,515],
  [22.35,1.96,1067,562],[24.50,1.96,1049,580],[26.30,1.96,1048,579],
  [28.73,1,720,405],[35.2,1,720,405],
];

function stageCursor(t) {
  const [x,y] = curve(cursorKeys,t);
  if(t>rubStart&&t<rubEnd){
    const phase=(t-rubStart)/(rubEnd-rubStart);
    const amplitude=ease(phase/.09)*ease((1-phase)/.09);
    return {
      x:x+amplitude*70*Math.sin(phase*10*Math.PI),
      y:y+amplitude*(6-6*Math.cos(phase*10*Math.PI)),
      t:t*1000,
    };
  }
  return {x,y,t:t*1000};
}

function press(pet) {
  click=stageCursor(stageNow);
  pet.pointer('down',click);
}

const events=[
  [.43,()=>yun.walk(1036,true,'entrance')],
  [wakeClick,()=>press(mian)],
  [5.82,()=>mian.pointer('up',stageCursor(stageNow))],
  [12.35,()=>mian.walk(594,false,'follow-cursor')],
  [15.40,()=>mian.pointer('leave')],
  [16.66,()=>yun.set({listening:true})],
  [17.70,()=>yun.set({listening:false})],
  [grabClick,()=>{press(yun);dragging=true;}],
  [letGo,()=>{yun.pointer('up',stageCursor(stageNow));dragging=false;}],
  [23.57,()=>yun.do('happy')],
  [25.35,()=>yun.do('wag')],
  [27.13,()=>yun.pointer('leave')],
  [28.10,()=>mian.do('sit')],
  [30.32,()=>mian.do('sleep')],
];

// The stool sprite extends below the native standing baseline.
const sheepKit={
  ...kit,
  createBody(host,options){
    const figure=options.figure;
    const corrected=Object.create(figure);
    corrected.draw=(group,face,frame)=>{
      const stool=(frame.sit??0)>.5&&['sit','sleep','dizzy','wake'].includes(frame.mode);
      if(stool) group.setAttribute('transform','translate(0 -12) '+group.getAttribute('transform'));
      figure.draw(group,face,frame);
    };
    return kit.createBody(host,{...options,figure:corrected});
  },
};

async function createPet(path,id,x,facing) {
  const base=new URL(path,location.href);
  const [manifest,model]=await Promise.all(['figure.json','model.json'].map(async name=>{
    const response=await fetch(new URL(name,base));
    if(!response.ok) throw new Error('Unable to load '+response.url);
    return response.json();
  }));
  const factory=(await import(new URL(manifest.entry,base)))[manifest.export];
  const host={
    root:document.getElementById(id),bounds,start:{x,facing},sound(){},
    emit(event,data){
      if(event==='touch') touches[id].push({kind:data.kind,time:stageNow});
    },
  };
  const body=await factory(base,{kit:id==='mian'?sheepKit:kit,host,model});
  body.set({roam:'off'});
  body.step(0);
  return body;
}

function compose(t) {
  const [zoom,cx,cy]=curve(cameraKeys,t);
  const tx=Math.min(0,Math.max(W-W*zoom,W*.5-cx*zoom));
  const ty=Math.min(0,Math.max(H-H*zoom,H*.5-cy*zoom));
  desktop.style.transform=`translate(${tx}px,${ty}px) scale(${zoom})`;
  const p=stageCursor(t);
  pointer.style.transform=`translate(${p.x}px,${p.y}px) scale(${dragging?.92:1})`;
  pointer.style.opacity=String(ease((t-3.02)/.62)*(1-ease((t-26.47)/.67)));
  const ripple=click?t-click.t/1000:Infinity;
  if(ripple<.40){
    ring.style.transform=`translate(${click.x+2}px,${click.y+2}px) scale(${.34+ripple*2.25})`;
    ring.style.opacity=String(.85*(1-ripple/.40));
  }else ring.style.opacity='0';
  const ending=ease((t-30.18)/1.46);
  windows.forEach((window,i)=>{
    window.style.opacity=String(1-ending);
    window.style.translate=`0 ${-12*ending*(i+1)}px`;
  });
  shade.style.opacity=String(ending*.84);
  title.style.opacity=String(ending);
  title.style.transform=`translateY(${18*(1-ending)}px)`;
  fade.style.opacity=String(Math.max(.9*(1-ease(t/.55)),ease((t-34.45)/.75)));
}

function step(frame) {
  const t=frame/fps;
  stageNow=t;
  for(const [at,run] of events) if(frame===Math.round(at*fps)) run();
  compose(t);
  const p=stageCursor(t);
  if(t>=3.30&&t<15.40) mian.pointer('move',p);
  if(t>=15.40&&t<27.13) yun.pointer('move',p);
  mian.step(1/fps);
  yun.step(1/fps);
  const mode=yun.layout().mode;
  sawRun ||= mode==='run';
  sawDrag ||= mode==='drag';
  sawDrop ||= sawDrag&&mode==='land';
  sawWalk ||= mian.layout().mode==='walk';
}

window.filmReady=(async()=>{
  mian=await createPet('/delivery/coopanion-sheep-03-v2.0.4/pack/coopanion-sheep-03/','mian',476,1);
  yun=await createPet('/xingyun-v2/pack/xingyun-v2/','yun',1340,-1);
  mian.do('sit');
  for(let i=0;i<32;i++){mian.step(1/fps);yun.step(1/fps);}
  await document.fonts.ready;
  const wallpaper=new Image();
  wallpaper.src='wallpaper.png';
  await wallpaper.decode().catch(()=>{});
  window.renderFilmFrame=frame=>{
    if(frame<lastFrame) throw new Error('Render frames in chronological order.');
    while(lastFrame<frame) step(++lastFrame);
    return {frame,cloud:yun.layout().mode,sheep:mian.layout().mode,sawRun,sawDrag,sawDrop,sawWalk,touches};
  };
  window.renderFilmFrame(0);
  return {fps, frames};
})();
