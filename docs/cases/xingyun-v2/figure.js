const SVG = 'http://www.w3.org/2000/svg';
const XHTML = 'http://www.w3.org/1999/xhtml';
const TAU = Math.PI * 2;
const clamp = (n,lo,hi) => Math.max(lo,Math.min(hi,n));
const bell = n => Math.sin(Math.PI * clamp(n,0,1));
const ease = (rate,dt) => 1-Math.exp(-rate*dt);
const smooth = n => { const k = clamp(n,0,1); return k*k*(3-2*k); };
const held = k => smooth(k/.18)*smooth((1-k)/.22);
const f1 = n => Math.round(n*100)/100;

// Coopanion's shipped whale figure: reuse its marks, paths and timing.
// The caller supplies Xingyun's head anchor in the whale's effect space.
export function officialFaceEffects(fc,t,at,ac,sweatScale=1.4) {
  let s = '';
  const top = at(124,34), side = at(204,52);
  if (fc.orbit) {
    for (let i = 0; i < 3; i++) {
      const a = t * 3.2 + i * 2.094, sn = Math.sin(a);
      s += `<path fill="#ffd23f" stroke="#3a2f7a" stroke-width="1.6" stroke-linejoin="round" opacity="${sn < 0 ? .55 : 1}" transform="translate(${f1(top[0] + 56 * Math.cos(a))} ${f1(top[1] - 4 + 10 * sn)}) scale(${sn < 0 ? .7 : 1})" d="M0 -7L2 -2L7 -2L3 1L4.5 6.5L0 3.3L-4.5 6.5L-3 1L-7 -2L-2 -2Z"/>`;
    }
  }
  if (fc.listen) {
    for (let i = 0; i < 3; i++) {
      const p = (t * .9 + i / 3) % 1, r = 36 - 24 * p, c = at(214, 116);
      s += `<path fill="none" stroke="${ac}" stroke-width="5" stroke-linecap="round" opacity="${f1(Math.sin(Math.PI * p))}" d="M${f1(c[0] + r * Math.cos(-.55))} ${f1(c[1] + r * Math.sin(-.55))}A${f1(r)} ${f1(r)} 0 0 1 ${f1(c[0] + r * Math.cos(.55))} ${f1(c[1] + r * Math.sin(.55))}"/>`;
    }
  }
  if (fc.think) {
    for (let i = 0; i < 3; i++) {
      const k = (t * .8 + i / 3) % 1;
      s += `<circle fill="#e8f0ff" stroke="${ac}" stroke-width="3" cx="${f1(side[0] + 10 * i)}" cy="${f1(side[1] - 20 * i - 6 * k)}" r="${4 + 3 * i}" opacity="${f1(.4 + .6 * Math.sin(Math.PI * k))}"/>`;
    }
  }
  if (fc.sweat) {
    const c = at(196, 88 + 3 * Math.sin(t * 7));
    s += `<path fill="#8fd0ff" stroke="#2f5fae" stroke-width="1.4" transform="translate(${f1(c[0])} ${f1(c[1])}) scale(${sweatScale})" d="M0 -9C4 -3 6 0 6 3.5A6 6 0 0 1 -6 3.5C-6 0 -4 -3 0 -9Z"/>`;
  }
  if (fc.anger) {
    const c = at(190, 62), k = 1 + .12 * Math.sin(t * 10);
    s += `<g transform="translate(${f1(c[0])} ${f1(c[1])}) scale(${f1(k)})" fill="none" stroke="#e5484d" stroke-width="5" stroke-linecap="round"><path d="M-11 -3Q-3 -3 -3 -11M3 -11Q3 -3 11 -3M11 3Q3 3 3 11M-3 11Q-3 3 -11 3"/></g>`;
  }
  if (fc.bang) {
    const c = at(206, 36);
    s += `<g transform="translate(${f1(c[0])} ${f1(c[1])})"><path fill="none" stroke="#252049" stroke-width="8" stroke-linecap="round" d="M0 -16V3"/><circle fill="#252049" cx="0" cy="14" r="4.5"/></g>`;
  }
  if (fc.question) {
    const c = at(206, 36), k = 1 + .06 * Math.sin(t * 3);
    s += `<g transform="translate(${f1(c[0])} ${f1(c[1])}) scale(${f1(k)})"><path fill="none" stroke="#252049" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" d="M-8 -9Q-8 -19 0 -19Q9 -19 9 -11Q9 -4 0 -1V4"/><circle fill="#252049" cx="0" cy="14" r="4.5"/></g>`;
  }
  return s;
}

