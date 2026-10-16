 function buildFace(pose,parent){
  // 2026-10-16 user instruction: "绝大多数坐下的表情都有问题,复用跟站立时一样的表情". The seated set is a
  // separate redraw - its eye art has the fringe baked across the pupil - so the seated face is built
  // from the SAME art and the SAME rig as the standing one, and the group carries the similarity that
  // fits the standing eye pair onto the seated eye pair (FX_POSE_FIT, derived from the two rigs).
  const rig=model.expression_rig.standing,g=n('g',{'data-face':pose}),eyes=[];parent.append(g);
  const fit=FX_POSE_FIT[pose];
  if(fit)g.setAttribute('transform',`matrix(${fit.map(v=>Math.round(v*1e5)/1e5).join(' ')})`);
  const defs=n('defs');g.append(defs);
  const foreheadId=`${clipPrefix}-${pose}-forehead`,forehead=n('mask',{id:foreheadId,maskUnits:'userSpaceOnUse',x:0,y:0,width:W,height:H,style:'mask-type:alpha'});
  const foreheadPart=parts.get('brow-mask');forehead.append(n('image',{width:W,height:H,href:textures.get(foreheadPart.file)}));defs.append(forehead);
  for(let i=0;i<2;i++){const id='eye-'+i;
   const source=n('image',{width:W,height:H,href:textures.get(parts.get(id).file)});g.append(source);
   const happyId=`closed-happy-${i}`;
   const happy=n('image',{width:W,height:H,href:textures.get(parts.get(happyId).file)});g.append(happy);
   // 2026-10-17 user correction: the old crop destroyed the lash tips and the double-lid line, it was not a
   // layer problem. happy-arc-* (pure-generation/new-art/, restored from art-source/closed-happy.png by
   // restore-smiling-eyes.py) is used for the smiling face. The old single arc stays for the wink's closed eye.
   const arc=n('image',{width:W,height:H,href:textures.get(parts.get(`happy-arc-${i}`).file),'data-eye-arc':i});
   g.append(arc);eyes.push({source,happy,arc});}
  // Each redrawn pair uses one registered posed-face source. No separate eye
  // translations, vertical iris clipping or generic heart/spiral/chevron paths.
  const eyeArt={};
  for(const variant of ['half','late','rest','love','dizzy','pinch']){
   const part=parts.get('eye-pair-'+variant);
   eyeArt[variant]=n('image',{width:W,height:H,href:textures.get(part.file),'data-eye-art':variant});g.append(eyeArt[variant]);
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
   eyes[i].happy.setAttribute('display',selected==='wink'&&i===1?'inline':'none');
   if(eyes[i].arc)eyes[i].arc.setAttribute('display',selected==='happy'?'inline':'none');
   // 2026-10-16 user feedback: "害羞没有变化". The official face table shrinks the eyes and pulls them in
   // and down for shy (ring rx 13 / ry 12 with dx -3, dy 5 against the neutral 16/16), so the accepted
   // open-eye art is scaled and shifted the same way instead of sitting unchanged.
   const [ex,ey]=rig.eyes[i];
   const shy=f==='shy',sy=shy?.82:f==='scared'?1.10:f==='sad'?.90:f==='worried'?.96:1,sx=shy?.90:f==='scared'?1.035:1;
   const ox=shy?(i===0?5:-5):0,oy=shy?7:0;
   eyes[i].source.setAttribute('transform',selected==='open'&&(sy!==1||ox||oy)?`translate(${ex+ox} ${ey+oy}) scale(${sx} ${sy}) translate(${-ex} ${-ey})`:'');
  }
  for(const [variant,image]of Object.entries(eyeArt))image.setAttribute('display',selected===variant?'inline':'none');
  state.currentEyeArt=selected;
  const pinch=selected==='pinch';
  // the face is always drawn in the standing frame now, so both poses use the standing brow tables
  const baseBrows=[[518,388,550,380,582,393],[680,386,711,357,738,349]];
  const pinchBrows=[[499,426,552,413,590,393],[688,390,720,405,747,397]];
  for(let i=0;i<2;i++){
   const [x0,y0,x1,y1,x2,y2]=(pinch?pinchBrows:baseBrows)[i];
   // 2026-10-16 user feedback: "开心的笑脸不是很自然". The smiling arcs ARE the eyes; the official face
   // table draws brows only for sad/worried/scared/angry/determined, never for happy - so the two extra
   // dark strokes above the arcs (four curves on one face) go away while the arcs are showing.
   brows[i].setAttribute('display',['happy','wink'].includes(selected)?'none':'inline');
   let outer=0,inner=0,arch=0;
   // 2026-10-16: travels roughly doubled, and 大哭 joins the sad group because the official whale face
   // table gives cry `brows: 'sad'`. sad/worried/cry lift the inner ends, angry/determined drive them
   // down towards the nose, both with the outer end doing the opposite.
   if(['sad','worried','confused','cry'].includes(f)){outer=22;inner=-12;arch=4;}
   else if(f==='scared'){outer=20;inner=-20;arch=-2;}
   else if(['angry','determined'].includes(f)){outer=-12;inner=26;arch=0;}
   else if(['happy','excited','surprised'].includes(f)){outer=-9;inner=-10;arch=-14;}
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
   // 2026-10-16 user feedback: 开心 went through three mouths - a 2.8px stroke (read as a hairline
   // scratch), a big open crescent (too heavy) and the official small oval ("别用这张嘴"). This is the
   // fourth: a smile with real weight but no wide开口 - a filled lens, mid-width, no tongue.
   happy:['M-12 -2Q0 6 12 -4Q0 12 -12 -2Z','#b8737d',''],
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
  // 2026-10-16 user feedback: "大哭丑更重要的原因是嘴型". The official whale's face table maps cry to its
  // surprised mouth at .8 scale (MOUTH.cry = ['surprised_mouth', .8]) - a wail is one small open oval,
  // not the wavy blob this table used to draw for cry (entry removed, it is unreachable from here on).
  const key=f==='bowing'?'happy':f==='squeeze'?'sleep':f==='cry'?'surprised':styles[f]?f:'neutral',mouthScale=f==='cry'?.8:1;
  const [outline,fill,inner]=styles[key];
  mouth.setAttribute('data-mouth-style',pinch?'source-pinch':key);
  mouth.setAttribute('transform',`translate(${x} ${y}) rotate(-7) scale(${mouthScale} ${mouthScale*(1+Math.min(.18,(o.talk||0)*.18))})`);
  lip.setAttribute('d',outline);lip.setAttribute('fill',fill);
  tongue.setAttribute('d',inner);tongue.setAttribute('display',inner?'inline':'none');

 }
