import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as sleep } from 'node:timers/promises';
import assert from 'node:assert/strict';

const here=fileURLToPath(new URL('.',import.meta.url));
const review=resolve(here,'review');
const profile=await mkdtemp(join(review,'edge-check-'));
const edge=process.env.WITCH_EDGE??'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const child=spawn(edge,['--headless=new','--remote-debugging-port=0','--no-first-run',
  '--disable-extensions','--disable-background-timer-throttling','--disable-renderer-backgrounding',
  '--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
let socket;
const messages=[];
async function connect() {
  let port;
  for(let i=0;i<100;i++) {
    try {port=+(await readFile(join(profile,'DevToolsActivePort'),'utf8')).split(/\r?\n/)[0];break;}
    catch(error){if(error.code!=='ENOENT')throw error;}
    if(child.exitCode!==null)throw Error('Edge exited '+child.exitCode);
    await sleep(100);
  }
  if(!port)throw Error('No Edge debugging port.');
  const tab=(await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(item=>item.type==='page');
  socket=new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((ok,bad)=>{socket.addEventListener('open',ok,{once:true});socket.addEventListener('error',bad,{once:true});});
  let id=0;
  const pending=new Map();
  socket.addEventListener('message',event=>{
    const data=JSON.parse(event.data);
    if(data.id&&pending.has(data.id)){
      const [ok,bad]=pending.get(data.id);
      pending.delete(data.id);
      if(data.error)bad(data.error);else ok(data.result);
    }else if(data.method==='Runtime.exceptionThrown'){
      messages.push(data.params.exceptionDetails.exception?.description??data.params.exceptionDetails.text);
    }
  });
  return (method,params={})=>new Promise((ok,bad)=>{
    const key=++id;pending.set(key,[ok,bad]);socket.send(JSON.stringify({id:key,method,params}));
  });
}
try{
  const cdp=await connect();
  await cdp('Page.enable');
  await cdp('Runtime.enable');
  await cdp('Page.addScriptToEvaluateOnNewDocument',{source:`
    window.witchPaints=[];
    window.witchMotion={};
    window.witchDizzy={draws:0};
    window.witchStartFrames=[];
    const clear=CanvasRenderingContext2D.prototype.clearRect;
    CanvasRenderingContext2D.prototype.clearRect=function(...args){
      if(this.canvas.parentNode?.localName==='foreignObject'){
        const frame={layers:[],stars:0};
        window.witchFrame=frame;
        if(window.witchTraceStart){
          window.witchStartFrames.push(frame);
          queueMicrotask(()=>{frame.stars=document.querySelectorAll('path[fill="#ffd23f"]').length;});
        }
      }
      return clear.apply(this,args);
    };
    for(const Gl of [window.WebGLRenderingContext,window.WebGL2RenderingContext]){
      const upload=Gl.prototype.bufferSubData;
      Gl.prototype.bufferSubData=function(target,offset,data,...rest){
        if(data instanceof Float32Array&&data.length===1558){
          window.witchDizzy.mesh={topX:data[0],toeX:data.at(-2),toeY:data.at(-1)};
        }
        if(data instanceof Float32Array&&data.length===4134){
          const vertex=(row,col)=>[data[(row*53+col)*2],data[(row*53+col)*2+1]];
          window.witchFaceMesh={eye:vertex(25,23),jaw:vertex(34,30),fringe:vertex(22,27)};
        }
        return upload.call(this,target,offset,data,...rest);
      };
    }
    const previous=CanvasRenderingContext2D.prototype.drawImage;
    CanvasRenderingContext2D.prototype.drawImage=function(image,...args){
      const path=image?.src?.split('?')[0];
      const name=path?.split('/').pop()??image?.dataset?.texture;
      if(this.canvas.parentNode?.localName==='foreignObject'&&window.witchFrame){
        const layer=name??image?.dataset?.rig;
        if(layer) window.witchFrame.layers.push(layer);
      }
      if(image?.dataset?.rig==='seat-dizzy') window.witchDizzy.draws++;
      if (['body.png','hat.png','legRight.png','legLeft.png','leftArm.png','rightArm.png','lockLeft.png','sitBody.png','dizzyNear.png','dizzyFar.png'].includes(name)) {
        const {a,b,c,d,e,f}=this.getTransform();
        window.witchMotion[name]={a,b,c,d,e,f,angle:Math.atan2(b,a)*180/Math.PI};
      }
      if (['moodPortrait.png','talkPortrait.png','blinkFace.png','winkFace.png','sleepBody.png'].includes(name)) {
        const columns=name==='blinkFace.png'||name==='winkFace.png'?5:4;
        const frame=args.length===8?(args[1]/args[3])*columns+args[0]/args[2]:0;
        const list=window.witchPaints;
        list.push({name,frame,time:performance.now()});
        if(list.length>160) list.shift();
      }
      return previous.call(this,image,...args);
    };
  `});
  await cdp('Emulation.setDeviceMetricsOverride',{width:1180,height:900,deviceScaleFactor:1,mobile:false});
  await cdp('Page.navigate',{url:process.env.WITCH_PREVIEW??'http://127.0.0.1:4334/'});
  async function read(expression) {
    const result=await cdp('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
    if(result.exceptionDetails)throw Error(result.exceptionDetails.exception?.description??result.exceptionDetails.text);
    return result.result.value;
  }
  const results={};
  async function waitFor(expression) {
    for(let i=0;i<85;i++){
      if(await read(expression))return;
      await sleep(65);
    }
    throw Error('Preview condition not met '+expression);
  }
  const shot=async name=>{
    const {data}=await cdp('Page.captureScreenshot',{format:'png',fromSurface:true});
    await writeFile(join(review,'preview-'+name+'.png'),Buffer.from(data,'base64'));
  };
  const action=async (name,delay=220)=>{await read(`witchPreview.action(${JSON.stringify(name)})`);await sleep(delay);};
  const mode=()=>read('witchPreview.body.layout().mode');
  async function painted(name,frame,after) {
    await waitFor(`witchPaints.some(item=>item.name===${JSON.stringify(name+'.png')}&&
      item.time>=${after}&&(${frame}===-1||item.frame===${frame}))`);
  }
  const motion=()=>read(`({
    ...witchMotion,
    x:witchPreview.body.layout().x,
    facing:witchPreview.body.layout().facing,
    rootAngle:document.querySelector('svg.kit foreignObject').parentNode.transform.baseVal.getItem(1).angle,
  })`);
  await waitFor('Boolean(window.witchPreview)');
  const model=await read("fetch('/pack/star-witch/model.json').then(response=>response.json())");
  await action('compare');
  await shot('stand');
  let since=await read('performance.now()');
  await action('closed',420);
  await painted('blinkFace',16,since);
  await shot('closed');
  await action('closed');
  since=await read('performance.now()');
  await action('wink',105);
  await shot('wink');
  await painted('winkFace',-1,since);
  await action('stand',170);
  await action('compare');
  await read('witchPreview.controls.look=[-12,10]');
  await waitFor('Boolean(window.witchFaceMesh)');
  await sleep(220);await shot('head-left');
  const faceLeft=await read('witchFaceMesh');
  await read('witchPreview.controls.look=[12,-10]');
  await sleep(220);await shot('head-right');
  const faceRight=await read('witchFaceMesh');
  assert.ok(faceRight.eye[0]-faceLeft.eye[0]>6&&faceLeft.eye[1]-faceRight.eye[1]>3);
  assert.deepEqual(faceLeft.jaw,faceRight.jaw);
  assert.deepEqual(faceLeft.fringe,faceRight.fringe);
  results.parallax={nearEyeX:faceRight.eye[0]-faceLeft.eye[0],
    nearEyeY:faceLeft.eye[1]-faceRight.eye[1],jawFixed:true,fringeFixed:true};
  await action('follow');
  await action('stand',250);
  const baseline=await motion();
  await action('listen',500);
  const listening=await motion();
  assert.equal(listening.rootAngle,0);
  assert.equal(listening['body.png'].angle,0);
  assert.ok(listening['hat.png'].angle<baseline['hat.png'].angle-4);
  await shot('listen');
  await waitFor(`Math.abs(witchMotion['hat.png'].angle-(${baseline['hat.png'].angle}))<2.5`);
  results.listen={head: listening['hat.png'].angle,torso:0,stage:0};
  await read('witchTraceStart=true');
  await action('dizzy',520);
  assert.equal(await mode(),'dizzy');
  const startFrames=await read('(witchTraceStart=false,witchStartFrames)');
  const firstSeat=startFrames.findIndex(f=>f.layers.includes('seat-dizzy')||f.layers.includes('dizzySeat.png'));
  assert.ok(firstSeat>0&&startFrames[firstSeat-1].layers.includes('body.png'));
  assert.ok(startFrames.slice(0,firstSeat).every(f=>f.stars===0&&
    !f.layers.some(name=>['dizzyNear.png','dizzyFar.png','dizzyPortrait.png'].includes(name))),
    'Standing frames must not show dizzy eyes or stars');
  assert.ok(startFrames[firstSeat].stars===3&&
    ['dizzyNear.png','dizzyFar.png'].every(name=>startFrames[firstSeat].layers.includes(name)),
    'First seated frame must show both spirals and orbit stars');
  const dizzyFrames=[];
  const swayShots=new Set();
  for(let i=0;i<12;i++) {
    const pose=await motion();
    const dizzy=await read(`({
      ...witchDizzy,
      stars:[...document.querySelectorAll('path[fill="#ffd23f"]')].map(p=>p.getAttribute('transform'))
    })`);
    dizzyFrames.push({...dizzy,pose});
    const sway=dizzy.mesh?.topX-model.parts.dizzySeat.box[0];
    const direction=sway>40?'dizzy':sway<-40?'dizzy-other-side':null;
    if(direction&&!swayShots.has(direction)){
      swayShots.add(direction);
      await shot(direction);
    }
    await sleep(110);
  }
  const span=values=>Math.max(...values)-Math.min(...values);
  assert.ok(dizzyFrames.every(f=>f.draws>0&&f.mesh&&f.stars.length===3),'Expected seated head mesh and orbit stars');
  assert.ok(dizzyFrames.every(f=>f.pose.rootAngle===0),'Dizzy must not rock the stage root');
  assert.ok(span(dizzyFrames.map(f=>f.mesh.topX))>35,'Head must sway while seated');
  assert.ok(span(dizzyFrames.map(f=>f.mesh.toeX))<.01&&span(dizzyFrames.map(f=>f.mesh.toeY))<.01,'Chair and feet must stay put');
  for(const eye of ['dizzyNear.png','dizzyFar.png']){
    assert.ok(span(dizzyFrames.map(f=>f.pose[eye].angle))>120,'Painted spiral must rotate through several phases');
  }
  assert.ok(new Set(dizzyFrames.map(f=>f.stars.join('|'))).size>8);
  const recoveryStart=await read('witchDizzy.draws');
  await waitFor('document.querySelectorAll(\'path[fill="#ffd23f"]\').length===0');
  assert.equal(await mode(),'dizzy');
  await shot('dizzy-recovery');
  assert.ok(await read('witchDizzy.draws')>recoveryStart);
  const recovery=[];
  for(let i=0;i<4;i++){
    recovery.push(await read('witchDizzy.mesh.topX'));
    await sleep(52);
  }
  assert.ok(span(recovery)>8,'Closed-eye recovery must shake before settling');
  await waitFor('witchPreview.body.layout().mode==="idle"');
  results.dizzy={onset:'seat, eyes and stars together',seatedFrames:dizzyFrames.length,
    headRange:span(dizzyFrames.map(f=>f.mesh.topX)),rotatingEyes:2,recovered:true};
  await action('walk',430);
  results.walk=await mode();assert.equal(results.walk,'walk');await shot('walk');
  const frames=[];
  for(let i=0;i<15;i++){
    frames.push(await motion());
    await sleep(55);
  }
  for(const sample of frames) {
    assert.equal(sample.rootAngle,0);
    assert.equal(sample['body.png'].angle,0);
  }
  assert.ok(Math.abs(frames.at(-1).x-frames[0].x)>10);
  for(const name of ['legLeft.png','legRight.png']){
    const angles=frames.map(frame=>frame[name].angle);
    assert.ok(Math.max(...angles)>2.5 && Math.min(...angles)<-2.5);
  }
  function assertSoleSupport(samples) {
    // Probe the source-space sole heights through the rendered Canvas matrices.
    const floor=samples[0]['body.png'].d*(1312-12);
    const bottom=(matrix,points)=>Math.max(...points.map(([x,y])=>matrix.b*x+matrix.d*y+matrix.f));
    const soleYs=samples.map(frame=>[
      bottom(frame['legLeft.png'],[[543,1309],[559,1312],[580,1312],[594,1309]]),
      bottom(frame['legRight.png'],[[647,1302],[668,1305],[680,1305],[700,1302]]),
    ]);
    assert.ok(soleYs.every(ys=>Math.abs(Math.max(...ys)-floor)<2));
    assert.ok(soleYs.some(([a,b])=>a-b>7)&&soleYs.some(([a,b])=>b-a>7));
    return soleYs.length;
  }
  // Select well-separated poses where the direction of each limb is readable.
  // Check the actual rotated sprites, including arm masks rendered offscreen.
  function assertOppositeLimbSwing(samples) {
    const forward = samples.filter(s=>Math.abs(s['legRight.png'].angle)>2.5 &&
      Math.abs(s['legLeft.png'].angle)>2.5 &&
      Math.sign(s['legRight.png'].angle)!==Math.sign(s['legLeft.png'].angle));
    assert.deepEqual([...new Set(forward.map(s=>Math.sign(s['legRight.png'].angle)))].sort(),[-1,1]);
    for (const sample of forward) {
      for (const [side,opposite] of [['left','Right'],['right','Left']]) {
        const arm = sample[side+'Arm.png'].angle;
        assert.ok(arm*sample['leg'+opposite+'.png'].angle>0, 'Contralateral arm and leg must swing together');
      }
    }
    return forward.length;
  }
  assert.ok(frames.at(-1).x>frames[0].x);
  await waitFor('witchPreview.body.layout().mode==="idle"');
  await action('walk',450);
  assert.equal(await mode(),'walk');
  await shot('walk-left');
  const mirrored=[];
  for(let i=0;i<15;i++){
    mirrored.push(await motion());
    await sleep(55);
  }
  assert.ok(mirrored.at(-1).x<mirrored[0].x);
  assert.equal(frames.at(-1).facing,1);
  assert.equal(mirrored.at(-1).facing,-1);
  results.walkContralateralSamples={right:assertOppositeLimbSwing(frames),left:assertOppositeLimbSwing(mirrored)};
  results.walkSupportSamples={right:assertSoleSupport(frames),left:assertSoleSupport(mirrored)};
  await waitFor('witchPreview.body.layout().mode==="idle"');
  await action('run',300);
  results.run=await mode();assert.equal(results.run,'run');await shot('run');
  await action('stand',200);
  await action('sit',490);
  results.sit=await mode();assert.equal(results.sit,'sit');await shot('sit');
  await action('listen',350);
  const seated=await motion();
  assert.equal(await mode(),'sit');
  assert.equal(seated.rootAngle,0);
  assert.equal(seated['sitBody.png'].angle,0);
  await sleep(1480);
  await action('sleep',330);
  results.sleep=await mode();assert.equal(results.sleep,'sleep');await shot('sleep');
  await painted('sleepBody',0,await read('performance.now()')-100);
  await action('stand',2050);
  results.portraits=[];
  for(const name of ['happy','surprised','angry','shy','sad','confused','sleepy','love']){
    since=await read('performance.now()');
    await action(name,410);
    await painted('moodPortrait',model.expressions[name],since);
    await shot(name);
    results.portraits.push(name);
  }
  await action('stand');
  since=await read('performance.now()');
  await action('talk',30);
  await painted('talkPortrait',3,since);
  await shot('talk');
  results.talk=true;
  await sleep(1800);
  since=await read('performance.now()');
  await action('bow',570);
  await painted('blinkFace',16,since);
  await shot('bow');
  assert.equal(await mode(),'idle');
  results.bow=true;
  await action('stand');
  since=await read('performance.now()');
  const grab=await read(`(() => {
    const body=witchPreview.body, p=body.layout().hit[0], t=performance.now();
    body.pointer('down',{...p,t});
    return p;
  })()`);
  const dragTo=dx=>read(`witchPreview.body.pointer('move',{
    x:${grab.x+dx},y:${grab.y-85},t:performance.now()})`);
  await sleep(55);
  await dragTo(0);
  await sleep(450);
  results.drag=await mode();assert.equal(results.drag,'drag');
  const layers=await read('witchFrame.layers');
  const skirtOrder=['skirtBack.png','skirtRear.png','legRight.png','legLeft.png','body.png'].map(name=>layers.indexOf(name));
  assert.ok(skirtOrder[0]>=0&&skirtOrder.every((index,i)=>i===0||index>skirtOrder[i-1]),
    'Both legs must render between the rear hem and the front skirt');
  results.skirtDepth=true;
  await painted('moodPortrait',model.expressions.dragged,since);
  const getPalmHeight=(pose,name,[x,y])=>{
    const arm=pose[name],body=pose['body.png'];
    const ax=arm.a*x+arm.c*y+arm.e-body.e;
    const ay=arm.b*x+arm.d*y+arm.f-body.f;
    return (body.a*ay-body.b*ax)/(body.a*body.d-body.b*body.c);
  };
  const dragTest={};
  for(const direction of [1,-1]) {
    for(let i=1;i<=6;i++){
      await dragTo(direction*(-80+40*i));
      await sleep(34);
    }
    await shot(direction>0?'drag':'drag-left');
    const sample=[];
    for(let i=0;i<25;i++){
      sample.push(await motion());
      await sleep(48);
    }
    const roll=sample.map(p=>p.rootAngle*direction);
    const neck=sample.map(p=>p['hat.png'].angle-p['body.png'].angle);
    const hair=sample.map(p=>p['lockLeft.png'].angle-p['hat.png'].angle);
    const peak=Math.max(...roll.slice(0,12));
    const rebound=Math.min(...roll.slice(3,19));
    const steady=Math.max(...roll.slice(-4).map(Math.abs));
    const range=values=>Math.max(...values)-Math.min(...values);
    const kick=sample.map(p=>p['legRight.png'].angle-p['legLeft.png'].angle);
    const palmGap=Math.max(...sample.map(p=>Math.abs(
      getPalmHeight(p,'leftArm.png',[470,973])-getPalmHeight(p,'rightArm.png',[774,964]))));
    assert.ok(peak>7&&rebound<-1.2&&steady<peak*.24,
      `Held body must rebound and settle: ${JSON.stringify({peak,rebound,steady})}`);
    assert.ok(range(neck)>4&&range(hair)>2.4,
      `Head and hair must keep separate motion: ${JSON.stringify({neck:range(neck),hair:range(hair)})}`);
    assert.ok(Math.max(...kick)>8&&Math.min(...kick)<-8,'Both legs must take turns swinging from the hips');
    assert.ok(palmGap<2.5,`Held palms must stay level relative to torso (gap ${palmGap})`);
    dragTest[direction>0?'right':'left']={peak,rebound,steady,palmGap};
  }
  results.dragMotion=dragTest;
  await dragTo(-160);
  await sleep(130);
  await dragTo(-160);
  await sleep(130);
  await read(`witchPreview.body.pointer('up',{
    x:${grab.x-160},y:${grab.y-85},t:performance.now()})`);
  await waitFor('witchPreview.events.some(([kind,data])=>kind==="touch"&&data.kind==="drop")');
  await waitFor('witchPreview.events.some(([kind,data])=>kind==="mode"&&data.mode==="land")');
  await waitFor('witchPreview.body.layout().mode==="idle"');
  results.drop=true;
  assert.deepEqual(messages,[]);
  await writeFile(join(review,'preview-qa.json'),JSON.stringify(results,null,2));
  console.log(results);
}finally{
  socket?.close();
  if(child.exitCode===null){child.kill();await Promise.race([once(child,'exit'),sleep(1500)]);}
  if(resolve(profile).startsWith(review+sep))await rm(profile,{recursive:true,force:true,maxRetries:5,retryDelay:100}).catch(()=>{});
}