const EXPRESSIONS = {
  happy: {eyes:[1,1],mouth:'happyFace'},
  love: {eyes:[.16,.16],mouth:'smile',roll:-1.4},
  wink: {eyes:[0,0],mouth:'shy'},
  shy: {eyes:[.34,.43],mouth:'shy',roll:-2.2,glance:.42},
  surprised: {mouth:'surprisedFace',roll:-1.4},
  angry: {mouth:'angryFace',roll:1.5},
  sad: {mouth:'sadFace',glance:.62},
  sleepy: {eyes:[.61,.61],mouth:'yawn'},
  thinking: {eyes:[.18,.32],mouth:'hmm',glance:-.46,roll:2},
  smug: {eyes:[.43,.28],mouth:'shy',roll:-2},
  pout: {eyes:[.16,.27],mouth:'pout',glance:.2,roll:1.4},
  worried: {eyes:[.15,.24],mouth:'worry',glance:.23},
  determined: {eyes:[.21,.16],mouth:'firm',roll:.9},
  flustered: {eyes:[.87,.78],mouth:'worry',roll:-1.5},
  scared: {mouth:'worry',open:.38,glance:.12},
  excited: {mouth:'smile',open:.48,roll:-1.1},
  cry: {eyes:[.94,1],mouth:'worry'},
  confused: {eyes:[.11,.44],mouth:'hmm',roll:3,glance:-.18},
  dizzy: {eyes:[.44,.60],mouth:'hmm'},
  sleep: {eyes:[1,1]},
  content: {eyes:[.22,.22],mouth:'shy'},
  waking: {eyes:[.64,.64],mouth:'yawn'},
  listening: {open:.25,glance:-.16,roll:-9.5},
  dragged: {mouth:'neutralFace'},
  bowing: {eyes:[.87,.87]},
};
// Values are in original canvas pixels: lift, height difference at the
// inner end, arch, and shift towards the nose. The far brow is foreshortened.
const BROWS = {
  happy:[6,0,3,0], love:[7,3,4,0], wink:[4,1,3,0], shy:[-1,14,-3,2],
  surprised:[14,3,8,0], angry:[-8,-36,-5,3], sad:[-3,24,-9,3],
  sleepy:[-8,1,-4,0], sleep:[-6,4,-4,0], thinking:[0,-12,-1,2],
  smug:[-4,-13,2,2], pout:[-3,-18,-4,3], worried:[-3,21,-7,3],
  determined:[-5,-23,-4,2], flustered:[3,16,-5,2], scared:[8,17,-4,1],
  excited:[11,4,6,0], cry:[-3,26,-8,3], confused:[5,-8,6,2],
  dizzy:[1,9,-3,1], dragged:[-2,15,-5,2], listening:[6,2,3,0],
};
const BROW_RATE={surprised:17,scared:17,excited:14,angry:15,sad:5,cry:5,worried:6,sleepy:4,sleep:4};

export function viewAngles(frame, controls={}) {
  const phase = frame.gesture?.k ?? 0;
  const envelope = bell(phase) ** 2;
  const nod = frame.gesture?.kind === 'nod' ? Math.sin(TAU*phase)**2 * held(phase) : 0;
  const shake = frame.gesture?.kind === 'shake' ? Math.sin(TAU*phase*2) * envelope : 0;
  const bow = frame.gesture?.kind === 'bow' ? held(phase) : 0;
  const dance = frame.mode==='dance' ? Math.sin((frame.modeT??0)*TAU*1.08) : 0;
  const mood = EXPRESSIONS[frame.face] ?? {};
  const look = frame.look ?? [0,0];
  const listening = frame.face==='listening';
  return {
    yaw: clamp(controls.yaw ?? (look[0]/5 + shake*1.15),-1.25,1.25),
    pitch: clamp(controls.pitch ?? (look[1]/5 + nod*1.18 + bow*.98
      + (frame.mode==='sleep' ? .35 : 0)+(listening?.2:0)),-1.25,1.25),
    roll: clamp(controls.roll ?? (nod*4 + shake*3.7 + bow*4.2 + dance*2.2
      + look[0]*.28+(mood.roll??0)),-12,12),
  };
}

// Use the same affine displacement for each head layer. Separate mesh grids
// interpolate affine functions identically, so shared painted edges stay put.
export function headDisplacement(u,v,yaw,pitch) {
  const x=u-(644-260)/700;
  const y=(669-40)/860-v;
  return [yaw*8.1*y-Math.abs(yaw)*4.6*x,
    pitch*(8.2*y+2*x)-Math.abs(pitch)*1.4*y];
}

// The ear tips flex inside the shared hair mesh. The diagonal base of each
// ear follows the scalp so its root stays attached to the head.
function earWarp(x,y,angle,far) {
  const [px,py]=far?[799,232]:[438,252];
  const base=far?209+(x-710)*.47:261-(x-374)*.25;
  const sides=far?smooth((x-684)/36)*smooth((890-x)/36)
    :smooth((x-324)/37)*smooth((568-x)/45);
  const a=angle*RAD*sides*smooth((base-y)/87);
  const c=Math.cos(a), s=Math.sin(a), dx=x-px, dy=y-py;
  return [dx*c-dy*s-dx,dx*s+dy*c-dy];
}

