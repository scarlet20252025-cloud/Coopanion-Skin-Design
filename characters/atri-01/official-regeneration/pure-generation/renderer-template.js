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
 let mounted,root,stand,seat,head,back,armFront,faceHost,faceStand,faceSeat,fxStand,fxSeat,effectsStand,effectsSeat,lastT=0,poseAge=99,poseSeated=false,poseDy=0,seatMix=0,low=0;
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
  faceStand=buildFace('standing',faceHost);effectsStand=buildFaceEffects('standing',faceHost,faceStand);
  // The marks around the head go above the whole figure: kit/body.js only declares the flags, and in
  // the official pack the figure paints them into its own group appended after the body (whale drawFx).
  fxStand=n('g',{'data-fx':'standing'});stand.append(fxStand);
  place('seated-clean',seat);faceSeat=buildFace('seated',seat);effectsSeat=buildFaceEffects('seated',seat,faceSeat);
  fxSeat=n('g',{'data-fx':'seated'});seat.append(fxSeat);mounted=g;
 }
 // 2026-10-24: integer pixel offsets that carry the standing face onto the seated head.
 // Derived once from the two rigs (see the comment in buildFace) and frozen here, so the runtime does
 // no arithmetic and every number is a whole pixel - no interpolation, no halo.
 const POSE_OFFSET={
  standing:{group:[0,0],eyes:[[0,0],[0,0]],eyeArt:[0,0],mouth:[0,0],brows:[[0,0],[0,0]]},
  seated:{group:[0,305],eyes:[[3,0],[-9,-11]],eyeArt:[-3,-5],mouth:[-8,-2],brows:[[-14,1],[-8,-11]]}
 };
