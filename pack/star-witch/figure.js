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
const FACE_VIEW=[365,305,525,375];

export function solvePose(frame, controls={}, walking, listening) {
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
    +Math.sin(t*1.9)*.55,-3.3,3.3)-7.2*listen;
  const swing=Math.cos(TAU*(walkPhase-.045))*walkAmount;
  // The arm array is left/right, while the legs below are drawn right/left.
  // Pair the near arm with the far leg, and the far arm with the near leg.
  const arms=[
    run?-2.4*runRamp:-3.9*swing,
    run?-1.8*runRamp:3.1*swing,
  ];
  const legs=[0,1].map(i=>{
    const cycle=runPhase+i*Math.PI;
    const step=(walkPhase+i*.5)%1;
    const flight=clamp((step-STANCE)/(1-STANCE),0,1);
    // During support the shoe travels back at the same rate the pet moves.
    // A separate swing returns it forward and lifts it clear of the floor.
    const travel=WALK_CYCLE*(STANCE/2-step+smooth(flight))*walkAmount;
    const stride=-Math.asin(travel/294)*180/Math.PI;
    const lift=13*Math.sin(Math.PI*flight)**2*walkAmount;
    return {
      angle:stride+Math.sin(cycle)*runRamp*4.6,
      lift:lift+Math.max(0,Math.cos(cycle))*runRamp*12,
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

// The same semi-implicit spring, head and shoulder tuning as Xingyun v2 0.1.9.
function heldSpring(k,c,limit) {
  let x=0,v=0;
  return (target,dt)=>{
    v+=((target-x)*k-v*c)*dt;
    x+=v*dt;
    if(Math.abs(x)>limit){x=Math.sign(x)*limit;v=0;}
    return x;
  };
}

const RAD=Math.PI/180;
const PALMS=[[470,973],[774,964]];
function palmArc([sx,sy],[px,py],direction) {
  const dx=px-sx,dy=py-sy;
  const bias=Math.atan2(dx,dy),radius=Math.hypot(dx,dy);
  return {
    height:angle=>sy+radius*Math.cos(angle*RAD-bias),
    angle:height=>(bias+direction*Math.acos(clamp((height-sy)/radius,-1,1)))/RAD,
  };
}

function bodyDepth(doc,body,depth) {
  const [x,y,w,h]=body.box;
  const [mx,my]=depth.box;
  const plane=()=>Object.assign(doc.createElement('canvas'),{width:w,height:h});
  const front=plane(),rear=plane();
  const near=front.getContext('2d'),back=rear.getContext('2d');
  near.drawImage(body.image,0,0);
  back.drawImage(depth.image,mx-x,my-y);
  const foreground=near.getImageData(0,0,w,h),background=back.getImageData(0,0,w,h);
  for(let i=0;i<foreground.data.length;i+=4){
    const alpha=foreground.data[i+3];
    const frontAlpha=Math.round(alpha*(255-background.data[i+3])/255);
    for(let c=0;c<3;c++) background.data[i+c]=foreground.data[i+c];
    background.data[i+3]=frontAlpha<255?Math.round(255*(alpha-frontAlpha)/(255-frontAlpha)):0;
    foreground.data[i+3]=frontAlpha;
  }
  near.putImageData(foreground,0,0);
  back.putImageData(background,0,0);
  front.dataset.texture='body.png';
  rear.dataset.texture='skirtRear.png';
  return {front,rear};
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
  if(parts.skirtDepth){
    const bodyPart=parts.body;
    const {front,rear}=bodyDepth(host.root.ownerDocument,bodyPart,parts.skirtDepth);
    parts.skirtRear={box:bodyPart.box,image:rear};
    bodyPart.image=front;
  }
  const [vx,vy,vw,vh]=model.view, [gx,gy]=model.ground, unit=model.unitsPerPixel;
  const u=x=>128+(x-gx)*unit, v=y=>256+(y-gy)*unit;
  const px=.83;
  let mount, frameCanvas, context, scratch, pen, fx, fxState='';
  let last=0, wink=0, winkAt=-Infinity, rest=0, lock=0, previousFace='neutral';
  let body, listening=0, walked=0, settleAt=0, walkAmount=0, previousX, wasWalking=false;
  let carry=0, carryStretch=0, carryKick=0, lastHeldHead=0, lastHeldYaw=0;
  const heldHead=heldSpring(70,10,16), heldHair=heldSpring(55,7,1.8);
  const dizzyHead=heldSpring(70,10,16);
  let dizzyBend=0, seatedDizzyRig, seatedDizzyCanvas;
  let faceRig,faceRigCanvas,facePainting,foregroundHair,paintKey;
  const heldArms=[heldSpring(60,9,125),heldSpring(60,9,95)];
  const palms=[palmArc(joints.leftShoulder,PALMS[0],1),palmArc(joints.rightShoulder,PALMS[1],-1)];

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

  function dizzyEyes(marks) {
    for(const [i,name] of ['dizzyNear','dizzyFar'].entries()) {
      const {image,box:[x,y,w,h]}=parts[name];
      context.save();
      context.translate(x+w/2,y+h/2);
      context.scale(i===0?.75:.66,i===0?.72:.71);
      context.rotate((marks?.eyes?.[i]?.rot??0)*.6);
      context.drawImage(image,-w/2,-h/2);
      context.restore();
    }
  }

  function seatedDizzy(angle,recovering,marks) {
    if(!seatedDizzyCanvas){
      seatedDizzyCanvas=context.canvas.ownerDocument.createElement('canvas');
      seatedDizzyCanvas.dataset.rig='seat-dizzy';
      [seatedDizzyCanvas.width,seatedDizzyCanvas.height]=[frameCanvas.width,frameCanvas.height];
      const names=['dizzySeat','sleepBody'];
      if(kit.createRig) {
        try {
          seatedDizzyRig=kit.createRig(seatedDizzyCanvas,{
            view:[vx,vy,vx+vw,vy+vh],
            deformers:{head:{kind:'warp',rect:[0,0,model.canvas[0],model.canvas[1]]}},
            parts:names.map(id=>({id,tex:id,box:parts[id].box,z:0,parent:'head',grid:[18,40]})),
          });
          for(const id of names) seatedDizzyRig.upload(id,parts[id].image);
        } catch {
          seatedDizzyRig?.dispose();
          seatedDizzyRig=null;
        }
      }
    }
    if(seatedDizzyRig){
      const [nx,ny]=joints.neck;
      const c=Math.cos(angle*RAD),s=Math.sin(angle*RAD);
      seatedDizzyRig.render({alpha:{dizzySeat:Number(!recovering),sleepBody:Number(recovering)},head:{
        fn:(_u,_v,x,y)=>{
          const k=smooth((752-y)/117);
          const dx=x-nx,dy=y-ny;
          return [k*((c-1)*dx-s*dy),k*(s*dx+(c-1)*dy)];
        },
      }});
      context.drawImage(seatedDizzyCanvas,vx,vy,vw,vh);
    }else{
      sprite(context,recovering?'sleepBody':'dizzySeat');
    }
    if(!recovering){
      context.save();
      turn(context,joints.neck,seatedDizzyRig?angle:0);
      context.transform(...model.dizzySeatFit);
      dizzyEyes(marks);
      context.restore();
    }
  }

  function paintPortrait(ctx,selected) {
    sprite(ctx,'face');
    sprite(ctx,'frontHair');
    if(selected) atlas(ctx,...selected);
  }

  function drawFaceParallax(selected,yaw,pitch) {
    if(!kit.createRig||Math.abs(yaw)+Math.abs(pitch)<.025) return false;
    const [x,y,w,h]=FACE_VIEW;
    if(!faceRigCanvas){
      const doc=context.canvas.ownerDocument;
      facePainting=Object.assign(doc.createElement('canvas'),{width:w,height:h});
      const paint=facePainting.getContext('2d');
      paint.setTransform(1,0,0,1,-x,-y);
      sprite(paint,'frontHair');
      foregroundHair=paint.getImageData(0,0,w,h).data;
      faceRigCanvas=Object.assign(doc.createElement('canvas'),
        {width:Math.ceil(w*px),height:Math.ceil(h*px)});
      faceRigCanvas.dataset.rig='face-parallax';
      try {
        faceRig=kit.createRig(faceRigCanvas,{
          view:[x,y,x+w,y+h],
          deformers:{features:{kind:'warp',rect:[x,y,x+w,y+h]}},
          parts:[{id:'portrait',tex:'portrait',box:FACE_VIEW,z:0,parent:'features',grid:[52,38]}],
        });
      } catch {
        return false;
      }
    }
    if(!faceRig) return false;
    const key=selected?.join('/')??'neutral';
    if(paintKey!==key){
      const paint=facePainting.getContext('2d');
      paint.clearRect(x,y,w,h);
      paintPortrait(paint,selected);
      faceRig.upload('portrait',facePainting);
      paintKey=key;
    }
    const ellipse=(px,py,cx,cy,rx,ry)=>smooth(1-((px-cx)/rx)**2-((py-cy)/ry)**2);
    faceRig.render({features:{fn:(_u,_v,px,py)=>{
      const near=ellipse(px,py,596,551,64,35);
      const far=ellipse(px,py,738,553,27,32);
      const mouth=ellipse(px,py,670,616,43,23);
      if(near+far+mouth===0) return [0,0];
      const ix=Math.round(px-x),iy=Math.round(py-y);
      let hair=0;
      for(const [dx,dy] of [[0,0],[-7,0],[7,0],[0,-7],[0,7]]){
        hair=Math.max(hair,foregroundHair[4*((iy+dy)*w+ix+dx)+3]??255);
      }
      const visible=1-smooth(hair/255);
      return [yaw*visible*(near*6.8+far*4.0+mouth*4.8),
        pitch*visible*(near*4.4+far*3.2+mouth*3.6)];
    }}});
    context.drawImage(faceRigCanvas,x,y,w,h);
    return true;
  }

  function expression(frame,p) {
    const face=controls.closedEyes?'sleep':frame.face??'neutral';
    const mood=model.expressions[face];
    const hasMood=mood!==undefined;
    const side=smooth(wink);
    const nativeBlink=side>.04?0:Math.max(frame.blink??0,face==='wink'?0:frame.eyeClose??0);
    const shared=clamp(Math.max(nativeBlink,smooth(rest)),0,1);
    const blinking=Math.max(shared,side)>.04;
    const speech=Math.round(3*clamp((frame.talk??0)*1.35,0,1));
    let selected;
    if(face==='squeeze'&&frame.mode==='dizzy'){
      selected=['blinkFace',16];
    } else if (blinking) {
      const winkOnly=side>.04&&shared<=.04;
      selected=[winkOnly?'winkFace':'blinkFace',Math.round((winkOnly?side:Math.max(shared,side))*16)];
    } else if(speech) {
      selected=['talkPortrait',4*(hasMood?mood+1:0)+speech];
    } else if(hasMood) {
      selected=['moodPortrait',mood];
    }
    if(!drawFaceParallax(selected,p.yaw,p.pitch)) paintPortrait(context,selected);
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
    const dizzy=frame.mode==='dizzy';
    const grabbed=frame.mode==='drag';
    const inFlight=frame.mode==='air'||frame.mode==='land';
    const oldCarry=carry;
    carry=approach(carry,+(grabbed||(carry>.01&&inFlight)),dt,10);
    carryStretch=approach(carryStretch,+grabbed,dt,8);
    const kickTarget=grabbed?1:(frame.mode==='air'&&carry>.01?.4:0);
    carryKick=approach(carryKick,kickTarget,dt,grabbed?10:24);
    const inputSwing=frame.swing??0;
    const sway=clamp(inputSwing/26,-1.6,1.6);
    const [lookX,lookY]=frame.look??[0,0];
    const head=heldHead(lookX*.7+Math.sin(t*.9)*1.2+lookY*.4+(grabbed?inputSwing*.25:0),dt);
    const yaw=clamp(lookX/5,-1,1)*.9;
    const hair=heldHair(sway*1.1-(head-lastHeldHead)/Math.max(dt,.001)*.004
      -(yaw-lastHeldYaw)/Math.max(dt,.001)*.02,dt);
    lastHeldHead=head;
    lastHeldYaw=yaw;
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
    const p=solvePose(frame,controls,{distance:walked,amount:walkAmount},listening);
    const dizzySeated=dizzy&&p.sit&&parts.dizzySeat;
    const orbit=Boolean(dizzySeated&&face==='dizzy'&&marks?.orbit);
    const dizzyRock=dizzyHead(dizzySeated&&face==='dizzy'?3*Math.sin(t*4.5):0,dt);
    dizzyBend=approach(dizzyBend,dizzySeated?clamp((frame.tilt??0)*.8,-10,12):0,dt,dizzySeated?32:16);
    const dizzyRoll=dizzyRock+dizzyBend;
    if(!controls.still) p.head+=dizzyRoll;
    if (!controls.still&&carry>.005) {
      const bend=((frame.tilt??0)+(frame.lean??0)*Math.sign(frame.facing||1))*(1-oldCarry);
      p.head+=(head+clamp(bend*.8,-10,12)-p.head)*carry;
      const kick=10*Math.sin(t*11)*carryKick;
      p.legs[0].angle+=kick;
      p.legs[1].angle-=kick;
      // The master differs from Xingyun. Solve the same shared low palm
      // height with these shorter sleeves and the two measured palm points.
      const height=956-10*Math.sin(t*13);
      let angles=heldArms.map((step,i)=>step(grabbed?palms[i].angle(height):p.arms[i],dt));
      if(grabbed){
        const shared=(palms[0].height(angles[0])+palms[1].height(angles[1]))*.5;
        angles=palms.map(palm=>palm.angle(shared));
      }
      // The force ramps in from the actual standing pose as the host grabs.
      p.arms=angles.map((angle,i)=>p.arms[i]+(angle-p.arms[i])*carry);
    } else {
      heldArms.forEach(step=>step(0,dt));
    }
    clear(context);
    if(dizzySeated) seatedDizzy(controls.still?0:dizzyRoll,face!=='dizzy',marks);
    else if(p.sit) sprite(context,frame.mode==='sleep'?'sleepBody':'sitBody');
    else {
      if(!controls.still&&carry>.005) {
        // Invert the kit's drag stretch about the scruff, as in Xingyun v2.
        const scruff=gy+(36-256)/unit;
        context.translate(gx,scruff);
        context.scale(1/(1-.05*carryStretch),1/(1+.09*carryStretch));
        context.translate(-gx,-scruff);
        turn(context,joints.neck,(-sway*1.2+inputSwing*.15)*carry);
      }
      // The skirt lining, shoulders and upper body share this transform.
      // Both leg transforms remain in the grounded stage coordinate system.
      const bowBody=()=>turn(context,[609,957],p.bow*3.5,p.bow*3.2);
      context.save();
      bowBody();
      rotateSprite('backHair','neck',p.head*.35,p.bodyY);
      rotateSprite('skirtBack','neck',0,p.bodyY);
      if(parts.skirtRear) rotateSprite('skirtRear','neck',0,p.bodyY);
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
        const freeSwing=lock*(i===0?1:.7);
        const heldSwing=clamp(-head*.55+hair*5.8,-12,12)*(i===0?1:.78);
        turn(context,joints[name],freeSwing+(heldSwing-freeSwing)*(controls.still?0:carry));
        sprite(context,name);
        context.restore();
      }
      expression(frame,p);
      sprite(context,'hatRim');
      context.restore();
      context.restore();
    }
    if (controls.showJoints) anchors();
    const [nx,ny]=joints.neck;
    const crown=orbit?[nx+(614-nx)*Math.cos(dizzyRoll*RAD)-(104-ny)*Math.sin(dizzyRoll*RAD),
      ny+(614-nx)*Math.sin(dizzyRoll*RAD)+(104-ny)*Math.cos(dizzyRoll*RAD)]:[614,163];
    const at=(x,y)=>[u(crown[0])+(x-124)*.75,v(crown[1])+(y-34)*.65];
    const markup=officialFaceEffects({...marks,orbit},t,at,'#ac94c3',1.12);
    if(markup!==fxState) {fx.innerHTML=markup;fxState=markup;}
  }

  const figure={
    draw, dispose(){faceRig?.dispose();seatedDizzyRig?.dispose();mount?.remove();fx?.remove();},
    gestures:['nod','shake','bow'],
    groupTilt(mode,tilt,lean){
      if(mode==='dizzy') return 0;
      if(mode==='drag'||carry>.01) return (tilt+lean)*carry;
      if (['idle','walk','sit'].includes(mode)) return 0;
      return clamp(tilt+lean*.2,-4,4);
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