function spring(state,target,dt,frequency,damping) {
  // The closed-form damped spring also handles dropped display frames.
  const decay=frequency*damping;
  const oscillation=frequency*Math.sqrt(1-damping*damping);
  const offset=state.value-target;
  const c=Math.cos(oscillation*dt), s=Math.sin(oscillation*dt);
  const e=Math.exp(-decay*dt);
  const phase=(state.speed+decay*offset)/oscillation;
  const residual=offset*c+phase*s;
  state.value=target+e*residual;
  state.speed=e*(oscillation*(-offset*s+phase*c)-decay*residual);
  return state.value;
}

// Xingmian's drag uses these spring coefficients and semi-implicit step.
function xingmianSpring(k,c,limit) {
  let x=0, v=0;
  return (target,dt)=>{
    if(!Number.isFinite(target)||!Number.isFinite(dt)) return x;
    v+=((target-x)*k-v*c)*dt;
    x+=v*dt;
    if(Math.abs(x)>limit){ x=Math.sign(x)*limit; v=0; }
    return x;
  };
}

function heldLeg([px,py],angle,lift) {
  const a=angle*Math.PI/180, c=Math.cos(a), s=Math.sin(a);
  return (_u,_v,x,y)=>{
    const w=smooth((y-py+6)/20), dx=x-px, dy=y-py;
    return [(dx*c-dy*s-dx)*w,(dx*s+dy*c-dy-lift)*w];
  };
}

// Palm centers from the standing arm registration, in the master canvas.
const PALM_CENTERS={leftArm:[465.7,904.5],rightArm:[827,898.5]};
const RAD=Math.PI/180;
function palmArc([dx,dy],pivotY,direction) {
  const bias=Math.atan2(dx,dy), radius=Math.hypot(dx,dy);
  return {
    height:angle=>pivotY+radius*Math.cos(angle*RAD-bias),
    angle:height=>(bias+direction*Math.acos(clamp((height-pivotY)/radius,-1,1)))/RAD,
  };
}

const RUN_CONTACT=.38;
function runningStep(p) {
  if(p<RUN_CONTACT) return {angle:-14+25*p/RUN_CONTACT,lift:0};
  const recovery=(p-RUN_CONTACT)/(1-RUN_CONTACT);
  const lift=bell(recovery);
  return {angle:11-25*smooth(recovery)+9*lift,
    lift:7.6*lift*(.68+.32*recovery)};
}

// Wag amplitudes and spring terms from Coopanion's shipped whale figure.
const WHALE_WAG={
  happy:1,love:1,wink:.7,surprised:.2,angry:.15,sad:0,shy:.3,
  sleepy:0,sleep:0,dizzy:0,dragged:.6,content:.25,listening:.2,
  thinking:.15,run:.4,waking:0,squeeze:0,neutral:.25,smug:.6,pout:0,
  worried:.1,determined:.3,flustered:.8,scared:0,excited:1,cry:0,confused:.1,bowing:.2,
};
const TAIL_DROOP=new Set(['sad','cry','scared']);
const TAIL_WAG_SECONDS=2.6;

function whaleTailMotion() {
  const inertia=xingmianSpring(40,5,32);
  let amplitude=0, droop=0, phase=0;
  return (frame,dt,seated,flap)=>{
    const gesture=frame.gesture;
    const requested=gesture?.kind==='wag' ? held(gesture.k) : 0;
    const wag=Math.max(WHALE_WAG[frame.face]??WHALE_WAG.neutral,requested);
    const t=frame.t??0;
    amplitude+=(wag-amplitude)*ease(3,dt);
    droop+=((frame.mode==='sleep'||TAIL_DROOP.has(frame.face)?-1:0)-droop)*ease(3,dt);
    // Integrating the frequency keeps the tail continuous when mood changes.
    phase=(phase+dt*(4+5*amplitude)*.85)%TAU;
    const sway=clamp((frame.swing??0)/26,-1.6,1.6);
    const turn=inertia(sway*14+droop*12,dt)+amplitude*13*Math.sin(phase)
      +Math.sin(t*1.3)*3+flap*14*Math.sin(t*17);
    return seated?0:turn*.78;
  };
}

function tailDisplacement(x,y,[pivotX,pivotY],unit,angle) {
  // Mirror the whale's tip bend onto this left-pointing tail and feather
  // the rotation next to the root tucked into Xingyun's cape.
  const length=Math.max(0,pivotX-x)/unit;
  const tip=clamp(length/185,0,1);
  const radians=angle*smooth(length/42)*RAD;
  const c=Math.cos(radians), s=Math.sin(radians);
  const dx=x-pivotX, dy=y-pivotY;
  const bent=dy-angle*.5*tip*tip;
  return [dx*c-bent*s-dx,dx*s+bent*c-dy];
}

