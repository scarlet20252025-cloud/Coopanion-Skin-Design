/* Exercise the draft through the Coopanion kit's actual command and frame path. */
import assert from 'node:assert/strict';
import { createPet } from './vendor/Coopanion-web/kit/body.js';
import { createXingyunBody } from './pack/xingyun-v2/figure.js';

const origin = process.argv[2] ?? 'http://127.0.0.1:4332';
const {revision,error} = await fetch(origin+'/draft-status.json').then(r=>r.json());
assert.ok(revision && !error,error);
const draft = new URL(`/draft/${revision}/`,origin);
const [model,manifest] = await Promise.all(['model.json','figure.json']
  .map(file=>fetch(new URL(file,draft)).then(r=>r.json())));
assert.equal(model.deformers.ahoge.parent,'head');
assert.equal(model.mouthAtlas.frames.smile,0);
if (model.brows) {
  const hair=model.parts.find(part=>part.id==='frontHair');
  const brows=model.parts.filter(part=>part.id.startsWith('brow'));
  assert.equal(brows.length,2);
  assert.ok(brows.every(brow=>brow.z>hair.z && brow.alpha>0 && brow.alpha<1));
}

function node() {
  const ctx={clearRect(){this.drawn=undefined;},drawImage(...args){this.drawn=args;},
    save(){},restore(){},translate(){},rotate(){}};
  return {dataset:{},style:{},isConnected:true,setAttribute(){},appendChild(){},
    prepend(){},remove(){},getContext(){return ctx;}};
}
const doc={createElement:node,createElementNS:node};
const bounds=()=>({W:900,H:500,floorY:465,S:1.42});

async function sample(word,kind) {
  const poses=[], uploads=new Map();
  let fxLayer, extraWords;
  const kit={
    createBody:(_,{figure,words})=>{extraWords=words;return figure;},
    createRig:()=>({dispose(){},upload(key,value){uploads.set(key,value);},render(st){poses.push(st);},
      point(_key,_st,x,y){return [x,y];}}),
  };
  const figure=await createXingyunBody(draft,{kit,model,loadImage:async url=>url});
  const group={...node(),ownerDocument:doc,appendChild(child){if(child.dataset.faceFx) fxLayer=child;}};
  const ctl=createPet({petG:group,shadowEl:node(),fxG:node()},
    {figure,bounds,roam:'off',sfx:{},words:extraWords});
  ctl.render();
  poses.length=0;
  if(word==='listening') ctl.setListening(true);
  else if(word==='carried') {
    ctl.pointerDown(ctl.layout().hit[0]);
    ctl.pointerMove({x:450,y:100,t:0});
    assert.equal(ctl.layout().mode,'drag');
  } else assert.ok(ctl.doWord(word),word);
  for(let i=0;i<(word==='wag'||word==='neutral'?360:240);i++) {
    if(word==='carried') {
      if(i===175) ctl.dropAt({x:450,y:100});
      else if(i<175) ctl.pointerMove({x:450+(i<84?90*Math.sin(i/9):0),y:100,t:i/60});
    }
    ctl.step(1/60);
    ctl.render();
    if (i===39) {
      const mark={angry:'#e5484d',dizzy:'#ffd23f',worried:'#8fd0ff',
        flustered:'#8fd0ff',scared:'#8fd0ff',surprised:'M0 -16V3',confused:'M-8 -9',thinking:'#e8f0ff'}[word];
      if(mark) assert.ok(fxLayer.innerHTML.includes(mark),`${word} official effect`);
    }
    if (i===39 && (kind==='expression'||word==='carried')) {
      const expression=word==='carried'?'dragged':word;
      const mouth=model.mouthAtlas;
      const index=mouth.frames[expression+'Face'];
      assert.notEqual(index,undefined,word);
      const tile=uploads.get('mouthExpression').getContext('2d').drawn;
      assert.deepEqual(tile.slice(1,3),[index%mouth.columns*mouth.width,
        Math.floor(index/mouth.columns)*mouth.height],`${word} mouth`);
      for(const [key,eye] of Object.entries(model.eyeAtlases)){
        const group=expression==='neutral'?0:eye.poses[expression];
        assert.notEqual(group,undefined,word);
        const tile=uploads.get(key).getContext('2d').drawn;
        assert.deepEqual(tile.slice(1,3),[0,group*Math.ceil(eye.count/eye.columns)*eye.height],
          `${word} ${key} must hold its authored pose, not a blink frame`);
      }
    }
  }
  assert.ok(poses.every(p=>Number.isFinite(p.ahoge.a)
    && p.tail.fn(.95,.5,102,210).every(Number.isFinite)),word);
  assert.ok(uploads.has('mouthExpression'),word);
  return poses;
}

