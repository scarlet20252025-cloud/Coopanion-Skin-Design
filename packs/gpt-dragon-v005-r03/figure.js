// GPT Dragon v005-r02: original-coordinate layered prototype.
// Behaviour comes from host kit; no whale facial geometry is used.
const NS='http://www.w3.org/2000/svg';
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const textureCache=new Map(); // One page load; reset/seek never re-encodes unchanged art.
export async function createDragonBody(base,opts){
 const model=opts.model||await(await fetch(new URL('model.json',base))).json();
 const asset=opts.asset||(p=>new URL(p,base));
 const load=opts.loadImage||(url=>new Promise((ok,bad)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=bad;im.src=url;}));
 const names=['hair-covered-underpaint','body-covered-underpaint','head-open','head-half','head-closed','sitting-open','sitting-half','sitting-closed','leg-left','leg-right','body-without-legs','skirt-hole-fill'];
 const textures={};
 await Promise.all(names.map(async name=>{
  const url=asset('tex/'+name+'.png'),key=String(url);
  if(textureCache.has(key)){textures[name]=textureCache.get(key);return;}
  const im=await load(url);
  const cv=document.createElement('canvas');cv.width=im.naturalWidth||im.width;cv.height=im.naturalHeight||im.height;cv.getContext('2d').drawImage(im,0,0);
  textures[name]=cv.toDataURL('image/png');
  textureCache.set(key,textures[name]);
 }));
 const S=.2,X=128-650*S,Y=256-model.standing_feet_y*S;
 let mounted=null,root,back,body,head,sitting,headGroup,backGroup,prevEye='',prevSit=false;
 let articulation,fill,front,legNodes=[],lastT=0,airK=0,groundK=0,jumpWord='jump';
 const cfg=model.leg_rig;
 function node(tag,attrs={}){const n=document.createElementNS(NS,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);return n;}
 function picture(name){return node('image',{href:textures[name],x:0,y:0,width:model.canvas[0],height:model.canvas[1]});}
 function mount(g){
  g.replaceChildren();root=node('g');root.setAttribute('transform',`translate(${X} ${Y}) scale(${S})`);g.append(root);
  backGroup=node('g');back=picture('hair-covered-underpaint');backGroup.append(back);root.append(backGroup);
  articulation=node('g');fill=picture('skirt-hole-fill');articulation.append(fill);
  legNodes=cfg.legs.map(l=>{const group=node('g');group.append(picture('leg-'+l.id));articulation.append(group);return group;});
  front=picture('body-without-legs');articulation.append(front);root.append(articulation);
  body=picture('body-covered-underpaint');root.append(body);
  headGroup=node('g');head=picture('head-open');headGroup.append(head);root.append(headGroup);
  sitting=picture('sitting-open');sitting.setAttribute('visibility','hidden');root.append(sitting);mounted=g;prevEye='';
 }
 const figure={
  colors:{z:'#a18acb'},gestures:['nod','shake'],
  extent:[45,25,225,257],hits:[[132,106,69],[131,197,45],[133,243,25]],
  anchors:{gaze:[143,116],bubble:[130,20],z:[199,55],tear:[160,129],hearts:[100,176,70]},
  draw(g,fc,o){
   if(mounted!==g)mount(g);
   // Keep native trajectory/landing timing, limit whole-face squash for this art.
   // Apply about the foot anchor so the character never slides vertically.
   const scales=g.getAttribute('transform')?.match(/scale\(([-\d.]+)\s+([-\d.]+)\)/);
   let cx=1,cy=1;
   if(scales&&['crouch','air','land'].includes(o.mode)&&Math.abs(o.facing)>.1){
    const hostScale=opts.host.bounds().S,sx=Number(scales[1])/(hostScale*o.facing),sy=Number(scales[2])/hostScale;
    if(sx>0&&sy>0){cx=clamp(sx,.97,1.03)/sx;cy=clamp(sy,.98,1.02)/sy;}
   }
   root.setAttribute('transform',`translate(128 256) scale(${cx} ${cy}) translate(-128 -256) translate(${X} ${Y}) scale(${S})`);
   const dt=Math.max(0,Math.min(.05,o.t-lastT));lastT=o.t;
   const smooth=x=>{x=clamp(x,0,1);return x*x*(3-2*x);};
   const duration=2*cfg[jumpWord].velocity/cfg[jumpWord].gravity;
   const airTarget=o.mode==='air'?1-smooth((o.modeT-(duration-cfg.timing.extend_before_landing_seconds))/cfg.timing.extend_before_landing_seconds):0;
   const groundTarget=o.mode==='crouch'?smooth(o.modeT/cfg.timing.crouch_seconds):o.mode==='land'?1-smooth(o.modeT/cfg.timing.land_seconds):0;
   airK+=(airTarget-airK)*(1-Math.exp(-dt*30));groundK+=(groundTarget-groundK)*(1-Math.exp(-dt*35));
   const active=airK>.002||groundK>.002;
   const drop=groundK*(o.mode==='land'?cfg.landing_body_drop_px:cfg.crouch_body_drop_px);
   // Translate the torso; plant each sole during compression. Never scale the legs.
   root.setAttribute('transform',root.getAttribute('transform')+` translate(0 ${drop})`);
   cfg.legs.forEach((leg,i)=>{
    const angle=leg.air_angle*airK+leg.crouch_angle*groundK,rad=angle*Math.PI/180,[px,py]=leg.pivot;
    const sole=i?[742,1188]:[597,1198],dx=sole[0]-px,dy=sole[1]-py;
    const tx=-((Math.cos(rad)-1)*dx-Math.sin(rad)*dy)*groundK;
    const ty=-leg.air_lift*airK-((Math.sin(rad)*dx+(Math.cos(rad)-1)*dy)*groundK)-drop;
    legNodes[i].setAttribute('transform',`translate(${tx} ${ty}) rotate(${angle} ${px} ${py})`);
   });
   const seated=o.sit>.5;
   const shut=['sleep','bowing','cry'].includes(o.face)||o.drowse>.75;
   const closure=shut?1:Math.max(o.blink||0,o.eyeClose||0);
   const eye=closure>.75?'closed':closure>.25?'half':'open';
   if(eye!==prevEye||seated!==prevSit){head.setAttribute('href',textures['head-'+eye]);sitting.setAttribute('href',textures['sitting-'+eye]);prevEye=eye;prevSit=seated;}
   backGroup.setAttribute('visibility',seated?'hidden':'visible');body.setAttribute('visibility',seated?'hidden':'visible');headGroup.setAttribute('visibility',seated?'hidden':'visible');sitting.setAttribute('visibility',seated?'visible':'hidden');
   articulation.setAttribute('visibility',!seated&&active?'visible':'hidden');
   body.setAttribute('visibility',seated||active?'hidden':'visible');
   // Seated art has its own shorter silhouette. Align feet, never squash the face.
   sitting.setAttribute('transform',`translate(0 ${model.standing_feet_y-model.sitting_feet_y})`);
   const gesture=o.gesture;
   let angle=clamp((o.look?.[0]||0)*.16,-1.2,1.2),dy=clamp((o.look?.[1]||0)*.35,-2,2);
   if(gesture?.kind==='nod')dy+=3*Math.sin(gesture.k*Math.PI*2);
   if(gesture?.kind==='shake')angle+=2.3*Math.sin(gesture.k*Math.PI*4);
   angle=clamp(angle,-model.rotation_limit_degrees,model.rotation_limit_degrees);dy=clamp(dy,-3,3);
   const [px,py]=model.head_pivot,t=`translate(0 ${dy}) rotate(${angle} ${px} ${py})`;
   headGroup.setAttribute('transform',t);backGroup.setAttribute('transform',t);
  },
  dispose(){mounted=null;},
 };
 const native=opts.kit.createBody(opts.host,{figure});
 // Do not expose unsupported expressions/limb motions just because kit knows them.
 const supported=['neutral','stand','sit','sleep','nod','shake','jump','hop','turn'];
 return {...native,words:supported,do(word){const ok=supported.includes(word)?native.do(word):false;if(ok&&['jump','hop'].includes(word))jumpWord=word;return ok;}};
}
