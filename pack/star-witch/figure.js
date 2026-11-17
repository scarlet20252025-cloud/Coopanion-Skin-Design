import { officialFaceEffects } from './effects.js';

const SVG = 'http://www.w3.org/2000/svg';
const TAU = Math.PI * 2;
const clamp = (v,a,b) => Math.max(a,Math.min(b,v));
const smooth = t => { const k=clamp(t,0,1); return k*k*(3-2*k); };
const approach = (value,target,dt,rate=12) => value+(target-value)*(1-Math.exp(-dt*rate));
const WALK_CYCLE = 120;
const WALK_CADENCE_CAP = 1.75;
const STANCE = .60;
// Lower sole points sampled from the standing parts in master coordinates,
// far leg first to match the drawing order.
const SOLES = [
  [[647,1302],[657,1304],[668,1305],[680,1305],[690,1304],[700,1302]],
  [[543,1309],[552,1311],[559,1312],[580,1312],[587,1311],[594,1309]],
];

export function solvePose(frame, controls={}, carried=0, walking, listening) {
  const t=frame.t??0, mode=frame.mode??'idle';
  const walk=mode==='walk', run=mode==='run';
  const look=controls.look??frame.look??[0,0];
  const modeT=frame.modeT??0;
  const runPhase=modeT*TAU*2.18;
  const runRamp=run?smooth(modeT/.27):0;
  const {distance,amount:walkAmount}=walking??{
    distance:modeT*WALK_CYCLE*1.24,amount:walk?smooth(modeT/.3):0,
  };
  const walkPhase=distance/WALK_CYCLE;
  const nod=frame.gesture?.kind==='nod'?Math.sin(Math.PI*frame.gesture.k)**2:0;
  const shake=frame.gesture?.kind==='shake'
    ?Math.sin(TAU*frame.gesture.k*2)*Math.sin(Math.PI*frame.gesture.k):0;
  const bow=frame.gesture?.kind==='bow'
    ?smooth(frame.gesture.k/.26)*smooth((1-frame.gesture.k)/.34):0;
  const bodyY=run?(1+Math.cos(runPhase*2))*2.8*runRamp:
    (1-Math.cos(TAU*(walkPhase-.05)*2))*1.05*walkAmount;
  const listen=listening??+(frame.face==='listening');
  const head=clamp(look[0]*.36+look[1]*.13+nod*3.4+shake*3.65
    +Math.sin(t*1.9)*.55+(frame.swing??0)*carried*.12,-3.3,3.3)-7.2*listen;
  const swing=Math.cos(TAU*(walkPhase-.045))*walkAmount;
  const arms=[
    (run?-2.4*runRamp:3.9*swing)+carried*(-3.8+1.4*Math.sin(t*8)),
    (run?-1.8*runRamp:-3.1*swing)+carried*(3.4-1.4*Math.sin(t*8-.55)),
  ];
  const legs=[0,1].map(i=>{
    const cycle=runPhase+i*Math.PI;
    const kick=Math.sin(t*12+i*Math.PI)*carried;
    const step=(walkPhase+i*.5)%1;
    const flight=clamp((step-STANCE)/(1-STANCE),0,1);
    // During support the shoe travels back at the same rate the pet moves.
    // A separate swing returns it forward and lifts it clear of the floor.
    const travel=WALK_CYCLE*(STANCE/2-step+smooth(flight))*walkAmount;
    const stride=-Math.asin(travel/294)*180/Math.PI;
    const lift=13*Math.sin(Math.PI*flight)**2*walkAmount;
    return {
      angle:stride+Math.sin(cycle)*runRamp*4.6+kick*3.8,
      lift:lift+Math.max(0,Math.cos(cycle))*runRamp*12+Math.max(0,kick)*5,
    };
  });
  const sit=['sit','sleep','dizzy','wake'].includes(mode)&&(frame.sit??0)>.5;
  if (controls.still) return {head:0,yaw:0,pitch:0,bodyY:0,nod:0,bow:0,arms:[0,0],legs:legs.map(()=>({angle:0,lift:0})),sit,walkAmount:0};
  const yaw=clamp(look[0]/12,-1,1);
  const pitch=clamp(look[1]/12,-1,1);
  return {head,yaw,pitch,bodyY,nod,bow,arms,legs,sit,walkAmount};
}

function soleCorrection(points,[x,y],angle,floor) {
  const a=angle*Math.PI/180;
  const lowest=Math.max(...points.map(([px,py])=>y+Math.sin(a)*(px-x)+Math.cos(a)*(py-y)));
  return floor-lowest;
}

function turn(ctx,[x,y],angle,dy=0) {
  ctx.translate(x,y+dy);
  ctx.rotate(angle*Math.PI/180);
  ctx.translate(-x,-y);
}

