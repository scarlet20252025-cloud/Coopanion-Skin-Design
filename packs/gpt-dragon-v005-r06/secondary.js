// Local deformation fields; source images are never recut or regenerated.
const NS='http://www.w3.org/2000/svg';
let serial=0;
export function createSecondary(root,config,canvas){
 const defs=document.createElementNS(NS,'defs');root.prepend(defs);
 const channels={},prefix=`dragon-secondary-${++serial}`;
 const make=(tag,attrs)=>{const n=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);return n;};
 for(const name of ['hair','wings','tail']){
  const c=config[name],size=config.map_size,cv=document.createElement('canvas');cv.width=cv.height=size;
  const ctx=cv.getContext('2d'),im=ctx.createImageData(size,size);
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
   const px=(x+.5)*canvas[0]/size,py=(y+.5)*canvas[1]/size;let dx=0,dy=0;
   for(const[cx,cy,rx,ry,vx,vy]of c.regions){const r2=((px-cx)/rx)**2+((py-cy)/ry)**2;if(r2<1){const w=(1-r2)**3;dx+=vx*w;dy+=vy*w;}}
   const i=(y*size+x)*4;im.data[i]=128+Math.round(127*Math.max(-1,Math.min(1,dx)));im.data[i+1]=128+Math.round(127*Math.max(-1,Math.min(1,dy)));im.data[i+2]=128;im.data[i+3]=255;
  }
  ctx.putImageData(im,0,0);
  const filter=make('filter',{id:`${prefix}-${name}`,filterUnits:'userSpaceOnUse',x:-24,y:-24,width:canvas[0]+48,height:canvas[1]+48,'color-interpolation-filters':'sRGB'});
  filter.append(make('feImage',{href:cv.toDataURL(),x:0,y:0,width:canvas[0],height:canvas[1],result:'field',preserveAspectRatio:'none'}));
  // Map encoded neutral 128 exactly to 0.5, so the face and roots remain fixed.
  const linear=make('feComponentTransfer',{in:'field',result:'centered'});
  linear.append(make('feFuncR',{type:'linear',slope:255/256}),make('feFuncG',{type:'linear',slope:255/256}));filter.append(linear);
  const disp=make('feDisplacementMap',{in:'SourceGraphic',in2:'centered',scale:0,xChannelSelector:'R',yChannelSelector:'G'});filter.append(disp);defs.append(filter);
  channels[name]={x:0,v:0,disp,c,id:`${prefix}-${name}`};
 }
 function wrap(element,names){let outer=element;for(const name of names){const g=make('g',{filter:`url(#${channels[name].id})`});outer.replaceWith(g);g.append(outer);outer=g;}return outer;}
 return {wrap,step(o,dt,enabled=true){
  const walking=['walk','run'].includes(o.mode),air=o.mode==='air',sleep=['sleep','sit','wake'].includes(o.mode);
  for(const[name,s]of Object.entries(channels)){
   const phase={hair:.4,wings:1.1,tail:2.0}[name],freq=walking?(o.mode==='run'?9:6):1.7;
   const target=enabled&&!sleep?s.c.idle*Math.sin(o.t*1.7+phase)+(walking?s.c.motion*.55*Math.sin(o.t*freq+phase):0)+(air?-s.c.motion:0)+Math.max(-1,Math.min(1,(o.swing||0)/26))*s.c.motion:0;
   const h=Math.min(dt,.05)/3;for(let i=0;i<3;i++){s.v+=((target-s.x)*s.c.k-s.v*s.c.damping)*h;s.x+=s.v*h;if(Math.abs(s.x)>s.c.limit){s.x=Math.sign(s.x)*s.c.limit;s.v=0;}}
   s.disp.setAttribute('scale',String(enabled?s.x*2:0));
  }
 },values(){return Object.fromEntries(Object.entries(channels).map(([k,s])=>[k,s.x]));}};
}
