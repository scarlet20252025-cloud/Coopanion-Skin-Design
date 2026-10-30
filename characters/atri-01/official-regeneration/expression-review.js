const NS='http://www.w3.org/2000/svg';
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const n=(tag,attrs={})=>{const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);return e;};
const base='/scratch/candidates/atri-hair-junctions/';
const model=await(await fetch(base+'model.json')).json(),parts=new Map(model.parts.map(p=>[p.id,p])),textures=new Map(model.parts.map(p=>[p.file,base+p.file]));
const [W,H]=model.canvas,faceNodes=new Map();let clipPrefix='';
 function buildFace(pose,parent){
  const rig=model.expression_rig[pose],g=n('g',{'data-face':pose}),eyes=[];parent.append(g);
  const defs=n('defs');g.append(defs);
  const foreheadId=`${clipPrefix}-${pose}-forehead`,forehead=n('mask',{id:foreheadId,maskUnits:'userSpaceOnUse',x:0,y:0,width:W,height:H,style:'mask-type:alpha'});
  const foreheadPart=parts.get((pose==='standing'?'':'seat-')+'brow-mask');forehead.append(n('image',{width:W,height:H,href:textures.get(foreheadPart.file)}));defs.append(forehead);
  for(let i=0;i<2;i++){const id=(pose==='standing'?'eye-':'seat-eye-')+i;
   const source=n('image',{width:W,height:H,href:textures.get(parts.get(id).file)});g.append(source);
   const happyId=(pose==='standing'?'':'seat-')+`closed-happy-${i}`;
   const happy=n('image',{width:W,height:H,href:textures.get(parts.get(happyId).file)});g.append(happy);eyes.push({source,happy});}
  // Each redrawn pair uses one registered posed-face source. No separate eye
  // translations, vertical iris clipping or generic heart/spiral/chevron paths.
  const eyeArt={};
  for(const variant of ['half','late','rest','love','dizzy','pinch']){
   const part=parts.get((pose==='standing'?'':'seat-')+'eye-pair-'+variant);
   eyeArt[variant]=n('image',{width:W,height:H,href:textures.get(part.file),'data-eye-art':variant});g.append(eyeArt[variant]);
  }
  // Brows belong to exposed skin; a screen-space path across the bangs is not a brow.
  const brows=rig.brows.map((_,i)=>n('path',{'data-brow':i,fill:'none',stroke:'#74564f','stroke-width':3.2,'stroke-linecap':'round',mask:`url(#${foreheadId})`}));brows.forEach(e=>g.append(e));
  const pinchPart=parts.get((pose==='standing'?'':'seat-')+'pinch-mouth');
  const pinchMouth=n('image',{width:W,height:H,href:textures.get(pinchPart.file),'data-pinch-mouth':pose});g.append(pinchMouth);
  const mouth=n('g',{'data-mouth-style':'neutral'}),lip=n('path',{fill:'none',stroke:'#a96165','stroke-width':2.8,'stroke-linecap':'round','stroke-linejoin':'round'}),tongue=n('path',{fill:'#eea0aa',stroke:'none'});
  mouth.append(lip,tongue);g.append(mouth);
  const state={g,eyes,eyeArt,brows,mouth,lip,tongue,pinchMouth,pose,rig,currentEyeArt:'open'};faceNodes.set(pose,state);return state;
 }
 function paintFace(state,f,o){
  const {rig,eyes,eyeArt,brows,mouth,lip,tongue,pinchMouth,pose}=state;
  const happy=['happy','bowing'].includes(f),wink=f==='wink';
  const forcedRest=['sleep','sleepy','squeeze','cry'].includes(f)||o.eyes?.every(e=>e.shape==='down');
  const closure=clamp(Math.max(o.blink||0,o.eyeClose||0,forcedRest?1:0));
  let selected=closure>.88?'rest':closure>.68?'late':closure>.24?'half':'open';
  if(['smug','angry','determined','content'].includes(f)&&selected==='open')selected='half';
  if(['flustered','dragged'].includes(f))selected='pinch';
  else if(f==='dizzy'||f==='love')selected=f;
  // Preserve the user-accepted smiling lashes verbatim, including wave/wink.
  if(happy||wink)selected=happy?'happy':'wink';
  for(let i=0;i<2;i++){
   eyes[i].source.setAttribute('display',selected==='open'||selected==='wink'&&i===0?'inline':'none');
   eyes[i].happy.setAttribute('display',selected==='happy'||selected==='wink'&&i===1?'inline':'none');
   const [ex,ey]=rig.eyes[i];const sy=f==='scared'?1.10:f==='sad'?.90:f==='worried'?.96:1;const sx=f==='scared'?1.035:1;eyes[i].source.setAttribute('transform',selected==='open'&&sy!==1?`translate(${ex} ${ey}) scale(${sx} ${sy}) translate(${-ex} ${-ey})`:'');
  }
  for(const [variant,image]of Object.entries(eyeArt))image.setAttribute('display',selected===variant?'inline':'none');
  state.currentEyeArt=selected;
  const pinch=selected==='pinch';
  const baseBrows=pose==='standing'?[[518,388,550,380,582,393],[680,386,711,357,738,349]]:[[515,691,546,682,576,702],[679,685,698,665,718,657]];
  const pinchBrows=pose==='standing'?[[499,426,552,413,590,393],[688,390,720,405,747,397]]:[[517,729,559,720,596,692],[668,692,694,710,720,705]];
  for(let i=0;i<2;i++){
   const [x0,y0,x1,y1,x2,y2]=(pinch?pinchBrows:baseBrows)[i];
   let outer=0,inner=0,arch=0;
   if(['sad','worried','confused'].includes(f)){outer=13;inner=-7;arch=1;}
   else if(f==='scared'){outer=12;inner=-12;arch=-1;}
   else if(['angry','determined'].includes(f)){outer=-7;inner=16;arch=2;}
   else if(['happy','excited','surprised'].includes(f)){outer=-5;inner=-6;arch=-8;}
   const dy0=i===0?outer:inner,dy2=i===0?inner:outer;
   brows[i].setAttribute('d',`M${x0} ${y0+dy0}Q${x1} ${y1+arch} ${x2} ${y2+dy2}`);

  }
  pinchMouth.setAttribute('display',pinch?'inline':'none');
  mouth.setAttribute('display',pinch?'none':'inline');
  const [x,y]=rig.mouth;
  // Native vector mouth designs: no universal dark talking bowl or double dash.
  // Talking modulates only the chosen design, never replaces its emotion.
  const styles={
   neutral:['M-12 0 Q-2 7 10 -1','none',''],
   happy:['M-17 -2 C-9 10 5 10 17 -4','none',''],
   wink:['M-15 -2 Q-2 11 15 -5','none',''],
   shy:['M-9 2 Q-1 6 7 0','none',''],
   love:['M-10 1 Q0 8 12 -3','none',''],
   surprised:['M-7 -6 C-15 -3 -15 15 -4 17 C7 18 10 0 4 -5 Q0 -9 -7 -6Z','#c47c85','M-9 11 Q-3 7 3 12 Q-2 19 -9 11Z'],
   excited:['M-13 -1 Q-2 8 13 -3','none',''],
   angry:['M-14 5 Q-5 -3 3 0 Q8 2 13 -2','none',''],
   determined:['M-15 3 L11 0','none',''],
   sad:['M-13 5 Q0 -7 12 3','none',''],
   worried:['M-12 4 Q-5 -4 1 0 Q6 4 11 1','none',''],
   scared:['M-9 3 Q0 -3 9 2','none',''],
   smug:['M-12 3 Q3 8 17 -5 M14 -5 L18 -5','none',''],
   content:['M-12 0 Q1 9 13 -2','none',''],
   confused:['M-9 3 Q0 -3 9 2','none',''],
   dizzy:['M-15 1 Q-10 -6 -5 0 Q0 6 5 0 Q10 -5 15 1','none',''],
   sleep:['M-7 1 Q0 3 7 0','none',''],
   sleepy:['M-7 1 Q0 3 7 0','none',''],
   cry:['M-17 8 Q-15 -6 -2 -8 Q12 -8 17 6 Q4 0 -1 7 Q-8 1 -17 8Z','#c7838d','']
  };
  const key=f==='bowing'?'happy':f==='squeeze'?'sleep':styles[f]?f:'neutral';
  const [outline,fill,inner]=styles[key];
  mouth.setAttribute('data-mouth-style',pinch?'source-pinch':key);
  mouth.setAttribute('transform',`translate(${x} ${y}) rotate(-7) scale(1 ${1+Math.min(.18,(o.talk||0)*.18)})`);
  lip.setAttribute('d',outline);lip.setAttribute('fill',fill);
  tongue.setAttribute('d',inner);tongue.setAttribute('display',inner?'inline':'none');

 }

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