export async function createStarWitchBody(base, options) {
  const { model, kit, host, asset, controls={} }=options;
  if (!model || model.canvas.join('x')!=='1163x1352') throw new Error('子图与 1163×1352 母版不匹配。');
  const load=options.loadImage??(url=>new Promise((resolve,reject)=>{
    const im=new Image();
    im.onload=()=>resolve(im); im.onerror=()=>reject(new Error('贴图加载失败 '+url)); im.src=url;
  }));
  const parts=Object.fromEntries(await Promise.all(Object.entries(model.parts).map(async ([name,p])=>{
    const image=await load(asset?asset(p.file):new URL(p.file,base));
    const [,,w,h]=p.box;
    const cols=p.columns??1, rows=Math.ceil((p.count??1)/cols);
    if (image.naturalWidth!==w*cols||image.naturalHeight!==h*rows)
      throw new Error('贴图尺寸与模型清单不符 '+name);
    return [name,{ ...p,image }];
  })));
  const joints=model.joints;
  const [vx,vy,vw,vh]=model.view, [gx,gy]=model.ground, unit=model.unitsPerPixel;
  const u=x=>128+(x-gx)*unit, v=y=>256+(y-gy)*unit;
  const px=.83;
  let mount, frameCanvas, context, scratch, pen, fx, fxState='';
  let last=0, wink=0, winkAt=-Infinity, rest=0, carry=0, lock=0, previousFace='neutral';
  let body, listening=0, walked=0, settleAt=0, walkAmount=0, previousX, wasWalking=false;

  function init(group) {
    const doc=group.ownerDocument;
    mount=doc.createElementNS(SVG,'foreignObject');
    for (const [key,value] of Object.entries({x:u(vx),y:v(vy),width:vw*unit,height:vh*unit,
                                             'pointer-events':'none'})) mount.setAttribute(key,value);
    frameCanvas=doc.createElement('canvas');
    frameCanvas.width=Math.ceil(vw*px);frameCanvas.height=Math.ceil(vh*px);
    frameCanvas.style.cssText='display:block;width:100%;height:100%;';
    scratch=doc.createElement('canvas');
    [scratch.width,scratch.height]=[frameCanvas.width,frameCanvas.height];
    context=frameCanvas.getContext('2d');pen=scratch.getContext('2d');
    fx=doc.createElementNS(SVG,'g');
    mount.append(frameCanvas);
    group.prepend(mount);
    group.append(fx);
  }

  function clear(ctx) {
    ctx.setTransform(1,0,0,1,0,0);
    ctx.clearRect(0,0,frameCanvas.width,frameCanvas.height);
    ctx.setTransform(px,0,0,px,-vx*px,-vy*px);
    ctx.imageSmoothingQuality='high';
  }

  function sprite(ctx,name) {
    const { image,box:[x,y] }=parts[name];
    ctx.drawImage(image,x,y);
  }

  function atlas(ctx,name,index) {
    const { image,box:[x,y,w,h],columns,count }=parts[name];
    const i=clamp(index,0,count-1);
    ctx.drawImage(image,(i%columns)*w,Math.floor(i/columns)*h,w,h,x,y,w,h);
  }

  function rotateSprite(name,pivot,angle,dy) {
    context.save();
    turn(context,joints[pivot],angle,dy);
    sprite(context,name);
    context.restore();
  }

  function arm(name,angle,dy) {
    clear(pen);
    pen.setTransform(context.getTransform());
    pen.save();
    turn(pen,joints[name+'Shoulder'],angle,dy);
    sprite(pen,name+'Arm');
    pen.restore();
    pen.translate(0,dy);
    pen.globalCompositeOperation='destination-out';
    sprite(pen,name+'Cover');
    pen.globalCompositeOperation='source-over';
    context.save();
    context.setTransform(1,0,0,1,0,0);
    context.drawImage(scratch,0,0);
    context.restore();
  }

  function expression(frame) {
    const face=controls.closedEyes?'sleep':frame.face??'neutral';
    const mood=model.expressions[face];
    const hasMood=mood!==undefined;
    const side=smooth(wink);
    const nativeBlink=side>.04?0:Math.max(frame.blink??0,face==='wink'?0:frame.eyeClose??0);
    const shared=clamp(Math.max(nativeBlink,smooth(rest)),0,1);
    const blinking=Math.max(shared,side)>.04;
    const speech=Math.round(3*clamp((frame.talk??0)*1.35,0,1));
    sprite(context,'face');
    sprite(context,'frontHair');
    if (blinking) {
      const winkOnly=side>.04&&shared<=.04;
      atlas(context,winkOnly?'winkFace':'blinkFace',Math.round((winkOnly?side:Math.max(shared,side))*16));
    } else if(speech) {
      atlas(context,'talkPortrait',4*(hasMood?mood+1:0)+speech);
    } else if(hasMood) {
      atlas(context,'moodPortrait',mood);
    }
  }

  function anchors() {
    context.fillStyle='#8667bd';
    context.strokeStyle='#fff8ec';
    context.lineWidth=2.5;
    for (const [x,y] of Object.values(joints)) {
      context.beginPath();context.arc(x,y,5,0,TAU);context.fill();context.stroke();
    }
  }

  function draw(group,marks,frame) {
    if(!mount||mount.parentNode!==group) init(group);
    const t=frame.t??0, dt=clamp(t-last,0,.065);
    last=t;
    const face=frame.face??'neutral';
    carry=approach(carry,+(frame.mode==='drag'),dt,8);
    const wantsWink=face==='wink'&&previousFace!==face;
    if(wantsWink) winkAt=t;
    const winkAge=t-winkAt;
    wink=smooth(winkAge/.078)*(1-smooth((winkAge-.081)/.14));
    previousFace=face;
    rest=approach(rest,+(controls.closedEyes||frame.mode==='sleep'||face==='bowing'),dt,17);
    listening=approach(listening,+(face==='listening'),dt,10);
    const walking=frame.mode==='walk';
    if(walking) {
      const x=body?.layout().x;
      if(Number.isFinite(x)&&Number.isFinite(previousX)) {
        const delta=Math.abs(x-previousX)/(host.bounds().S*unit);
        // Small desktop avatars still read as walking even when the kit's
        // unscaled stage velocity would call for a frantic stepping rate.
        walked+=Math.min(delta,WALK_CADENCE_CAP*WALK_CYCLE*dt);
      }
      previousX=x;
    } else {
      previousX=undefined;
      if(wasWalking) {
        const doubleSupport=(STANCE-.5)/2;
        settleAt=(Math.round((walked/WALK_CYCLE-doubleSupport)*2)/2+doubleSupport)*WALK_CYCLE;
      }
      walked=approach(walked,settleAt,dt,12);
    }
    const canSettle=frame.mode==='idle'||walking;
    walkAmount=canSettle?approach(walkAmount,+walking,dt,walking?7:16):0;
    wasWalking=walking;
    const p=solvePose(frame,controls,carry,{distance:walked,amount:walkAmount},listening);
    clear(context);
    if(p.sit) sprite(context,frame.mode==='sleep'?'sleepBody':'sitBody');
    else {
      // The skirt lining, shoulders and upper body share this transform.
      // Both leg transforms remain in the grounded stage coordinate system.
      const bowBody=()=>turn(context,[609,957],p.bow*3.5,p.bow*3.2);
      context.save();
      bowBody();
      rotateSprite('backHair','neck',p.head*.35,p.bodyY);
      rotateSprite('skirtBack','neck',0,p.bodyY);
      context.restore();
      for (const [i,id] of ['right','left'].entries()) {
        const leg=p.legs[i];
        const pivot=id+'Leg';
        const ground=p.walkAmount?soleCorrection(SOLES[i],joints[pivot],leg.angle,gy-1):0;
        rotateSprite('leg'+(id==='right'?'Right':'Left'),pivot,leg.angle,
          p.bodyY*(1-p.walkAmount)+ground*p.walkAmount-leg.lift);
      }
      context.save();
      bowBody();
      rotateSprite('body','neck',0,p.bodyY);
      arm('left',p.arms[0],p.bodyY);
      arm('right',p.arms[1],p.bodyY);
      context.save();
      turn(context,joints.neck,p.head+p.bow*2.2,p.bodyY+p.nod*2+p.bow*3);
      const [headX,headY]=joints.neck;
      context.translate(headX,headY);
      context.transform(1-.016*Math.abs(p.yaw),0,p.yaw*.032,1+p.pitch*.021,0,0);
      context.translate(-headX,-headY);
      sprite(context,'hat');
      lock=approach(lock,clamp(-p.head*.40+Math.sin(t*3)*.42,-1.65,1.65),dt,7);
      for (const [i,name] of ['lockLeft','lockRight'].entries()) {
        context.save();
        turn(context,joints[name],lock*(i===0?1:.7));
        sprite(context,name);
        context.restore();
      }
      expression(frame);
      sprite(context,'hatRim');
      context.restore();
      context.restore();
    }
    if (controls.showJoints) anchors();
    const at=(x,y)=>[u(614)+(x-124)*.75,v(163)+(y-34)*.65];
    const markup=officialFaceEffects(marks??{},t,at,'#ac94c3',1.12);
    if(markup!==fxState) {fx.innerHTML=markup;fxState=markup;}
  }

  const figure={
    draw, dispose(){mount?.remove();fx?.remove();},
    gestures:['nod','shake','bow'],
    groupTilt(mode,tilt,lean){
      if (['idle','walk','sit'].includes(mode)) return 0;
      return mode==='drag'?clamp(tilt+lean*.24,-10,10):clamp(tilt+lean*.2,-4,4);
    },
    anchors:{gaze:[u(655),v(557)],bubble:[u(616),v(64)],z:[u(790),v(115)],
      hearts:[u(528),u(762),v(211)],tear:[u(574),v(577)],tears:[[u(574),v(577)],[u(733),v(579)]]},
    colors:{z:'#ab92ce'},
    extent:[u(181),v(45),u(989),v(1316)],
    hits:[[u(617),v(481),62],[u(604),v(799),39],[u(605),v(1085),29]],
  };
  body=kit.createBody(host,{figure});
  return body;
}
