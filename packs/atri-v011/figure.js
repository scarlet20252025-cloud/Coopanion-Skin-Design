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
// stride phase, integrated from travel speed each frame (see the gait block in draw())
let gaitPhase=0;
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
 // 2026-10-30: the seated face is positioned by ONE uniform translate, not per-feature offsets.
// The old table carried different offsets per eye (3,305) / (-9,294) and per brow, taken from
// expression_rig.seated. Those rig numbers are leftovers from the early non-compliant cut-out pass and
// no longer match this face: the far eye landed OUTSIDE the head outline and every seated expression
// looked crooked ("眼睛这里都离开脸了，歪掉了").
// Measured from the actual iris centres of the paired source art:
//   standing irises (558,485) and (710,460); seated irises (553,788) and (706,762)
//   -> offsets (-5,+304) and (-4,+302). Iris spacing is 152 vs 153 and the vertical offset -25 vs -26,
// so the two poses are a PURE TRANSLATION of each other - no rotation, no scale. One uniform (-4,+303)
// therefore fits both eyes and every other feature to within a pixel, which is why the table now has a
// single number instead of per-part deltas. The mouth measures (0,+306) independently, agreeing.
const POSE_OFFSET={
  standing:{group:[0,0],eyes:[[0,0],[0,0]],eyeArt:[0,0],mouth:[0,0],brows:[[0,0],[0,0]]},
  seated:{group:[-4,303],eyes:[[0,0],[0,0]],eyeArt:[0,0],mouth:[0,0],brows:[[0,0],[0,0]]}
 };
 function buildFace(pose,parent){
  // 2026-10-23 user instruction: "坐下的表情都有眼角缺失，形状不对，全都改成跟站立一样的表情状态".
  // The seated set is a separate redraw whose eye art has the fringe baked across the pupil, which is
  // why every seated expression looked wrong. So the seated face is built from the SAME art and the
  // SAME rig as the standing one, and the group carries the similarity that fits the standing eye pair
  // onto the seated eye pair (FX_POSE_FIT, derived from the two rigs at load). Brows, mouth, blush,
  // tear streams and the 期待 stars all live in that group, so the whole expression is mapped with it;
  // the 14 seat-* textures stay in the pack unreferenced.
  // NOTE: this restores the seated-reuse half of 4eec957 only. That commit also changed the mouth table
  // and added the blush layer; the user rejected the mouth ("别用这张嘴"), so those stay withdrawn.
  const rig=model.expression_rig.standing,g=n('g',{'data-face':pose}),eyes=[];parent.append(g);
  // 2026-10-24: the seated face is positioned with INTEGER translations only, never a rotation or a
  // scale. The eye textures ship with a hard 1-bit alpha (0 or 255) whose transparent pixels are pure
  // white; any fractional transform makes the renderer interpolate along that edge and the white bleeds
  // in as a dotted halo - which is what read as "a corner of the eye is missing". Integer translate is
  // a pixel copy, so the art stays byte-identical to the standing render.
  // The two poses' eye pairs are not exactly similar (eye distance 182 vs 170), so one transform cannot
  // place both eyes; each eye and each feature therefore gets its own integer offset from the rigs.
  const OFF=POSE_OFFSET[pose];
  if(OFF.group[0]||OFF.group[1])g.setAttribute('transform',`translate(${OFF.group[0]} ${OFF.group[1]})`);
  const defs=n('defs');g.append(defs);
  const foreheadId=`${clipPrefix}-${pose}-forehead`,forehead=n('mask',{id:foreheadId,maskUnits:'userSpaceOnUse',x:0,y:0,width:W,height:H,style:'mask-type:alpha'});
  const foreheadPart=parts.get('brow-mask');forehead.append(n('image',{width:W,height:H,href:textures.get(foreheadPart.file)}));defs.append(forehead);
  for(let i=0;i<2;i++){const id='eye-'+i;
   const [ox,oy]=OFF.eyes[i];
   const tr=ox||oy?`translate(${ox} ${oy})`:'';
   const source=n('image',{width:W,height:H,href:textures.get(parts.get(id).file),transform:tr});g.append(source);
   const happyId=`closed-happy-${i}`;
   const happy=n('image',{width:W,height:H,href:textures.get(parts.get(happyId).file),transform:tr});g.append(happy);eyes.push({source,happy});}
  // Each redrawn pair uses one registered posed-face source. No separate eye
  // translations, vertical iris clipping or generic heart/spiral/chevron paths.
  const eyeArt={};
  for(const variant of ['half','late','rest','love','dizzy','pinch']){
   const part=parts.get('eye-pair-'+variant);
   const [ax,ay]=OFF.eyeArt;
   eyeArt[variant]=n('image',{width:W,height:H,href:textures.get(part.file),'data-eye-art':variant,
     transform:ax||ay?`translate(${ax} ${ay})`:''});g.append(eyeArt[variant]);
  }
  // 2026-10-30: an extra blush wash, drawn in code. 害羞's strongest sign in BOTH reference projects is
  // blush - the official whale sets shy to blush:1 (its maximum, above 喜欢's .7) and saturates it with
  // lookLock, while the dragon sets shy to blush:.9. Ours is baked into head-clean.png and therefore
  // fixed, so 害羞 adds one more translucent wash over the cheeks. Vector, not new art: each cheek is a
  // flat ellipse with three short slant strokes, so a code-drawn bloom matches without a redraw.
  const blush=n('g',{'data-blush-wash':'1',opacity:0});g.append(blush);
  // Cheek centres measured off head-clean.png, where the art already paints three short slant strokes on
  // each cheek (near 552,545 and 724,520). An earlier version used (549,363)/(702,357) - that is the
  // skin showing BETWEEN THE BANGS, which is why the wash floated over the hair like a pink patch. The
  // wash is a soft radial bloom under those strokes, so it deepens the existing blush rather than
  // painting a new flat shape on top of it.
  // The wash is drawn in the same standing frame as everything else in this group, so it needs no pose
  // offset of its own - the group transform (POSE_OFFSET.group) carries it onto the seated face with the
  // eyes, brows and mouth. An earlier version added a hand-computed (-4,+539) here, which double-counted
  // and dropped the cheeks far below the face on the seated pose.
  for(const [cx,cy] of [[552,545],[724,520]]){
   const gid=`${clipPrefix}-cheekwash-${cx}`,rg=n('radialGradient',{id:gid});
   rg.append(n('stop',{offset:'0','stop-color':'#ee8fa6','stop-opacity':'.62'}),
             n('stop',{offset:'.62','stop-color':'#ee8fa6','stop-opacity':'.34'}),
             n('stop',{offset:'1','stop-color':'#ee8fa6','stop-opacity':'0'}));
   defs.append(rg);
   blush.append(n('ellipse',{cx,cy,rx:30,ry:19,fill:`url(#${gid})`}));
  }
  // Brows belong to exposed skin; a screen-space path across the bangs is not a brow.
  // 2026-10-16 user feedback: "负面表情的眉毛你都没有变化". The forehead mask keeps only the skin between
  // the bangs, so a 3.2px stroke came through as two or three fragments and its travel was lost in the
  // gaps. The stroke is heavier now and the travels below are doubled, so the slant reads through them.
  const brows=rig.brows.map((_,i)=>n('path',{'data-brow':i,fill:'none',stroke:'#74564f','stroke-width':5,'stroke-linecap':'round',mask:`url(#${foreheadId})`}));brows.forEach(e=>g.append(e));
  const pinchPart=parts.get('pinch-mouth');
  const pinchMouth=n('image',{width:W,height:H,href:textures.get(pinchPart.file),'data-pinch-mouth':pose});g.append(pinchMouth);
  const mouth=n('g',{'data-mouth-style':'neutral'}),lip=n('path',{fill:'none',stroke:'#a96165','stroke-width':2.8,'stroke-linecap':'round','stroke-linejoin':'round'}),tongue=n('path',{fill:'#eea0aa',stroke:'none'});
  mouth.append(lip,tongue);g.append(mouth);
  const state={g,eyes,eyeArt,brows,mouth,lip,tongue,pinchMouth,blush,pose,rig,off:OFF,currentEyeArt:'open'};faceNodes.set(pose,state);return state;
 }
 function paintFace(state,f,o){
  const {rig,eyes,eyeArt,brows,mouth,lip,tongue,pinchMouth,pose,off:OFF}=state;
  const happy=['happy','bowing'].includes(f),wink=f==='wink';
  const forcedRest=['sleep','sleepy','squeeze','cry'].includes(f)||o.eyes?.every(e=>e.shape==='down');
  const closure=clamp(Math.max(o.blink||0,o.eyeClose||0,forcedRest?1:0));
  let selected=closure>.88?'rest':closure>.68?'late':closure>.24?'half':'open';
  // 2026-10-30 user instruction: 害羞 = the existing HALF eyes + blush, "龙娘就是这样的，官方的不适合套用
  // 这个角色". The GPT dragon project does exactly this: `shy:{eye:'half', blush:.9}`. The official
  // whale instead parameterises a shrunken round eye (ring rx:13 ry:12 against the default 16/16), but
  // that is only possible because its eyes are drawn as vector primitives in canvas - here the eye is a
  // bitmapped whole (lid + lashes + sclera + iris), so shrinking it scales the lashes too and leaves a
  // gap between lid and eye. Tried both and they were worse than half. Two other attempts were
  // rejected first: a generated replacement pair (ugly, linework did not match) and the shrunken
  // vector route (broken lashes).
  if(['smug','angry','determined','content','shy'].includes(f)&&selected==='open')selected='half';
  if(['flustered','dragged'].includes(f))selected='pinch';
  else if(f==='dizzy'||f==='love')selected=f;
  // Preserve the user-accepted smiling lashes verbatim, including wave/wink.
  if(happy||wink)selected=happy?'happy':'wink';
  for(let i=0;i<2;i++){
   eyes[i].source.setAttribute('display',selected==='open'||selected==='wink'&&i===0?'inline':'none');
   eyes[i].happy.setAttribute('display',selected==='happy'||selected==='wink'&&i===1?'inline':'none');
   // 2026-10-24: this transform OVERWRITES the pose translate set in buildFace, so the pose offset has
   // to be folded in here or sad/scared/worried would snap the eyes back to the standing position.
   const [ex,ey]=rig.eyes[i],[eox,eoy]=OFF.eyes[i];
   const sy=f==='scared'?1.10:f==='sad'?.90:f==='worried'?.96:1;const sx=f==='scared'?1.035:1;
   eyes[i].source.setAttribute('transform',selected==='open'&&sy!==1
     ?`translate(${eox} ${eoy}) translate(${ex} ${ey}) scale(${sx} ${sy}) translate(${-ex} ${-ey})`
     :(eox||eoy?`translate(${eox} ${eoy})`:''));
  }
  for(const [variant,image]of Object.entries(eyeArt))image.setAttribute('display',selected===variant?'inline':'none');
  state.currentEyeArt=selected;
  // 大哭 keeps the rest eyes but borrows the 慌张 mouth and brows, so the mouth flag is its own
  const pinch=selected==='pinch'||f==='cry';
  // the face is always drawn in the standing frame now, so both poses use the standing brow tables
  const baseBrows=[[518,388,550,380,582,393],[680,386,711,357,738,349]];
  const pinchBrows=[[499,426,552,413,590,393],[688,390,720,405,747,397]];
  for(let i=0;i<2;i++){
   const [x0,y0,x1,y1,x2,y2]=(pinch?pinchBrows:baseBrows)[i];
   let outer=0,inner=0,arch=0;
   // 2026-10-16: travels roughly doubled, and 大哭 joins the sad group because the official whale face
   // table gives cry `brows: 'sad'`. sad/worried/cry lift the inner ends, angry/determined drive them
   // down towards the nose, both with the outer end doing the opposite.
   if(['sad','worried','confused','cry'].includes(f)){outer=22;inner=-12;arch=4;}
   else if(f==='scared'){outer=20;inner=-20;arch=-2;}
   else if(['angry','determined'].includes(f)){outer=-12;inner=26;arch=0;}
   else if(['happy','excited','surprised'].includes(f)){outer=-9;inner=-10;arch=-14;}
   const dy0=i===0?outer:inner,dy2=i===0?inner:outer;
   const [bx,by]=OFF.brows[i];
   brows[i].setAttribute('d',`M${x0+bx} ${y0+dy0+by}Q${x1+bx} ${y1+arch+by} ${x2+bx} ${y2+dy2+by}`);

  }
  // 害羞 lights the extra blush wash; every other expression leaves it off.
  if(state.blush)state.blush.setAttribute('opacity',f==='shy'?'1':'0');
  pinchMouth.setAttribute('display',pinch?'inline':'none');
  mouth.setAttribute('display',pinch?'none':'inline');
  // 2026-10-24: OFF.mouth is an OFFSET, not the position - the mouth still sits at rig.mouth and only
  // moves by the pose offset. (Replacing the rig lookup with the offset put the mouth at the canvas
  // origin and made every mouth disappear.)
  const [x,y]=rig.mouth,[mx,my]=OFF.mouth;
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
  };
  // 2026-10-23 user feedback: "大哭的表情明显有严重问题，嘴可以改成慌张那种，其余部分尽量重做".
  // Scope agreed with the user: mouth + brows only. The wailing mouth becomes the 慌张 (pinch) mouth -
  // the open squeezed oval this pack already ships and the user accepted on 慌张 - and the brows follow
  // the pinch set, because a wail pulls the same > < shape. The eyes stay on `rest` (the closed pair
  // the user already accepted for sleep/cry), and the tear streams and side drops stay where they are.
  // This replaces the earlier official-derived routing (cry -> surprised mouth at .8 scale): on this
  // face that came out as a tiny circle floating above the mouth position, which is what the user
  // rejected. `mouthScale` is no longer applied to cry.
  // 大哭 draws the 慌张 source mouth, so the vector table is not consulted for it (and `styles`
  // has no 'source-pinch' entry on purpose - the texture is the design).
  const key=pinch?'neutral':f==='bowing'?'happy':f==='squeeze'?'sleep':styles[f]?f:'neutral',mouthScale=1;
  const [outline,fill,inner]=styles[key];
  mouth.setAttribute('data-mouth-style',pinch?'source-pinch':key);
  mouth.setAttribute('transform',`translate(${x+mx} ${y+my}) rotate(-7) scale(${mouthScale} ${mouthScale*(1+Math.min(.18,(o.talk||0)*.18))})`);
  lip.setAttribute('d',outline);lip.setAttribute('fill',fill);
  tongue.setAttribute('d',inner);tongue.setAttribute('display',inner?'inline':'none');

 }

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
   // 2026-10-30 user feedback: "点击、跳跃之类的动效都太少了，不像官方鲸鱼娘那样Q弹".
   // The squash-and-stretch the kit applies to the group was being cancelled out here.
   // kit/body.js render():  sx = (1 + sq*.7)(1 - .05*stretch)(1 - .009*br)
   //                       sy = (1 - sq)  (1 + .09*stretch)(1 + .016*br)
   // The old compensation was rigid = uniform/k, so the final scale came out as
   //   kx*uniform/kx = uniform  and  ky*uniform/ky = uniform
   // i.e. both axes identical - the ratio ky/kx that IS the squash was divided away and every
   // bounce landed as a flat breathing pulse.
   //
   // Now the compensation only normalises AREA (the figure is drawn at its own size and must not
   // also be scaled by the kit's absolute amount), while the anisotropic RATIO survives:
   //   rigidX = rigidY = 1/uniform   ->   final (kx/u, ky/u), ratio kx/ky intact, area 1
   // SQ_KEEP scales how much of that ratio reaches the drawing: 1 = the kit's own amount, 0 = the
   // old dead behaviour. Landing/jump/throw all go through pet.sq, so this is the one knob for Q弹.
   // 2026-10-31 user feedback: "被提起来的形变程度低一点". Being picked up stretches the body hard
   // (kit: pet.stretch -> 1 while mode==='drag', giving sx -5% and sy +9% on top of the squash), and
   // because the figure is held by the head that stretch reads as the whole body elongating. Drag
   // now keeps only DRAG_KEEP of the anisotropy, so the held pose stays rounder and closer to the
   // artwork while landing/jump still feel springy.
   const SQ_KEEP=.85, DRAG_KEEP=.45;
   const nativeScale=/scale\(\s*([-\d.e+]+)[ ,]+([-\d.e+]+)\s*\)/.exec(g.getAttribute('transform')||'');
   if(nativeScale){
    const kx=Math.abs(Number(nativeScale[1])),ky=Math.abs(Number(nativeScale[2])),uniform=Math.sqrt(Math.max(kx*ky,1e-8));
    // final axis = k^SQ_KEEP * uniform^(1-SQ_KEEP), so the x:y RATIO keeps SQ_KEEP of the kit's own
    // amount while the absolute size is normalised. rigid = final / k = (uniform/k)^(1-SQ_KEEP).
    const keep=o.mode==='drag'?DRAG_KEEP:SQ_KEEP;
    rigidX=Math.pow(uniform/Math.max(kx,1e-8),1-keep);
    rigidY=Math.pow(uniform/Math.max(ky,1e-8),1-keep);
    bodyScaleRatio=(ky*rigidY)/(kx*rigidX);
   }
   root.setAttribute('transform',`translate(128 256) scale(${rigidX} ${rigidY}) translate(-128 -256) translate(${tx} ${ty}) scale(${s})`);
   const dt=clamp(o.t-lastT,1/240,.04);lastT=o.t;low=o.low||0;
   // 2026-10-31 user feedback: "摔晕的动作延迟有点长，站了一会儿才播放坐下眩晕动画".
   // o.sit is the kit's pet.sitK, which ramps in with lerp(sitK, sitT, ease(6,dt)) - about 0.5-0.8 s
   // to reach half. The old mapping smooth((sit-.05)/.9) needed sit = .5 before the drawn pose
   // flipped, so the figure visibly stood through the first half of the wobble; on this body the
   // stand and seat are two separate drawings, so a late flip reads as "nothing happens, then it
   // suddenly sits". The mix now reaches its half point at sit ~.14 and saturates early, so the pose
   // change starts on the same frame the kit begins lowering the body. The settle animation
   // (poseDy) still smooths the swap, so this does not pop.
   seatMix=smooth(clamp(o.sit*3.2,0,1));
   const seated=o.sit>.14;if(seated!==poseSeated){poseSeated=seated;poseAge=0}else poseAge+=dt;
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
   // 2026-10-30 user feedback: "走路的脚步频率也有点慢，不够灵动，步幅度跟不上走路速度".
   // The gait used a FIXED frequency (sin(t*8) walking, sin(t*14) running) with a fixed leg angle,
   // so the feet kept one tempo whatever the travel speed was. The official kit drives both from
   // speed instead (kit/body.js):
   //     pet.phase += 2*PI * rate * dt * max(.35, k)      rate 2.1 walk / 4.4 run  (steps per second)
   //     strideT = (run ? 17 : 10) * (.4 + .6*k)          amplitude grows with speed
   // 2.1 steps/s is 13.2 rad/s and 4.4 is 27.6 - our 8/14 was roughly half the cadence, and the
   // amplitude never moved. Phase is now integrated from speed, and the leg/arm swing scales with it.
   const moving=['walk','run','dance'].includes(o.mode);
   // Speed proxy: the kit hands the figure `swing`, which it computes as
   // clamp(-(pet.velX*.06 + danceTilt), -28, 28) - i.e. travel speed already smoothed and capped.
   // Reading it is more honest than guessing from the mode, and it is the only speed signal a
   // figure-drawn body actually receives (custom.draw gets no raw velocity).
   const kSpeed=clamp(Math.abs(o.swing??0)/28,0,1);
   const kMin=o.mode==='run'?.85:o.mode==='dance'?.5:.45;
   const kk=Math.max(kSpeed,kMin);
   if(moving){
    const rate=o.mode==='run'?4.4:o.mode==='dance'?1.1:2.1;
    // dt is already clamped above; the .35 floor keeps a slow walk from freezing mid-step
    gaitPhase+=Math.PI*2*rate*dt*Math.max(.35,kk);
    if(gaitPhase>Math.PI*2e4)gaitPhase-=Math.PI*2e4;
   }else{
    // settle to the nearest foot-down phase so the legs do not stop mid-stride
    gaitPhase+=((Math.round(gaitPhase/Math.PI)*Math.PI)-gaitPhase)*Math.min(1,8*dt);
   }
   const gait=moving?Math.sin(gaitPhase):0;
   // amplitude follows speed: ±11° at a stroll up to ±16° at a sprint (was a flat ±8°)
   const swingAmp=o.mode==='run'?16:o.mode==='dance'?10:11;
   const swing=swingAmp*(.55+.45*kk);
    // Struggle while held, aligned with the whale pack: kit/body.js flaps every limb as
    // tx = hx + 7*sin(T*11 + i*2.2) and jitters the eyes at 22Hz, so the limbs here flap at 11Hz with
    // the same 2.2 rad phase offset and the hair/tuft shake moves from 15Hz to 21Hz.
    const held=o.mode==='drag';
    // 2026-10-31 user feedback: "走路姿势顺拐". Arm and leg on the SAME side were both +swing*gait,
    // so the left arm came forward exactly when the left leg did. A natural walk is diagonal: each
    // arm moves in anti-phase with the leg on its own side, i.e. the left arm pairs with the right
    // leg. Signs are now arm-left -1.2, arm-right +0.8 against leg-left +1, leg-right -1:
    //     left arm (-) / left leg (+)  opposite     -> 顺拐 gone
    //     left arm (-) / right leg (-) together     -> the diagonal pairing
    // Amplitudes stay asymmetric (1.2 near, 0.8 far) because the near arm is the one the viewer
    // reads; that asymmetry was accepted and is not what caused the fault.
    // The swing now comes from `swing` (speed-scaled) instead of a flat 8 degrees, and the two legs
    // use opposite phases of the SAME integrated gaitPhase, which is what makes a stride read as a
    // stride: at 8 deg the foot travelled 424*sin(8) = 59 px on a 1290 px figure, too short to match
    // the new cadence.
    for(const [id,angle] of [['arm-left',waveAngle+(kind==='wave'?0:-1.2*swing*gait)+(held?3*Math.sin(o.t*11):0)],['arm-right',.8*swing*gait+(held?3*Math.sin(o.t*11+2.2):0)],['leg-left',swing*gait+(held?2*Math.sin(o.t*11+4.4):0)],['leg-right',-swing*gait+(held?2*Math.sin(o.t*11+6.6):0)]]){const [x,y]=parts.get(id).pivot;nodes.get(id).setAttribute('transform',`rotate(${angle} ${x} ${y}) ${registered(id)}`)}
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