export async function createXingyunBody(base, opts) {
  const {kit,model,host} = opts;
  if (!kit.createRig || !model) throw new Error('Xingyun needs Coopanion’s mesh rig.');
  const controls = opts.controls ?? {};
  const asset = path => opts.asset ? opts.asset(path) : new URL(path,base);
  const imageLoad = opts.loadImage ?? (url => new Promise((resolve,reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error('Unable to load ' + url));
    image.src = url;
  }));
  const images = new Map(await Promise.all(Object.entries(model.textures).map(async([id,path]) =>
    [id,await imageLoad(asset(path))])));
  const [x0,y0,x1,y1] = model.view;
  const [gx,gy] = model.ground;
  const unit = model.unit;
  const X = x => 128+(x-gx)*unit;
  const Y = y => 256+(y-gy)*unit;
  const palms=Object.fromEntries(Object.entries(PALM_CENTERS).map(([key,[x,y]])=>{
    const [px,py]=model.deformers[key].pivot;
    return [key,palmArc([X(x)-px,Y(y)-py],py,key==='leftArm'?1:-1)];
  }));
  const springs=new Map(['lockLeft','lockRight','ahoge']
    .map(key=>[key,{value:0,speed:0}]));
  const carried={
    head:xingmianSpring(70,10,16), hair:xingmianSpring(55,7,1.8),
    hairY:xingmianSpring(50,8,1.2),
    ahoge:xingmianSpring(140,6,38), near:xingmianSpring(60,9,125), far:xingmianSpring(60,9,95),
  };
  const nearEar=xingmianSpring(92,12,9);
  const farEar=xingmianSpring(74,10,9);
  let runWeight=0, runPhase=0, carryStretch=0, headVelocity=0;
  let groupCarry=0, armRelease=0, lastCarryHead=0, lastCarryYaw=0, lastCarryLow=0;
  const footTips={leftLeg:[X(575),Y(1181)],rightLeg:[X(711),Y(1176)]};
  const stepTail=whaleTailMotion();
  const tailPivot=[X(513),Y(985)];
  let eyeOpen=0, moodGlance=0, mouthIndex=null, mouthBlend=1, mouthTile, mouthOld;
  let eyePose='neutral', requestedEye='neutral', eyeTransition=1;
  const browPose={browLeft:[0,0,0,0],browRight:[0,0,0,0]};
  let rig, element, artCanvas, fxGroup, fxMarkup='', mounted, previousTime, wink=0, rest=0;
  let yaw=0, pitch=0, roll=0;
  const eyePatch = {};
  const nearArm=model.parts.find(part=>part.id==='leftArm').sourceBox;
  const shoulder=model.parts.find(part=>part.id==='shoulderCover').sourceBox;
  const [ax,ay,aw,ah]=nearArm;
  const [px,py]=model.deformers.leftArm.pivot;
  const armPivot=[gx+(px-128)/unit-ax,gy+(py-256)/unit-ay];
  let armTile, armPen, lastArmAngle;

  function mount(group) {
    rig?.dispose();
    element?.remove();
    fxGroup?.remove();
    const doc = group.ownerDocument;
    element = doc.createElementNS(SVG,'foreignObject');
    for (const [name,value] of Object.entries({x:x0,y:y0,width:x1-x0,height:y1-y0})) {
      element.setAttribute(name,value);
    }
    element.setAttribute('pointer-events','none');
    element.dataset.figure='xingyun-v2';
    artCanvas = doc.createElementNS(XHTML,'canvas');
    artCanvas.width=Math.ceil((x1-x0)*4);
    artCanvas.height=Math.ceil((y1-y0)*4);
    artCanvas.style.cssText='width:100%;height:100%;display:block;';
    element.appendChild(artCanvas);
    group.prepend(element);
    fxGroup=doc.createElementNS(SVG,'g');
    fxGroup.setAttribute('pointer-events','none');
    fxGroup.setAttribute('aria-hidden','true');
    fxGroup.dataset.faceFx='xingyun-v2';
    group.appendChild(fxGroup);
    fxMarkup='';
    rig = kit.createRig(artCanvas,model);
    for(const [key,image] of images) {
      if (!model.eyeAtlases[key] && !['shoulderCover','leftArm','mouthExpression'].includes(key)) rig.upload(key,image);
    }
    armTile=doc.createElement('canvas');
    armTile.width=aw;
    armTile.height=ah;
    armPen=armTile.getContext('2d');
    lastArmAngle=undefined;
    for(const [key,sheet] of Object.entries(model.eyeAtlases)) {
      const tile=doc.createElement('canvas');
      tile.width=sheet.width;
      tile.height=sheet.height;
      eyePatch[key]={tile,context:tile.getContext('2d'),index:-1,pose:-1};
      paintEye(key,0);
    }
    if (model.mouthAtlas) {
      const {width,height}=model.mouthAtlas;
      mouthTile=doc.createElement('canvas');
      mouthOld=doc.createElement('canvas');
      mouthTile.width=mouthOld.width=width;
      mouthTile.height=mouthOld.height=height;
      rig.upload('mouthExpression',mouthTile);
      mouthIndex=null;
      mouthBlend=1;
    }
    mounted=group;
  }

  function paintNearArm(angle) {
    if (angle===lastArmAngle) return;
    lastArmAngle=angle;
    const [x,y]=armPivot;
    armPen.clearRect(0,0,aw,ah);
    armPen.save();
    armPen.translate(x,y);
    armPen.rotate(angle*Math.PI/180);
    armPen.drawImage(images.get('leftArm'),-x,-y);
    armPen.restore();
    armPen.save();
    armPen.globalCompositeOperation='destination-out';
    armPen.drawImage(images.get('shoulderCover'),shoulder[0]-ax,shoulder[1]-ay);
    armPen.restore();
    rig.upload('leftArm',armTile);
  }

  function paintEye(key, amount) {
    const sheet=model.eyeAtlases[key];
    const target=eyePatch[key];
    const index=sheet.fixed?.includes(eyePose)?0:Math.round(clamp(amount,0,1)*(sheet.count-1));
    const pose=sheet.poses?.[eyePose]??0;
    if(index===target.index && pose===target.pose) return;
    const {width,height,columns}=sheet;
    target.context.clearRect(0,0,width,height);
    const image=images.get(key);
    const row=pose*Math.ceil(sheet.count/columns)+Math.floor(index/columns);
    target.context.drawImage(image,(index%columns)*width,row*height,
      width,height,0,0,width,height);
    rig.upload(key,target.tile);
    target.index=index;
    target.pose=pose;
  }

  function paintMouth(name,dt) {
    if (!model.mouthAtlas || (name===mouthIndex && mouthBlend===1)) return;
    const {width,height,columns,frames}=model.mouthAtlas;
    const ctx=mouthTile.getContext('2d');
    if (name!==mouthIndex) {
      const previous=mouthOld.getContext('2d');
      previous.clearRect(0,0,width,height);
      previous.drawImage(mouthTile,0,0);
      mouthIndex=name;
      mouthBlend=0;
    }
    mouthBlend=Math.min(1,mouthBlend+dt*8);
    const k=smooth(mouthBlend);
    ctx.clearRect(0,0,width,height);
    ctx.save();
    ctx.globalAlpha=1-k;
    ctx.drawImage(mouthOld,0,0);
    if (Object.hasOwn(frames,name)) {
      const i=frames[name];
      ctx.globalAlpha=k;
      ctx.globalCompositeOperation='lighter';
      ctx.drawImage(images.get('mouthExpression'),i%columns*width,Math.floor(i/columns)*height,
        width,height,0,0,width,height);
    }
    ctx.restore();
    rig.upload('mouthExpression',mouthTile);
  }

  function state(frame,dt,leftClose,rightClose) {
    const t=frame.t ?? 0;
    const angles=viewAngles(frame,controls);
    const follow=ease(frame.face==='listening'?8:12,dt);
    const previousRoll=roll;
    yaw+=(angles.yaw-yaw)*follow;
    pitch+=(angles.pitch-pitch)*follow;
    roll+=(angles.roll-roll)*follow;
    const rollVelocity=dt>0?(roll-previousRoll)/dt:0;
    headVelocity+=(rollVelocity-headVelocity)*ease(12,dt);
    const walking=frame.mode==='walk';
    const running=frame.mode==='run';
    const grabbed=frame.mode==='drag';
    const air=frame.mode==='air';
    const swing=clamp((frame.swing??0)/28,-1,1);
    carryStretch+=(Number(grabbed)-carryStretch)*ease(8,dt);
    const inputSwing=frame.swing??0;
    const sway=clamp(inputSwing/26,-1.6,1.6);
    const carryHead=carried.head((frame.look?.[0]??0)*.7+Math.sin(t*.9)*1.2
      +(frame.look?.[1]??0)*.4+(grabbed?inputSwing*.25:0),dt);
    const carryTurn=clamp((frame.look?.[0]??0)/5,-1,1)*.9;
    const carryLow=(frame.low??0)-29*(frame.sit??0);
    const carryHeadSpeed=(carryHead-lastCarryHead)/Math.max(dt,.001);
    const carryYawSpeed=(carryTurn-lastCarryYaw)/Math.max(dt,.001);
    const carryLowSpeed=(carryLow-lastCarryLow)/Math.max(dt,.001);
    lastCarryHead=carryHead;
    lastCarryYaw=carryTurn;
    lastCarryLow=carryLow;
    const carryHair=carried.hair(sway*1.1-carryHeadSpeed*.004-carryYawSpeed*.02,dt);
    const carryHairY=carried.hairY(-(air||grabbed)+carryLowSpeed*.006,dt);
    const carryAhoge=carried.ahoge(-carryHeadSpeed*.12-carryYawSpeed*.5+sway*18-carryHairY*12,dt);
    const oldGroupCarry=groupCarry;
    const carryInAir=groupCarry>.01&&(air||frame.mode==='land');
    groupCarry+=(Number(grabbed||carryInAir)-groupCarry)*ease(10,dt);
    if(running && runWeight<.025) runPhase=0;
    runWeight+=(Number(running)-runWeight)*ease(running?7:12,dt);
    if(runWeight>.015) runPhase=(runPhase+dt*(1.8+.85*runWeight))%1;
    const runLean=10.2*runWeight;
    const nearStep=runningStep(runPhase);
    const farStep=runningStep((runPhase+.5)%1);
    const flight=smooth(((runPhase%.5)-RUN_CONTACT)/(.5-RUN_CONTACT));
    const cycle=(frame.modeT ?? t)*TAU*1.48;
    const amplitude=walking?smooth((frame.modeT??1)/.28):0;
    const stride=Math.sin(cycle)*amplitude;
    const bounce=Math.abs(Math.cos(cycle))*.68*amplitude;
    const gesture=frame.gesture?.kind;
    const phase=frame.gesture?.k??0;
    const wave=gesture==='wave'?held(phase):0;
    const bow=gesture==='bow'?held(phase):0;
    const shiver=gesture==='shiver'?held(phase)*Math.sin(t*32):0;
    const flap=gesture==='flap'?held(phase)*(.65+.35*Math.sin(phase*TAU*3)):0;
    const dance=frame.mode==='dance'?Math.sin((frame.modeT??0)*TAU*1.08):0;
    // The seated painting includes both bent legs. Switch the whole body in one
    // frame and keep the seat through the kit's seated portion of waking up.
    const seated=model.seatDepth!==undefined && (frame.mode==='sit'||frame.mode==='sleep'
      ||(frame.mode==='wake'&&(frame.modeT??0)<1.1&&(frame.sit??0)>.5));
    const rootY=seated?model.seatDepth:bounce+bow*1.6-Math.abs(dance)-3.4*bell(flight)*runWeight;
    const idle=Math.sin(t*1.9)*.36;
    const st={alpha:{}};
    // Balance the host's drag stretch about the scruff so the drawing keeps
    // its proportions even when it dangles below the pointer.
    const [bx,by]=model.deformers.body.pivot;
    const sx=1/(1-.05*carryStretch), sy=1/(1+.09*carryStretch);
    const carryBreath=Math.sin(t*2.4);
    st.body=seated?{ty:rootY}:{a:grabbed?-sway*1.2+inputSwing*.15:runLean,
      tx:(sx-1)*(bx-128),ty:rootY+(sy-1)*(by-36),
      sx:sx*(1+(grabbed?.006*carryBreath:idle*.009)),
      sy:sy*(1-(grabbed?.012*carryBreath:idle*.009))};
    if (model.seatDepth!==undefined) {
      st.alpha.sitBody=Number(seated);
      st.alpha.sitCapeRear=Number(seated);
      if (seated) {
        for (const key of ['body','capeRear','skirtLining','leftLeg','rightLeg','leftArm','rightArm']) st.alpha[key]=0;
      }
    }
    if (!seated) {
      const kick=10*Math.sin(t*11);
      for (const [key,step] of [['leftLeg',1],['rightLeg',-1]]) {
        if(grabbed){
          st[key]={a:0,ty:0};
          st[key+'Held']={fn:heldLeg(model.deformers[key].pivot,-step*kick,.3*Math.abs(kick))};
          continue;
        }
        const run=step>0?nearStep:farStep;
        st[key]={
          a:-step*stride*6.3+(air?step*Math.sin(t*14)*4:0)+dance*step*6
            +(run.angle-runLean)*runWeight,
          ty:-Math.max(0,step*Math.cos(cycle))*1.2*amplitude-Math.max(0,dance*step)*1.6,
        };
        if(runWeight>.015){
          const [,footY]=rig.point(key,st,...footTips[key]);
          const targetY=256-run.lift-2.6*bell(flight);
          st[key].ty+=clamp((targetY-footY)/Math.cos(runLean*Math.PI/180),-11,4)*runWeight;
        }
      }
    }
    const near=(walking?stride*6.8:air?4+Math.sin(t*12)*4:idle)+flap*11+shiver*1.3-dance*13;
    const far=(walking?-stride*6.1:air?-4-Math.sin(t*12)*4:-idle)
      +wave*(-61+10*Math.sin(phase*TAU*2.5))-flap*35-shiver*1.3-dance*12;
    const heldHeight=Y(863-14*Math.sin(t*13));
    let nearArm=carried.near(grabbed?palms.leftArm.angle(heldHeight):running?16:near,dt);
    let farArm=carried.far(grabbed?palms.rightArm.angle(heldHeight):running?14:far,dt);
    if(grabbed){
      const height=(palms.leftArm.height(nearArm)+palms.rightArm.height(farArm))*.5;
      nearArm=palms.leftArm.angle(height);
      farArm=palms.rightArm.angle(height);
    }
    armRelease=grabbed||running?1:armRelease*(1-ease(10,dt));
    st.leftArm={a:near+(nearArm-near)*armRelease};
    st.rightArm={a:far+(farArm-far)*armRelease};
    st.staff={a:stride*.8+idle*1.1+runWeight*2.1};
    const carriedBend=((frame.tilt??0)+(frame.lean??0)*Math.sign(frame.facing||1))*(1-oldGroupCarry);
    st.neck=grabbed?{a:carryHead+clamp(carriedBend*.8,-10,12),ty:carryBreath*.35}
      :{a:roll-runLean*.7,ty:pitch*.42+bow*2.1};
    const perk=frame.face==='happy'||frame.face==='love'||frame.face==='excited';
    const listen=frame.face==='listening';
    const lowered=frame.mode==='sleep'||frame.face==='sad';
    const earBounce=grabbed?inputSwing*.2+2.8*Math.sin(t*11)
      :runWeight*2.8*Math.sin(runPhase*TAU)+stride*.8;
    const flick=bell(clamp(((t+4)%7.8-7.3)/.5,0,1))*3.8;
    const leftEar=nearEar((perk?-5.5:listen?4.8:lowered?6:0)
      +earBounce+flick+.58*Math.sin(t*1.7),dt);
    const rightEar=farEar((perk?4.8:listen?-.8:lowered?-5.5:0)
      +earBounce*.82-flick*.28+.48*Math.sin(t*1.7-.6),dt);
    st.head={fn:(u,v,x,y)=>{
      const [dx,dy]=headDisplacement(u,v,yaw,pitch);
      const nativeX=gx+(x-128)/unit, nativeY=gy+(y-256)/unit;
      if(nativeY>=272) return [dx,dy];
      const [ex,ey]=earWarp(nativeX,nativeY,nativeX<630?leftEar:rightEar,nativeX>=630);
      const fade=smooth((272-nativeY)/25);
      return [dx+ex*unit*fade,dy+ey*unit*fade];
    }};
    // Keep the lid perimeter fixed. The near iris can travel further
    // than the far one; neither eye tracks through a closing lid.
    const glance=(u,v)=>bell(u)**2*bell(v)**2;
    const aim=frame.look??[0,0];
    const lookX=clamp(aim[0]/5,-1,1),lookY=clamp(aim[1]/5,-1,1);
    if(eyePose==='neutral') {
      st.eyeLeftGlance={fn:(u,v)=>[lookX*.90*glance(u,v)*(1-leftClose),
        (lookY*.72+moodGlance+eyeOpen*(v-.5)*4)*glance(u,v)*(1-leftClose)]};
      st.eyeRightGlance={fn:(u,v)=>[lookX*.55*glance(u,v)*(1-rightClose),
        (lookY*.60+moodGlance+eyeOpen*(v-.5)*3)*glance(u,v)*(1-rightClose)]};
    }
    const browTarget=BROWS[frame.face]??[0,0,0,0];
    for(const [key,def] of Object.entries(model.brows??{})){
      const near=def.innerRight;
      const next=[...browTarget];
      if (!near) {
        next[0]*=.92;
        next[1]*=.58;
        next[2]*=.68;
        next[3]*=.64;
      }
      if(frame.face==='wink') next[0]+=near?5:-4;
      if(frame.face==='confused') next[0]+=near?-5:6;
      const pose=browPose[key];
      const settle=ease(BROW_RATE[frame.face]??9,dt);
      for(let i=0;i<4;i++) pose[i]+=(next[i]-pose[i])*settle;
      const [lift,innerRise,arch,slide]=pose;
      st[key]={fn:u=>[unit*slide*(near?1:-1),
        -unit*(lift+((near?u:1-u)-.5)*innerRise+bell(u)**2*arch)]};
    }
    const target=swing*3+yaw*1.4+stride*1.8-headVelocity*.047-runWeight*2;
    for(const [key,phase] of [['lockLeft',0],['lockRight',.57]]) {
      const current=spring(springs.get(key),target+Math.sin(t*2.25+phase)*.7,
        dt,key==='lockLeft'?10.5:8.5,.63);
      if(grabbed){
        const [nx,ny]=model.deformers.neck.pivot;
        st[key]={fn:(_u,v,x,y)=>{
          const a=-carryHead*Math.PI/180*smooth((v-.3)/.5), c=Math.cos(a), s=Math.sin(a);
          const dx=x-nx, dy=y-ny, w=v**1.6;
          return [dx*c-dy*s-dx+(carryHair*8+Math.sin(t*1.6+v*3))*w,
            dx*s+dy*c-dy+carryHairY*12*w*w-Math.abs(carryHair)*1.5*w];
        }};
        continue;
      }
      st[key]={fn:(_u,v)=>{
        const free=clamp((v-.45)/.55,0,1)**2;
        return [current*free,-Math.abs(current)*free*.27];
      }};
    }
    const tailAngle=stepTail(frame,dt,seated,flap);
    st.tail={fn:(_u,_v,x,y)=>tailDisplacement(x,y,tailPivot,unit,tailAngle)};
    const idleAhoge=clamp(spring(springs.get('ahoge'),-headVelocity*.075,dt,15,.63)
      +Math.sin(t*1.38)*1.7-yaw*2.2+stride*1.2+flap*3+shiver*.35+tailAngle*.32,-8,8);
    st.ahoge={a:grabbed?carryAhoge*.5+Math.sin(t*2.1)*2:idleAhoge};
    return st;
  }

  function draw(group,face,frame) {
    if (controls.previewFace && frame.mode!=='drag' && frame.face!=='listening') {
      frame={...frame,face:controls.previewFace};
    }
    if(mounted!==group || !element?.isConnected) mount(group);
    const time=frame.t??0;
    const dt=previousTime===undefined?1/60:clamp(time-previousTime,0,.05);
    previousTime=time;
    const authored=model.eyeAtlases.eyeLeft.poses??{};
    const winking=frame.face==='wink'&&!Object.hasOwn(authored,'wink');
    wink+=(Number(winking)-wink)*ease(winking?42:25,dt);
    const closing=controls.closedEyes&&frame.mode!=='drag';
    rest+=(Number(frame.mode==='sleep'||Boolean(closing))-rest)*ease(31,dt);
    const mood=EXPRESSIONS[frame.face]??{};
    const transition=ease(12,dt);
    eyeOpen+=((mood.open??0)-eyeOpen)*transition;
    moodGlance+=((mood.glance??0)-moodGlance)*transition;
    const desired=Object.hasOwn(authored,frame.face)&&!closing?frame.face:'neutral';
    if(desired!==requestedEye){
      requestedEye=desired;
      eyeTransition=0;
    }
    eyeTransition=Math.min(1,eyeTransition+dt/.19);
    if(eyeTransition>=.5) eyePose=requestedEye;
    const inspect=controls.previewFace&&desired!=='neutral';
    const automatic=inspect?0:Math.max(frame.blink??0,winking?0:frame.eyeClose??0);
    const auto=Math.max(automatic,smooth(rest),bell(eyeTransition));
    const leftClose=auto;
    paintEye('eyeLeft',leftClose);
    const rightClose=Math.max(auto,smooth(wink));
    paintEye('eyeRight',rightClose);
    const speech=frame.mode==='drag'?0:clamp((frame.talk??0)*1.5,0,1);
    const paintedMouth=frame.face+'Face';
    paintMouth(Object.hasOwn(model.mouthAtlas?.frames??{},paintedMouth)
      ? paintedMouth : mood.mouth??'neutralFace',dt);
    const pose=state(frame,dt,leftClose,rightClose);
    pose.alpha.mouthTalk=speech;
    pose.alpha.mouthExpression=mouthTile?1-speech:0;
    if(pose.alpha.leftArm!==0) paintNearArm(pose.leftArm.a);
    rig.render(pose);
    const markers=(controls.previewFace===frame.face?kit.FACES?.[frame.face]?.f(time):face)??{};
    const anchor=(x,y)=>rig.point('head',pose,X(645)+(x-124)*.76,Y(81)+(y-34));
    const markup=officialFaceEffects(markers,time,anchor,'#81b8a0',frame.mode==='drag'?1:1.4);
    if(markup!==fxMarkup) {
      fxGroup.innerHTML=markup;
      fxMarkup=markup;
    }
  }

  const figure={
    draw,
    dispose(){ rig?.dispose(); element?.remove(); fxGroup?.remove(); mounted=undefined; },
    gestures:['nod','shake','wave','bow','shiver','flap','wag'],
    groupTilt(mode,tilt,lean) {
      if(mode==='drag'||groupCarry>.01) return (tilt+lean)*groupCarry;
      if(mode==='air'||mode==='land'||mode==='dance'||mode==='dizzy') return clamp(tilt+lean*.5,-9,9);
      return 0;
    },
    anchors:{gaze:[X(718),Y(557)],bubble:[X(640),Y(69)],z:[X(826),Y(106)],
      hearts:[X(557),X(771),Y(195)]},
    extent:[X(226),Y(58),X(947),Y(1184)],
    hits:[[X(631),Y(379),58],[X(640),Y(814),34],[X(647),Y(1062),28]],
    colors:{z:'#81b8a0'},
  };
  return kit.createBody(host,{figure,words:{wag:{motion:{seconds:TAIL_WAG_SECONDS}}}});
}
