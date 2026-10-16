// Whole generated components. Shared head parent, rigid sleeves and independent pony roots.
const NS='http://www.w3.org/2000/svg';
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const smooth=x=>{x=clamp(x);return x*x*(3-2*x)};
const env=(k,a=.16,b=.77)=>smooth(k/a)*(1-smooth((k-b)/(1-b)));
export async function createLayeredBody(base,opts){
 const model=opts.model,registration=model.part_registration,parts=new Map(model.parts.map(p=>[p.id,p])),textures=new Map(),faceNodes=new Map();
 const load=opts.loadImage||(url=>new Promise((ok,bad)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=bad;im.src=url}));
 for(const file of new Set(model.parts.map(p=>p.file))){
  const im=await load(opts.asset?opts.asset(file):new URL(file,base));
  const c=document.createElement('canvas');c.width=im.naturalWidth||im.width;c.height=im.naturalHeight||im.height;
  c.getContext('2d').drawImage(im,0,0);textures.set(file,c.toDataURL());
 }
 const n=(tag,attrs={})=>{const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);return e};
 const [W,H]=model.canvas,s=model.logo_scale,tx=128-model.center_x*s,ty=256-model.feet_y*s;
 let rigidX=1,rigidY=1,bodyScaleRatio=1;
 const convert=([x,y])=>[128+(tx+x*s-128)*rigidX,256+(ty+y*s-256)*rigidY],clipPrefix='atri-pure-'+Math.random().toString(36).slice(2,11);
 let mounted,root,stand,seat,head,back,armFront,faceHost,faceStand,faceSeat,lastT=0,poseAge=99,poseSeated=false,poseDy=0,seatMix=0,low=0;
 let hairL=0,hairR=0,hairLV=0,hairRV=0,tuft=0,tuftV=0,waveAngle=0,blink=0,lastFace='neutral',pointerStart;
 const nodes=new Map();
 const registered=id=>`matrix(${registration[id].join(' ')})`;
 function place(id,parent){const p=parts.get(id),g=n('g',{'data-part':id,transform:registered(id)});g.append(n('image',{width:W,height:H,href:textures.get(p.file)}));parent.append(g);nodes.set(id,g);return g}
 function mount(g){
  g.replaceChildren();nodes.clear();faceNodes.clear();
  root=n('g',{transform:`translate(${tx} ${ty}) scale(${s})`});stand=n('g',{'data-pose':'standing'});seat=n('g',{'data-pose':'seated'});root.append(stand,seat);g.append(root);
  back=n('g',{'data-head-parent':'back'});stand.append(back);for(const id of ['tail-left','tail-right','rear-hair'])place(id,back);
  for(const id of ['leg-left','leg-right','arm-right','body'])place(id,stand);
  head=n('g',{'data-head-parent':'front'});stand.append(head);for(const id of ['head-clean','tail-left-front','bow-left','bow-right','ahoge'])place(id,head);
  // 2026-10-16 user instruction: mount order is the draw order in this renderer, so the near arm is
  // mounted after the whole hair stack (back hair, head hair, front lock piece, bows, ahoge) and
  // therefore paints above every hair layer. The face group is mounted after the arm and mirrors the
  // head transform every frame, so the features stay above the arm and still follow nods and shakes.
  armFront=n('g',{'data-arm-front':'1'});stand.append(armFront);place('arm-left',armFront);
  faceHost=n('g',{'data-head-parent':'face'});stand.append(faceHost);
  faceStand=buildFace('standing',faceHost);place('seated-clean',seat);faceSeat=buildFace('seated',seat);mounted=g;
 }
