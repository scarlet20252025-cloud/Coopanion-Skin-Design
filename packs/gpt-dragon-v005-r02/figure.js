// GPT Dragon v005-r02: original-coordinate layered prototype.
// Behaviour comes from host kit; no whale facial geometry is used.
const NS='http://www.w3.org/2000/svg';
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export async function createDragonBody(base,opts){
 const model=opts.model||await(await fetch(new URL('model.json',base))).json();
 const asset=opts.asset||(p=>new URL(p,base));
 const load=opts.loadImage||(url=>new Promise((ok,bad)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=bad;im.src=url;}));
 const names=['hair-covered-underpaint','body-covered-underpaint','head-open','head-half','head-closed','sitting-open','sitting-half','sitting-closed'];
 const textures={};
 await Promise.all(names.map(async name=>{
  const im=await load(asset('tex/'+name+'.png'));
  const cv=document.createElement('canvas');cv.width=im.naturalWidth||im.width;cv.height=im.naturalHeight||im.height;cv.getContext('2d').drawImage(im,0,0);
  textures[name]=cv.toDataURL('image/png');
 }));
 const S=.2,X=128-650*S,Y=256-model.standing_feet_y*S;
 let mounted=null,root,back,body,head,sitting,headGroup,backGroup,prevEye='',prevSit=false;
 function node(tag,attrs={}){const n=document.createElementNS(NS,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);return n;}
 function picture(name){return node('image',{href:textures[name],x:0,y:0,width:model.canvas[0],height:model.canvas[1]});}
 function mount(g){
  g.replaceChildren();root=node('g');root.setAttribute('transform',`translate(${X} ${Y}) scale(${S})`);g.append(root);
  backGroup=node('g');back=picture('hair-covered-underpaint');backGroup.append(back);root.append(backGroup);
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
   const seated=o.sit>.5;
   const shut=['sleep','bowing','cry'].includes(o.face)||o.drowse>.75;
   const closure=shut?1:Math.max(o.blink||0,o.eyeClose||0);
   const eye=closure>.75?'closed':closure>.25?'half':'open';
   if(eye!==prevEye||seated!==prevSit){head.setAttribute('href',textures['head-'+eye]);sitting.setAttribute('href',textures['sitting-'+eye]);prevEye=eye;prevSit=seated;}
   backGroup.setAttribute('visibility',seated?'hidden':'visible');body.setAttribute('visibility',seated?'hidden':'visible');headGroup.setAttribute('visibility',seated?'hidden':'visible');sitting.setAttribute('visibility',seated?'visible':'hidden');
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
 return {...native,words:supported,do(word){return supported.includes(word)?native.do(word):false;}};
}