const outcomes=new Map();
for(const word of manifest.vocab) outcomes.set(word.id,await sample(word.id,word.kind));
for(const word of ['listening','carried']) outcomes.set(word,await sample(word));
const action=(word,key,read)=>outcomes.get(word).map(pose=>read(pose[key]));
assert.ok(Math.min(...action('wave','rightArm',arm=>arm.a))<-45);
const seat = model.parts.find(part=>part.id==='sitBody');
assert.ok(seat && seat.alpha===0);
assert.ok(Math.abs(seat.box[1]+seat.box[3]+model.seatDepth-256-2*model.unit)<.0001);
const z=key=>model.parts.find(part=>part.id===key).z;
assert.ok(z('capeRear')<z('tail')&&z('tail')<z('body'));
assert.ok(z('sitCapeRear')<z('tail')&&z('tail')<z('sitBody'));
for (const word of ['sit','sleep']) {
  assert.ok(outcomes.get(word).every(pose=>pose.alpha.sitBody===1
    && pose.alpha.sitCapeRear===1 && pose.alpha.capeRear===0
    && pose.body.ty===model.seatDepth
    && pose.tail.fn(0,.55,65,224).every(n=>n===0)
    && ['leftLeg','rightLeg','leftArm','rightArm','body','skirtLining'].every(key=>pose.alpha[key]===0)
    && !pose.leftLeg && !pose.rightLeg),`${word} must use the independent seated painting immediately`);
}
for (const word of ['stand','jump','walk','run','dizzy']) {
  assert.ok(outcomes.get(word).every(pose=>pose.alpha.sitBody===0 && pose.leftLeg && pose.rightLeg),word);
}
assert.ok(Math.max(...action('bow','neck',neck=>neck.ty))>2);
assert.ok(action('listening','neck',neck=>neck.a)[70]<-7);
assert.equal(action('listening','body',body=>body.a)[70],0);
const held=outcomes.get('carried');
const spread=values=>Math.max(...values)-Math.min(...values);
assert.ok(spread(held.slice(24,84).map(p=>p.body.a))>1.5);
const settledSwing=spread(held.slice(145,170).map(p=>p.body.a));
assert.ok(settledSwing<.35,`held sway never settled: ${settledSwing}`);
const heldStill=held.slice(135,175);
function palmY(key,[x,y],a) {
  const pivot=model.deformers[key].pivot;
  const [gx,gy]=model.ground;
  const [px,py]=[gx+(pivot[0]-128)/model.unit,gy+(pivot[1]-256)/model.unit];
  const angle=a*Math.PI/180;
  return py+(x-px)*Math.sin(angle)+(y-py)*Math.cos(angle);
}
const palmHeights=heldStill.map(p=>[
  palmY('leftArm',[465.7,904.5],p.leftArm.a),
  palmY('rightArm',[827,898.5],p.rightArm.a),
]);
assert.ok(palmHeights.every(([near,far])=>Math.abs(near-far)<.001 && near>848 && near<878));
assert.ok(spread(palmHeights.map(([near])=>near))>6);
for(const key of ['leftLeg','rightLeg']) {
  assert.equal(model.parts.find(p=>p.id===key).parent,key+'Held');
  const [x,y]=model.deformers[key].pivot;
  assert.ok(heldStill.every(p=>p[key+'Held'].fn(0,0,x,y-6).every(n=>n===0)));
  assert.ok(spread(heldStill.map(p=>p[key+'Held'].fn(0,1,x,y+30)[0]))>9);
}
assert.ok(Math.abs(held[235].leftArm.a)<2);
const running=outcomes.get('run').filter(p=>p.body.a>8);
assert.ok(running.length>20);
assert.ok(running.some(p=>p.body.ty<-2 && p.leftLeg.ty<-1 && p.rightLeg.ty<-1));
assert.ok(running.some(p=>Math.abs(p.leftArm.a-16)<.35 && Math.abs(p.rightArm.a-14)<.35));
const steadyRun=running.filter(p=>p.body.a>10.17);
assert.ok(steadyRun.length>8 && steadyRun.every(p=>Math.abs(p.leftArm.a-16)<2
  && Math.abs(p.rightArm.a-14)<2));
assert.equal(Math.max(...action('walk','body',body=>body.a)),0);
const tailY=word=>action(word,'tail',tail=>tail.fn(0,.55,65,224)[1]);
const idle=spread(tailY('neutral').slice(40,130));
assert.ok(spread(tailY('happy').slice(40,105))>idle+3);
const wag=tailY('wag');
assert.ok(spread(wag.slice(40,130))>idle+3);
assert.ok(spread(wag.slice(220,360))<spread(tailY('neutral').slice(220,360))+2);
const [gx,gy]=model.ground;
const tx=128+(513-gx)*model.unit, ty=256+(985-gy)*model.unit;
assert.ok(outcomes.get('wag').every(p=>p.tail.fn(1,.5,tx,ty).every(n=>n===0)));
assert.ok(outcomes.get('wag').every(p=>p.body.ty===0 && p.leftLeg.a===0 && p.rightLeg.a===0));
const hair=key=>model.parts.find(part=>part.id===key);
assert.deepEqual(hair('frontHair').sourceBox,hair('backHair').sourceBox);
assert.deepEqual(hair('frontHair').grid,hair('backHair').grid);
function earDelta(p,nx,ny) {
  const [u,v]=[(nx-260)/700,(ny-40)/860];
  const [x,y]=[128+(nx-gx)*model.unit,256+(ny-gy)*model.unit];
  const [baseX,baseY]=p.head.fn(u,v,x,256+(280-gy)*model.unit);
  const [dx,dy]=p.head.fn(u,v,x,y);
  return [dx-baseX,dy-baseY];
}
assert.ok(earDelta(outcomes.get('happy')[45],403,94)[0]<-2);
assert.ok(earDelta(outcomes.get('happy')[45],808,101)[0]>2);
assert.ok(outcomes.get('carried').every(p=>earDelta(p,438,264).every(n=>n===0)));
if (model.brows) {
  const furrow=action('angry','browLeft',brow=>brow.fn(1)[1]-brow.fn(0)[1]);
  assert.ok(Math.max(...furrow)>5);
}

console.log(`${manifest.vocab.length} commands, authored expressions, seated pose, drag, listening, running and tail wag verified`);
