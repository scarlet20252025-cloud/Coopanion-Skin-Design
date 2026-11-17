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
    const previous=CanvasRenderingContext2D.prototype.drawImage;
    CanvasRenderingContext2D.prototype.drawImage=function(image,...args){
      const path=image?.src?.split('?')[0];
      const name=path?.split('/').pop();
      if (['body.png','hat.png','legRight.png','legLeft.png','sitBody.png'].includes(name)) {
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
  await sleep(220);await shot('head-left');
  await read('witchPreview.controls.look=[12,-10]');
  await sleep(220);await shot('head-right');
  await action('follow');
  await action('stand',250);
  const baseline=await motion();
  await action('listen',500);
  const listening=await motion();
  assert.equal(listening.rootAngle,0);
  assert.equal(listening['body.png'].angle,0);
  assert.ok(listening['hat.png'].angle<baseline['hat.png'].angle-4);
  await shot('listen');
  await sleep(1500);
  const listened=await motion();
  assert.ok(Math.abs(listened['hat.png'].angle-baseline['hat.png'].angle)<2.5);
  results.listen={head: listening['hat.png'].angle,torso:0,stage:0};
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
  // Probe the source-space sole heights through the rendered Canvas matrices.
  const floor=frames[0]['body.png'].d*(1312-12);
  const bottom=(matrix,points)=>Math.max(...points.map(([x,y])=>matrix.b*x+matrix.d*y+matrix.f));
  const soleYs=frames.map(frame=>[
    bottom(frame['legLeft.png'],[[543,1309],[559,1312],[580,1312],[594,1309]]),
    bottom(frame['legRight.png'],[[647,1302],[668,1305],[680,1305],[700,1302]]),
  ]);
  assert.ok(soleYs.every(ys=>Math.abs(Math.max(...ys)-floor)<2));
  assert.ok(soleYs.some(([a,b])=>a-b>7)&&soleYs.some(([a,b])=>b-a>7));
  results.walkSupportSamples=soleYs.length;
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
  await read(`(() => {
    const body=witchPreview.body, p=body.layout().hit[0], t=performance.now();
    body.pointer('down',{...p,t}); body.pointer('move',{x:p.x+18,y:p.y-85,t:t+80});
  })()`);
  await sleep(360);
  results.drag=await mode();assert.equal(results.drag,'drag');await shot('drag');
  await painted('moodPortrait',model.expressions.dragged,since);
  await read(`(() => {
    const body=witchPreview.body, p=body.layout().hit[0], t=performance.now();
    body.pointer('move',{...p,t:t-250}); body.pointer('move',{...p,t:t-120});
    body.pointer('up',{...p,t});
  })()`);
  await waitFor('witchPreview.events.some(([kind,data])=>kind==="touch"&&data.kind==="drop")');
  await waitFor('witchPreview.events.some(([kind,data])=>kind==="mode"&&data.mode==="land")');
  results.drop=true;
  assert.deepEqual(messages,[]);
  await writeFile(join(review,'preview-qa.json'),JSON.stringify(results,null,2));
  console.log(results);
}finally{
  socket?.close();
  if(child.exitCode===null){child.kill();await Promise.race([once(child,'exit'),sleep(1500)]);}
  if(resolve(profile).startsWith(review+sep))await rm(profile,{recursive:true,force:true,maxRetries:5,retryDelay:100}).catch(()=>{});
}
