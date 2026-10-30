import {createRig} from '/preview/vendor/kit/rig.js';
const W=1145,H=1374,box=[0,0,W,H],q=s=>document.querySelector(s);
const files={fill:'pair-rear-fill.png',far:'far-pony-complete.png',near:'near-pony-complete.png',foreground:'pair-remainder.png',mother:'mother-source-matte.png'};
const imgs=Object.fromEntries(await Promise.all(Object.entries(files).map(async([k,file])=>{const im=new Image();im.src=file;await im.decode();return[k,im]})));
const model={view:box,deformers:{near:{kind:'warp',rect:[0,430,W,910]},far:{kind:'warp',rect:[0,590,W,940]}},parts:Object.keys(files).filter(k=>k!=='mother').map((id,z)=>({id,tex:id,z,box,parent:['near','far'].includes(id)?id:null,grid:['near','far'].includes(id)?[8,100]:[1,1]}))};
const rig=createRig(q('#rig'),model);for(const[k,img]of Object.entries(imgs))rig.upload(k,img);
const ctx=q('#reference').getContext('2d');let amount=0,playing=false,view=box;
const ease=x=>x*x*(3-2*x);
function draw(){rig.render({near:{fn:(_u,v)=>[-amount*ease(v),0]},far:{fn:(_u,v)=>[amount*ease(v),0]}});ctx.clearRect(0,0,W,H);ctx.drawImage(imgs.mother,...[view[0],view[1],view[2]-view[0],view[3]-view[1]],0,0,W,H);q('#status').textContent=`源图端部位移 ${amount.toFixed(2)} px；此页为失败定位证据，不是交付验收。`;}
q('#rest').onclick=()=>{playing=false;amount=0;draw()};q('#out').onclick=()=>{playing=false;amount=6;draw()};q('#in').onclick=()=>{playing=false;amount=-6;draw()};q('#play').onclick=()=>{playing=!playing};
q('#bg').onclick=()=>document.body.classList.toggle('dark');q('#flip').onclick=()=>document.body.classList.toggle('flip');
q('#view').onchange=e=>{view={full:box,near:[120,690,350,980],far:[810,710,1020,980],root:[280,240,460,460]}[e.target.value];rig.setView(view);draw()};
function step(t){if(playing){amount=6*Math.sin(t/900);draw()}requestAnimationFrame(step)}draw();requestAnimationFrame(step);
window.addEventListener('pagehide',()=>rig.dispose());document.body.dataset.ready='true';
