// Generic rigid-layer starter. All geometry/art belongs to model.json, never to GPT Dragon.
export async function createLayeredBody(base,opts){
 const model=opts.model,NS='http://www.w3.org/2000/svg',textures=new Map(),nodes=new Map();
 const registration=model.part_registration;
 const load=opts.loadImage||(url=>new Promise((ok,bad)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=bad;im.src=url;}));
 for(const file of new Set(model.parts.flatMap(p=>[p.file,...Object.values(p.variants||{})]))){
  const im=await load(opts.asset?opts.asset(file):new URL(file,base));
  const canvas=document.createElement('canvas');canvas.width=im.naturalWidth||im.width;canvas.height=im.naturalHeight||im.height;canvas.getContext('2d').drawImage(im,0,0);textures.set(file,canvas.toDataURL());
 }
 const node=(tag,attrs={})=>{const el=document.createElementNS(NS,tag);for(const [k,v]of Object.entries(attrs))el.setAttribute(k,v);return el;};
 let mounted,root,dizzy=false,pose='standing',lastFace='neutral';
 const [width,height]=model.canvas,s=model.logo_scale,tx=128-model.center_x*s,ty=256-model.feet_y*s;
 const convert=([x,y])=>[tx+x*s,ty+y*s];
 const figure={gestures:['wave','flap'],colors:{z:model.accent},
  extent:[...convert(model.bounds.slice(0,2)),...convert(model.bounds.slice(2))],
  hits:model.hits.map(([x,y,r])=>[...convert([x,y]),r*s]),
  anchors:Object.fromEntries(Object.entries(model.anchors).map(([k,v])=>[k,[...convert(v),...v.slice(2).map(n=>n*s)]])),
  draw(g,face,o){
   if(mounted!==g){g.replaceChildren();root=node('g',{transform:`translate(${tx} ${ty}) scale(${s})`});g.append(root);nodes.clear();
    for(const part of model.parts){const joint=node('g',{'data-part':part.id}),image=node('image',{width,height,href:textures.get(part.file)});joint.append(image);root.append(joint);nodes.set(part.id,{joint,image});}mounted=g;
   }
   if(o.mode==='dizzy')dizzy=true;else if(o.sit<.02||o.mode==='sit'||o.mode==='sleep')dizzy=false;
   pose=o.sit>.5?(dizzy?'dizzy':'seated'):'standing';lastFace=o.mode==='drag'?'flustered':o.face;
   const wave=o.gesture?.kind==='wave',k=wave?o.gesture.k:0,env=wave?Math.sin(Math.PI*k):0;
   for(const part of [...model.parts].sort((a,b)=>(wave?(a.wave_z??a.z):a.z)-(wave?(b.wave_z??b.z):b.z))){
    const {joint,image}=nodes.get(part.id);root.append(joint);joint.setAttribute('visibility',part.poses.includes(pose)?'visible':'hidden');
    let angle=0;
    if(part.role==='wave-arm')angle=part.motion.degrees*env+part.motion.swing*Math.sin(k*Math.PI*6)*env;
    if(part.role==='wing')angle=part.motion.degrees*Math.sin(o.t*part.motion.hz*2*Math.PI)*(lastFace==='happy'||o.mode==='drag'?1:.15);
    if(part.role==='leg'&&['walk','run'].includes(o.mode))angle=part.motion.degrees*Math.sin(o.t*part.motion.hz*2*Math.PI+(part.motion.phase||0));
    const [x,y]=part.pivot;
    joint.setAttribute('transform',`rotate(${angle} ${x} ${y}) matrix(${registration[part.id].join(' ')})`);
    const variant=part.variants?.[lastFace]||(o.blink>.5?part.variants?.blink:null)||part.file;image.setAttribute('href',textures.get(variant));
   }
  },dispose(){mounted=null;nodes.clear();}
 };
 const native=opts.kit.createBody(opts.host,{figure});
 return {...native,visualState:()=>({face:lastFace,pose}),words:model.words,do:word=>model.words.includes(word)?native.do(word):false};
}
