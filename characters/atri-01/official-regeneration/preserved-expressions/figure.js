// ATRI source-based SVG rig. Only source geometry; no inherited Dragon coordinates.
const NS='http://www.w3.org/2000/svg';
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const smooth=x=>{x=clamp(x);return x*x*(3-2*x);};
const env=(k,a=.16,b=.77)=>smooth(k/a)*(1-smooth((k-b)/(1-b)));
const exp=(r,dt)=>1-Math.exp(-r*dt);
export async function createLayeredBody(base,opts){
 const model=opts.model,registration=model.part_registration,textures=new Map(),parts=new Map(model.parts.map(p=>[p.id,p]));
 const load=opts.loadImage||(url=>new Promise((ok,bad)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=bad;im.src=url;}));
 for(const file of new Set(model.parts.map(p=>p.file))){const im=await load(opts.asset?opts.asset(file):new URL(file,base));const cv=document.createElement('canvas');cv.width=im.naturalWidth||im.width;cv.height=im.naturalHeight||im.height;cv.getContext('2d').drawImage(im,0,0);textures.set(file,cv.toDataURL());}
 const n=(tag,attrs={})=>{const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);return e;};
 const clipPrefix='atri-'+Math.random().toString(36).slice(2,11);
 const [W,H]=model.canvas,s=model.logo_scale,tx=128-model.center_x*s,ty=256-model.feet_y*s;
 const convert=([x,y])=>[tx+x*s,ty+y*s];
 let hairL=0,hairR=0,hairLV=0,hairRV=0,hairMeshes;
 let mounted,root,stand,seat,head,faceStand,faceSeat,bodyReveal,cloth,lastT=0,tuft=0,tuftV=0,lastFace='neutral',seatMix=0,poseSeated=false,poseAge=99,poseDy=0,waveAngle=0,blink=0,low=0,pointerStart;
 const nodes=new Map(),faceNodes=new Map();
 function mount(g){
  g.replaceChildren();root=n('g',{transform:`translate(${tx} ${ty}) scale(${s})`});g.append(root);
  stand=n('g',{'data-pose':'standing'});seat=n('g',{'data-pose':'seated'});head=n('g');root.append(stand,seat);nodes.clear();
  for(const p of model.parts){const group=n('g',{'data-part':p.id}),im=n('image',{width:W,height:H,href:textures.get(p.file)});group.append(im);nodes.set(p.id,{group,im});
   if(['eye-0','eye-1','seat-eye-0','seat-eye-1'].includes(p.id)||p.id.includes('closed-')||p.id.includes('eye-pair-')||p.id.endsWith('mask')||p.id.endsWith('pinch-mouth'))continue;
   if(p.id==='seated-clean')seat.append(group);
   else if(['head-clean','ahoge'].includes(p.id))head.append(group);
   else stand.append(group);
  }
  // Raised near sleeve occludes the collar tail, but front hair stays above it.
  stand.append(nodes.get('body').group,nodes.get('arm-left').group,nodes.get('garment-rest').group,head);
  cloth=buildCloth(nodes.get('garment-rest'));
  hairMeshes=[buildHair('tail-left'),buildHair('tail-right')];
  // The resting sleeve casts a shadow onto the mother bodice. Release only
  // this occluded side when lifting the arm; never replace the collar/chest.
  const bodyDefs=n('defs'),revealId=clipPrefix+'-body-reveal',softId=clipPrefix+'-reveal-soft';
  const soft=n('filter',{id:softId,x:'-20%',y:'-20%',width:'140%',height:'140%'});soft.append(n('feGaussianBlur',{stdDeviation:9}));bodyDefs.append(soft);
  const reveal=n('mask',{id:revealId,maskUnits:'userSpaceOnUse',x:0,y:0,width:W,height:H,style:'mask-type:luminance'});
  reveal.append(n('rect',{width:W,height:H,fill:'white'}));
  bodyReveal=n('polygon',{points:'418,720 548,720 554,815 543,930 526,1044 411,1055 399,991',fill:'black',opacity:0,filter:`url(#${softId})`});reveal.append(bodyReveal);bodyDefs.append(reveal);stand.prepend(bodyDefs);
  nodes.get('body').im.setAttribute('mask',`url(#${revealId})`);
  faceStand=buildFace('standing',head);faceSeat=buildFace('seated',seat);mounted=g;
 }
 // One connected texture and one continuous deformation field for ordinary
 // sleeve sway. Rotating separate sleeve cutouts opened both bodice seams.
 // Warp a single coverage surface. Overlapping translucent triangles
 // darkened source AA and produced moving seams along the hair silhouette.
 function displacementSurface(node,key,warp,span){
  const map=document.createElement('canvas');map.width=W;map.height=H;
  const ctx=map.getContext('2d'),pixels=ctx.createImageData(W,H);
  for(let y=0;y<H;y++)for(let x=0;x<W;x++){
   const [dx,dy]=warp(x,y),i=(y*W+x)*4;
   pixels.data[i]=Math.round(clamp(.5-dx/span)*256);
   pixels.data[i+1]=Math.round(clamp(.5-dy/span)*256);
   pixels.data[i+2]=128;pixels.data[i+3]=255;
  }
  ctx.putImageData(pixels,0,0);
  const defs=n('defs'),id=clipPrefix+'-'+key+'-continuous';
  const filter=n('filter',{id,filterUnits:'userSpaceOnUse',primitiveUnits:'userSpaceOnUse',x:0,y:0,width:W,height:H,'color-interpolation-filters':'sRGB'});
  filter.append(n('feImage',{href:map.toDataURL(),x:0,y:0,width:W,height:H,preserveAspectRatio:'none',result:'field'}));
  const centered=n('feComponentTransfer',{in:'field',result:'centered'});centered.append(n('feFuncR',{type:'linear',slope:255/256}),n('feFuncG',{type:'linear',slope:255/256}));filter.append(centered);
  const displacement=n('feDisplacementMap',{in:'SourceGraphic',in2:'centered',scale:0,xChannelSelector:'R',yChannelSelector:'G'});
  filter.append(displacement);defs.append(filter);node.group.prepend(defs);
  return {node,id,displacement,span};
 }
 function setDisplacement(surface,amount){
  if(Math.abs(amount)<1e-5){surface.node.im.removeAttribute('filter');return;}
  surface.node.im.setAttribute('filter',`url(#${surface.id})`);
  surface.displacement.setAttribute('scale',surface.span*amount);
 }
 function buildCloth(node){
  return displacementSurface(node,'cloth',(x,y)=>{
   const h=smooth((y-670)/245)*(1-smooth((y-1020)/115));
   const l=1-smooth((x-460)/140),r=smooth((x-710)/70);
   return [9*h*(l-r),3*h*(l+r)];
  },24);
 }
 function deformCloth(amount){setDisplacement(cloth,amount);}
 function buildHair(id){
  // Only the free span moves. Root, head occlusion and lower crossing
  // retain mother coordinates; unavailable hidden silhouettes cannot leak.
  const start=id==='tail-left'?540:620,rise=id==='tail-left'?95:65;
  return displacementSurface(nodes.get(id),id,(_,y)=>{
   const weight=smooth((y-start)/rise)*(1-smooth((y-715)/70));
   return [5*weight,0];
  },12);
 }
 function bendHair(surface,amount){setDisplacement(surface,amount);}
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
 const figure={gestures:['wave','nod','shake'],colors:{z:'#638eaa'},
  get extent(){const b=poseSeated?model.pose_bounds.seated:model.bounds;return [...convert([b[0],b[1]+poseDy]),...convert([b[2],b[3]+poseDy])];},
  get hits(){
   const points=poseSeated?model.pose_hits.seated:model.hits;
   return points.map(([x,y,r])=>[...convert([x,y+poseDy]),r*s]);
  },
  get anchors(){
   const dx=poseSeated?-3:0,dy=(poseSeated?298:0)+poseDy,position=([x,y])=>{const p=convert([x+dx,y+dy]);return[p[0],p[1]-low];};
   return Object.fromEntries(Object.entries(model.anchors).map(([k,v])=>[k,k==='hearts'?[tx+(v[0]+dx)*s,tx+(v[1]+dx)*s,ty+(v[2]+dy)*s-low]:k==='tears'?[position(v),position(v.slice(2))]:position(v)]));
  },
  draw(g,face,o){
   if(mounted!==g)mount(g);
   const dt=clamp(o.t-lastT,1/240,.04);lastT=o.t;seatMix=smooth((o.sit-.05)/.9);
   low=o.low||0;
   // Drawn pose exchange with a small rigid settle. Never squash the bodice,
   // shorten the legs, or crossfade two complete characters during sitting.
   const seated=seatMix>=.5;
   if(seated!==poseSeated){poseSeated=seated;poseAge=0;}else poseAge+=dt;
   poseDy=(poseSeated?-18:9)*Math.exp(-14*poseAge)*Math.cos(18*poseAge);
   stand.setAttribute('display',seated?'none':'inline');seat.setAttribute('display',seated?'inline':'none');
   stand.setAttribute('opacity',1);seat.setAttribute('opacity',1);
   stand.setAttribute('transform',`translate(0 ${poseDy})`);seat.setAttribute('transform',`translate(0 ${poseDy})`);
   const gesture=o.gesture,kind=gesture?.kind,k=gesture?.k||0,e=gesture?env(k):0;
   const nod=kind==='nod'?-3.6*Math.sin(k*Math.PI*2)*e:0;
   const shake=kind==='shake'?2.8*Math.sin(k*Math.PI*6)*e:0;
   const headAngle=nod+shake+.38*Math.sin(o.t*1.6)+(o.look?.[0]||0)*.09;
   head.setAttribute('transform',`rotate(${headAngle} 592 581)`);
   const rear=nodes.get('rear-hair').group;rear.setAttribute('transform',`rotate(${headAngle} 592 581) matrix(${registration['rear-hair'].join(' ')})`);
   const energy=o.mode==='run'?2.6:o.mode==='walk'||o.mode==='dance'?1.7:o.mode==='drag'?2.2:1;
   const targetL=energy*(1.2*Math.sin(o.t*2.05)+.55*Math.sin(o.t*3.3))-.5*headAngle;
   const targetR=energy*(1.05*Math.sin(o.t*2.05+.85)+.45*Math.sin(o.t*3.1))-.5*headAngle;
   hairLV+=(targetL-hairL)*36*dt;hairLV*=Math.exp(-7*dt);hairL=clamp(hairL+hairLV*dt,-5,5);
   hairRV+=(targetR-hairR)*31*dt;hairRV*=Math.exp(-6.5*dt);hairR=clamp(hairR+hairRV*dt,-5,5);
   nodes.get('tail-left').group.setAttribute('transform',`rotate(${headAngle} 592 581)`);bendHair(hairMeshes[0],hairL);
   nodes.get('tail-right').group.setAttribute('transform',`rotate(${headAngle} 592 581)`);bendHair(hairMeshes[1],hairR);
   const wave=kind==='wave';waveAngle=wave?111*e+6*Math.sin(k*Math.PI*6)*e:0;
   const split=wave&&e>0;
   for(const id of ['body','shoulder-underpaint','arm-left','arm-right'])nodes.get(id).group.setAttribute('display',split?'inline':'none');
   nodes.get('garment-rest').group.setAttribute('display',split?'none':'inline');
   const sway=['walk','run','dance'].includes(o.mode)?Math.sin(o.t*(o.mode==='run'?13:7)):0;
   if(!split)deformCloth(sway);
   nodes.get('garment-rest').group.removeAttribute('transform');
   bodyReveal.setAttribute('opacity',wave?smooth(Math.abs(waveAngle)/20):0);
   for(const p of model.parts){
    if(!['leg-left','leg-right','body','shoulder-underpaint','arm-left','arm-right'].includes(p.id))continue;
    let angle=0;
    if(p.id==='arm-left')angle=waveAngle;
    if(p.id.startsWith('leg')&&['walk','run','dance'].includes(o.mode))angle=8*Math.sin(o.t*(o.mode==='run'?14:8)+(p.id==='leg-right'?Math.PI:0));
    const[x,y]=p.pivot;
    nodes.get(p.id).group.setAttribute('transform',`rotate(${angle} ${x} ${y}) matrix(${registration[p.id].join(' ')})`);
   }
   const target=2.8*Math.sin(o.t*2.3)+clamp(o.look?.[0]||0,-6,6)*.17+(o.mode==='drag'?2*Math.sin(o.t*15):0);
   tuftV+=(target-tuft)*80*dt;tuftV*=Math.exp(-11*dt);tuft+=tuftV*dt;tuft=clamp(tuft,-10,10);
   nodes.get('ahoge').group.setAttribute('transform',`rotate(${tuft} 565 169)`);
   lastFace=o.mode==='drag'?'flustered':o.face;
   const transitionClose=poseAge<.14?Math.sin(Math.PI*poseAge/.14):0;
   const faceFrame={...o,eyeClose:Math.max(o.eyeClose||0,transitionClose)};
   blink=Math.max(o.blink||0,faceFrame.eyeClose);
   paintFace(faceStand,lastFace,faceFrame);paintFace(faceSeat,lastFace,faceFrame);
  },dispose(){mounted=null;nodes.clear();faceNodes.clear();}
 };
 const native=opts.kit.createBody(opts.host,{figure});
 return {...native,words:model.words,visualState:()=>({face:lastFace,pose:seatMix>.5?'seated':'standing',seatMix,blink,eyeArt:(seatMix>.5?faceSeat:faceStand)?.currentEyeArt}),secondaryState:()=>({ahoge:tuft,waveAngle,tailLeft:hairL,tailRight:hairR}),
  do:word=>model.words.includes(word)?native.do(word):false,
  pointer(type,p){if(type==='down')pointerStart={...p};if(type==='up'&&pointerStart){if(Math.hypot((p.x??pointerStart.x)-pointerStart.x,(p.y??pointerStart.y)-pointerStart.y)<8)tuftV+=50;pointerStart=null;}return native.pointer(type,p);}
 };
}