@@FACE@@
 const figure={gestures:['wave','nod','shake'],colors:{z:'#638eaa'},
  get extent(){const b=poseSeated?model.pose_bounds.seated:model.bounds;return [...convert([b[0],b[1]+poseDy]),...convert([b[2],b[3]+poseDy])]},
  get hits(){return (poseSeated?model.pose_hits.seated:model.hits).map(([x,y,r])=>[...convert([x,y+poseDy]),r*s])},
  get anchors(){const dx=poseSeated?-3:0,dy=(poseSeated?298:0)+poseDy,position=([x,y])=>{const p=convert([x+dx,y+dy]);return[p[0],p[1]-low]};return Object.fromEntries(Object.entries(model.anchors).map(([k,v])=>[k,k==='hearts'?[tx+(v[0]+dx)*s,tx+(v[1]+dx)*s,ty+(v[2]+dy)*s-low]:k==='tears'?[position(v),position(v.slice(2))]:position(v)]))},
  draw(g,face,o){
   if(mounted!==g)mount(g);
   // Kit wake/landing/breathing applies an outer anisotropic scale even when a
   // figure uses drawn poses. Cancel that scale about the same foot anchor.
   // Reported hits/extents use the same compensation; kit gestures remain native.
   const nativeScale=/scale\(\s*([-\d.e+]+)[ ,]+([-\d.e+]+)\s*\)/.exec(g.getAttribute('transform')||'');
   if(nativeScale){const kx=Math.abs(Number(nativeScale[1])),ky=Math.abs(Number(nativeScale[2])),uniform=Math.sqrt(kx*ky);rigidX=uniform/Math.max(kx,1e-8);rigidY=uniform/Math.max(ky,1e-8);bodyScaleRatio=kx*rigidX/(ky*rigidY)}
   root.setAttribute('transform',`translate(128 256) scale(${rigidX} ${rigidY}) translate(-128 -256) translate(${tx} ${ty}) scale(${s})`);
   const dt=clamp(o.t-lastT,1/240,.04);lastT=o.t;low=o.low||0;seatMix=smooth((o.sit-.05)/.9);
   const seated=seatMix>=.5;if(seated!==poseSeated){poseSeated=seated;poseAge=0}else poseAge+=dt;
   // Exchange two drawn poses with a small rigid settle; never compress the torso.
   poseDy=(seated?-12:7)*Math.exp(-14*poseAge)*Math.cos(18*poseAge);
   stand.setAttribute('display',seated?'none':'inline');seat.setAttribute('display',seated?'inline':'none');
   stand.setAttribute('transform',`translate(0 ${poseDy})`);seat.setAttribute('transform',`translate(0 ${poseDy})`);
   const gesture=o.gesture,kind=gesture?.kind,k=gesture?.k||0,e=gesture?env(k):0;
   const headAngle=(kind==='nod'?-3.6*Math.sin(k*Math.PI*2)*e:0)+(kind==='shake'?2.8*Math.sin(k*Math.PI*6)*e:0)+.38*Math.sin(o.t*1.6)+(o.look?.[0]||0)*.09;
   const parent=`rotate(${headAngle} 592 581)`;head.setAttribute('transform',parent);back.setAttribute('transform',parent);faceHost.setAttribute('transform',parent);
   const energy=o.mode==='run'?2.1:['walk','dance','drag'].includes(o.mode)?1.5:1;
   const tl=energy*(1.05*Math.sin(o.t*2.05)+.4*Math.sin(o.t*3.3))-.4*headAngle,tr=energy*(.95*Math.sin(o.t*2.05+.85)+.35*Math.sin(o.t*3.1))-.4*headAngle;
   hairLV+=(tl-hairL)*36*dt;hairLV*=Math.exp(-7*dt);hairL=clamp(hairL+hairLV*dt,-4,4);
   hairRV+=(tr-hairR)*31*dt;hairRV*=Math.exp(-6.5*dt);hairR=clamp(hairR+hairRV*dt,-4,4);
   for(const [id,angle,pivotX,pivotY] of [['tail-left',hairL,370,300],['tail-left-front',hairL,370,300],['tail-right',hairR,803,300]])
    nodes.get(id).setAttribute('transform',`rotate(${angle} ${pivotX} ${pivotY}) ${registered(id)}`);
   waveAngle=kind==='wave'?111*e+6*Math.sin(k*Math.PI*6)*e:0;
   const gait=['walk','run','dance'].includes(o.mode)?Math.sin(o.t*(o.mode==='run'?14:8)):0;
    // Struggle while held, aligned with the whale pack: kit/body.js flaps every limb as
    // tx = hx + 7*sin(T*11 + i*2.2) and jitters the eyes at 22Hz, so the limbs here flap at 11Hz with
    // the same 2.2 rad phase offset and the hair/tuft shake moves from 15Hz to 21Hz.
    const held=o.mode==='drag';
    for(const [id,angle] of [['arm-left',waveAngle+(kind==='wave'?0:1.2*gait)+(held?3*Math.sin(o.t*11):0)],['arm-right',-.8*gait+(held?3*Math.sin(o.t*11+2.2):0)],['leg-left',8*gait+(held?2*Math.sin(o.t*11+4.4):0)],['leg-right',-8*gait+(held?2*Math.sin(o.t*11+6.6):0)]]){const [x,y]=parts.get(id).pivot;nodes.get(id).setAttribute('transform',`rotate(${angle} ${x} ${y}) ${registered(id)}`)}
    const target=2.8*Math.sin(o.t*2.3)+clamp(o.look?.[0]||0,-6,6)*.17+(held?2.5*Math.sin(o.t*21):0);
   tuftV+=(target-tuft)*80*dt;tuftV*=Math.exp(-11*dt);tuft=clamp(tuft+tuftV*dt,-10,10);nodes.get('ahoge').setAttribute('transform',`rotate(${tuft} 565 169) ${registered('ahoge')}`);
   lastFace=o.mode==='drag'?'flustered':o.face;
   const transitionClose=poseAge<.14?Math.sin(Math.PI*poseAge/.14):0,frame={...o,eyeClose:Math.max(o.eyeClose||0,transitionClose)};
   blink=Math.max(o.blink||0,frame.eyeClose);paintFace(faceStand,lastFace,frame);paintFace(faceSeat,lastFace,frame);
  },dispose(){mounted=null;nodes.clear();faceNodes.clear()}
 };
 const native=opts.kit.createBody(opts.host,{figure});
 return {...native,words:model.words,visualState:()=>({face:lastFace,pose:poseSeated?'seated':'standing',seatMix,blink,eyeArt:(poseSeated?faceSeat:faceStand)?.currentEyeArt}),secondaryState:()=>({ahoge:tuft,waveAngle,tailLeft:hairL,tailRight:hairR,bodyScaleRatio}),do:word=>model.words.includes(word)?native.do(word):false,
  pointer(type,p){if(type==='down')pointerStart={...p};if(type==='up'&&pointerStart){if(Math.hypot((p.x??pointerStart.x)-pointerStart.x,(p.y??pointerStart.y)-pointerStart.y)<8)tuftV+=50;pointerStart=null}return native.pointer(type,p)}
 };
}