@@FACE@@
 // ---- figure-side effects -----------------------------------------------------------------------
 // kit/body.js declares these flags on its FACES table and never consumes them, so in the official
 // pack the FIGURE paints them. Reference: references/whale-coopanion-repro-kit/assets/shipped/
 // preview-pkg/web/whale/figure.js - drawFx() draws the marks around the head (sweat, anger vein,
 // question mark, exclamation mark, the orbit stars of 晕乎, listening arcs, thinking bubbles),
 // paintOpenEye() the twinkling iris stars (期待 is documented as 「眼睛里闪着星星」), and
 // paintStreams() the tears that run down the cheeks of 大哭.
 // Every position below is the official one, in kit logo units (x=128 under the body, soles y=256),
 // so the marks land where the official art puts them instead of somewhere guessed; every size is the
 // official number of logo units turned into master pixels. probes/check-fx-clearance.py checks that
 // each spot is empty canvas in this pack's own assembled art.
 const U=1/s,rd=v=>Math.round(v*100)/100,lg=([x,y])=>[(x-128)*U+model.center_x,(y-256)*U+model.feet_y];
 const FX_ORBIT=[124,34],FX_THINK=[204,52],FX_SWEAT=[196,88],FX_ANGER=[190,62],FX_ASK=[206,36],FX_LISTEN=[214,116];
 const FX_STAR='M0 -7L2 -2L7 -2L3 1L4.5 6.5L0 3.3L-4.5 6.5L-3 1L-7 -2L-2 -2Z';
 const FX_DROP='M0 -9C4 -3 6 0 6 3.5A6 6 0 0 1 -6 3.5C-6 0 -4 -3 0 -9Z';
 const FX_ANGER_VEIN='M-11 -3Q-3 -3 -3 -11M3 -11Q3 -3 11 -3M11 3Q3 3 3 11M-3 11Q-3 3 -11 3';
 const FX_BANG='M0 -16V3',FX_ASK_MARK='M-8 -9Q-8 -19 0 -19Q9 -19 9 -11Q9 -4 0 -1V4',FX_ACCENT=model.accent||'#658faa';
 // the iris of each open eye, measured from the four accepted eye textures (probes/measure-iris-centre.py)
 // The face is drawn in the standing frame for both poses (see expression-face.js), so one iris table
 // serves both; the seated pose maps it with the fit below.
 const FX_IRIS=[{cx:556.5,cy:480.9,w:53,h:69},{cx:711,cy:457.6,w:62,h:70}];
 // 2026-10-23: similarity that fits the standing face onto the seated head, from the two rigs' eye boxes.
 // Seated expressions reuse the standing art, so everything inside the face group is mapped by this.
 const FX_POSE_FIT=(()=>{const a=model.expression_rig.standing,b=model.expression_rig.seated;
  const c=e=>[e[0]+e[2]/2,e[1]+e[3]/2],A=a.eyes.map(c),B=b.eyes.map(c);
  const vx=A[1][0]-A[0][0],vy=A[1][1]-A[0][1],wx=B[1][0]-B[0][0],wy=B[1][1]-B[0][1];
  const s=Math.hypot(wx,wy)/Math.hypot(vx,vy),th=Math.atan2(wy,wx)-Math.atan2(vy,vx);
  const co=Math.cos(th),si=Math.sin(th),m=[s*co,s*si,-s*si,s*co,0,0];
  m[4]=B[0][0]-(m[0]*A[0][0]+m[2]*A[0][1]);m[5]=B[0][1]-(m[1]*A[0][0]+m[3]*A[0][1]);
  return {standing:null,seated:m};})();
 // dx/dy are master-pixel offsets for the seated drawing, the same convention the anchors getter uses;
 // the mark table itself stays in logo units, so the pose offset is applied after the conversion.
 // The face-side effects live inside the face group, which the seated pose already maps onto the seated
 // head, so they are all placed in the standing frame. Only the marks around the head (drawn outside the
 // face) need the pose offset, which is why fxFrame carries it and fxFace does not.
 function fxFace(){return{rig:model.expression_rig.standing,iris:FX_IRIS}}
 function fxFrame(seated){return{dx:seated?-3:0,dy:seated?298:0,rig:model.expression_rig.standing,iris:FX_IRIS}}
 function buildFaceEffects(pose,parent,state){
  const defs=n('defs'),paths=n('g',{'data-tear-paths':pose}),streams=n('g',{'data-streams':pose});
  const gradId=`${clipPrefix}-tear-${pose}`,grad=n('linearGradient',{id:gradId,x1:'0',y1:'0',x2:'0',y2:'1'});
  grad.append(n('stop',{offset:'0','stop-color':'#78c3ff','stop-opacity':'.95'}),n('stop',{offset:'1','stop-color':'#78c3ff','stop-opacity':'.3'}));
  defs.append(grad);streams.append(defs,paths);
  // the streams run under the features, where the official figure paints them into the face texture
  state.g.insertBefore(streams,state.g.children[1]||null);
  // inside the face group, so the seated fit carries the stars onto the seated eyes as well
  const sparkle=n('g',{'data-sparkle':pose});state.g.append(sparkle);const holders=[];
  for(let i=0;i<2;i++){
   const mid=`${clipPrefix}-iris-${pose}-${i}`,mask=n('mask',{id:mid,maskUnits:'userSpaceOnUse',x:0,y:0,width:W,height:H,style:'mask-type:alpha'});
   mask.append(n('image',{width:W,height:H,href:textures.get(parts.get('eye-'+i).file)}));
   defs.append(mask);
   const holder=n('g',{mask:`url(#${mid})`,display:'none'});sparkle.append(holder);holders.push(holder);
  }
  return{streams,paths,holders,grad:`url(#${gradId})`,tearPainted:'',starPainted:['','']};
 }
 /** 期待: two white four-pointed stars on the iris, twinkling (whale paintOpenEye). */
 function paintSparkle(state,face,seated,t){
  const art=(seated?faceSeat:faceStand)?.currentEyeArt,iris=fxFace().iris;
  for(let i=0;i<2;i++){
   const holder=state.holders[i],shown=art==='open'||(art==='wink'&&i===0);
   if(!face.sparkle||!shown){if(holder.getAttribute('display')!=='none')holder.setAttribute('display','none');continue}
   const e=iris[i];let s='';
   for(const [fx,fy,rf] of [[-.16,-.2,.25],[.2,.2,.135]]){
    const R=e.w*rf*(.8+.3*Math.sin(t*7+rf*100+(i===0?0:1))),q=R*.28,cx=e.cx+fx*e.w,cy=e.cy+fy*e.h;
    s+=`<path fill="rgba(255,255,255,.95)" d="M${rd(cx)} ${rd(cy-R)}Q${rd(cx+q)} ${rd(cy-q)} ${rd(cx+R)} ${rd(cy)}Q${rd(cx+q)} ${rd(cy+q)} ${rd(cx)} ${rd(cy+R)}Q${rd(cx-q)} ${rd(cy+q)} ${rd(cx-R)} ${rd(cy)}Q${rd(cx-q)} ${rd(cy-q)} ${rd(cx)} ${rd(cy-R)}Z"/>`;
   }
   if(state.starPainted[i]!==s){holder.innerHTML=s;state.starPainted[i]=s}
   holder.setAttribute('display','inline');
  }
 }
 /** 大哭: a tear running from each eye down the cheek (the whale figure's paintStreams shape).
  *  It is aimed from the eye's lower lid at the figure's own tear anchor, because the kit's own drop
  *  particle is a whole logo-unit teardrop: on this smaller face it has to fall past the eye at the
  *  side of the head, not on top of it, so the stream is what ties the eye to the drop. */
 function paintStreams(state,face,seated,t){
  let s='';
  // 2026-10-23 user feedback: "不要这两条激光一样的眼泪" - the cone read as two hard
  // laser beams across the face, so the streams are no longer drawn. The two side teardrops
  // (anchors.tears) stay: they are the part that reads as crying. The code is kept behind this
  // flag in case a softer version is wanted later.
  if(false&&face.streams){
   const p=fxFace(),two=(model.anchors.tears||[]).length>=4?model.anchors.tears:null;
   for(let i=0;i<2;i++){
    const iris=p.iris[i],x0=iris.cx,y0=iris.cy+iris.h/2+4;
    const x1=(two?two[i*2]:iris.cx),y1=(two?two[i*2+1]:p.rig.mouth[1]+20)-26;
    const dx=x1-x0,dy=y1-y0,len=Math.hypot(dx,dy)||1,ux=dx/len,uy=dy/len,nx=-uy,ny=ux;
    const w=iris.w*.22,w0=w*.15,w1=w*.75,wb=3*Math.sin(t*6+i);
    s+=`<path fill="${state.grad}" d="M${rd(x0+nx*w0)} ${rd(y0+ny*w0)}L${rd(x1+nx*w1)} ${rd(y1+ny*w1)}Q${rd(x1+ux*w1*1.2+nx*wb)} ${rd(y1+uy*w1*1.2+ny*wb)} ${rd(x1-nx*w1)} ${rd(y1-ny*w1)}L${rd(x0-nx*w0)} ${rd(y0-ny*w0)}Z"/>`;
   }
  }
  if(state.tearPainted!==s){state.paths.innerHTML=s;state.tearPainted=s}
 }
 /** The official mark flags around the head (whale drawFx): 晕乎 stars, 生气 vein, 惊讶 exclamation,
  *  疑惑 question mark, 倾听 arcs, 思考 bubbles, and the cold sweat of 被拎起 / 慌张 / 害怕 / 担心 / 冲刺. */
 function paintHeadMarks(group,face,seated,t){
  const p=fxFrame(seated),P=v=>{const m=lg(v);return[m[0]+p.dx,m[1]+p.dy]};let s='';
  if(face.orbit){
   const c=P(FX_ORBIT);
   for(let i=0;i<3;i++){
    const a=t*3.2+i*2.094,sn=Math.sin(a);
    s+=`<path fill="#ffd23f" stroke="#3a2f7a" stroke-width="1.6" stroke-linejoin="round" opacity="${sn<0?.55:1}" transform="translate(${rd(c[0]+56*U*Math.cos(a))} ${rd(c[1]-4*U+10*U*sn)}) scale(${rd((sn<0?.7:1)*U)})" d="${FX_STAR}"/>`;
   }
  }
  if(face.listen){
   const c=P(FX_LISTEN);
   for(let i=0;i<3;i++){
    const q=(t*.9+i/3)%1,r=(36-24*q)*U;
    s+=`<path fill="none" stroke="${FX_ACCENT}" stroke-width="${rd(5*U)}" stroke-linecap="round" opacity="${rd(Math.sin(Math.PI*q))}" d="M${rd(c[0]+r*Math.cos(-.55))} ${rd(c[1]+r*Math.sin(-.55))}A${rd(r)} ${rd(r)} 0 0 1 ${rd(c[0]+r*Math.cos(.55))} ${rd(c[1]+r*Math.sin(.55))}"/>`;
   }
  }
  if(face.think){
   const c=P(FX_THINK);
   for(let i=0;i<3;i++){
    const q=(t*.8+i/3)%1;
    s+=`<circle fill="#e8f0ff" stroke="${FX_ACCENT}" stroke-width="${rd(3*U)}" cx="${rd(c[0]+10*U*i)}" cy="${rd(c[1]-20*U*i-6*U*q)}" r="${rd((4+3*i)*U)}" opacity="${rd(.4+.6*Math.sin(Math.PI*q))}"/>`;
   }
  }
  if(face.sweat){
   const c=P([FX_SWEAT[0],FX_SWEAT[1]+3*Math.sin(t*7)]);
   s+=`<path fill="#8fd0ff" stroke="#2f5fae" stroke-width="1.4" transform="translate(${rd(c[0])} ${rd(c[1])}) scale(${rd(1.4*U)})" d="${FX_DROP}"/>`;
  }
  if(face.anger){
   const c=P(FX_ANGER);
   s+=`<g transform="translate(${rd(c[0])} ${rd(c[1])}) scale(${rd((1+.12*Math.sin(t*10))*U)})" fill="none" stroke="#e5484d" stroke-width="5" stroke-linecap="round"><path d="${FX_ANGER_VEIN}"/></g>`;
  }
  if(face.bang){
   const c=P(FX_ASK);
   s+=`<g transform="translate(${rd(c[0])} ${rd(c[1])}) scale(${rd(U)})"><path fill="none" stroke="#252049" stroke-width="8" stroke-linecap="round" d="${FX_BANG}"/><circle fill="#252049" cx="0" cy="14" r="4.5"/></g>`;
  }
  if(face.question){
   const c=P(FX_ASK);
   s+=`<g transform="translate(${rd(c[0])} ${rd(c[1])}) scale(${rd((1+.06*Math.sin(t*3))*U)})"><path fill="none" stroke="#252049" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" d="${FX_ASK_MARK}"/><circle fill="#252049" cx="0" cy="14" r="4.5"/></g>`;
  }
  if(group.__painted!==s){group.innerHTML=s;group.__painted=s}
 }
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
   // 2026-10-30: 害羞 tilts the head 2 degrees - the third ingredient of the GPT dragon's shy beside
   // `eye:'half'` and `blush:.9` (it does `angle+=face.tilt` before building the head transform).
   // Applied here because this one angle already drives head, back and faceHost together, so the
   // face follows the tilt without a second transform.
   const shyTilt=o.face==='shy'?2:0;
   const headAngle=(kind==='nod'?-3.6*Math.sin(k*Math.PI*2)*e:0)+(kind==='shake'?2.8*Math.sin(k*Math.PI*6)*e:0)+.38*Math.sin(o.t*1.6)+(o.look?.[0]||0)*.09+shyTilt;
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
   // The kit hands the effect flags over in `face` and leaves drawing them to the figure, exactly as
   // the official pack does: the iris stars and the cheek streams belong to the face, the marks around
   // the head go above the whole figure.
   paintStreams(effectsStand,face,false,o.t);paintStreams(effectsSeat,face,true,o.t);
   paintSparkle(effectsStand,face,false,o.t);paintSparkle(effectsSeat,face,true,o.t);
   paintHeadMarks(fxStand,face,false,o.t);paintHeadMarks(fxSeat,face,true,o.t);
  },dispose(){mounted=null;nodes.clear();faceNodes.clear()}
 };
 const native=opts.kit.createBody(opts.host,{figure});
   // 2026-10-16: the official body exposes ONE word entry point. kit/body.js createBody() returns
   // `do: ctl.doWord`, and that one function takes expressions (angry, sad, excited...) and motions
   // (walk, run, jump, bow, dance...) alike; it does NOT return `setExpr` at all, so the guarded call
   // below is a no-op that stays only for a body that might expose it. This renderer used to forward
   // everything to `native.do(...)`, which does not exist either, so every word outside the locally
   // handled gestures was silently dropped until the forward went to doWord.
   return {...native,words:model.words,visualState:()=>({face:lastFace,pose:poseSeated?'seated':'standing',seatMix,blink,eyeArt:(poseSeated?faceSeat:faceStand)?.currentEyeArt}),secondaryState:()=>({ahoge:tuft,waveAngle,tailLeft:hairL,tailRight:hairR,bodyScaleRatio}),do:word=>{if(!model.words.includes(word))return false;try{if(native.setExpr)native.setExpr(word)}catch(e){}const m=native.doWord||native.do;return m?m.call(native,word):false},
  pointer(type,p){if(type==='down')pointerStart={...p};if(type==='up'&&pointerStart){if(Math.hypot((p.x??pointerStart.x)-pointerStart.x,(p.y??pointerStart.y)-pointerStart.y)<8)tuftV+=50;pointerStart=null}return native.pointer(type,p)}
 };
}
