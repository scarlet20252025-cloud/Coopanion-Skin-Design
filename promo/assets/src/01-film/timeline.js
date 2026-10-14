import * as kit from '../../../../preview/vendor/kit/body.js';
import {createDragonBody} from '../../../../packs/gpt-dragon-v005-r25/figure.js';
const base=new URL('../../../../packs/gpt-dragon-v005-r25/',import.meta.url);
const model=await(await fetch(new URL('model.json',base))).json();
const $=id=>document.getElementById(id),clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v)),mix=(a,b,p)=>a+(b-a)*clamp(p);
const scenes=[['intro',0,4],['conversation',4,9],['touch',9,14],['actions',14,20],['seated',20,25],['outro',25,30]];
let seed=1871;Math.random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
const events=[],checks=[];
let body,sim=0,eventIndex=0,cursorPoint=null,playing=false,lastPlay=0;
async function reset(){body?.dispose();$('petMount').replaceChildren();seed=1871;body=await createDragonBody(base,{kit,model,host:{root:$('petMount'),bounds:()=>({W:800,H:880,floorY:820,S:3}),start:{x:410,facing:1,enter:'stand'},emit:(kind,detail)=>events.push({kind,detail,time:sim}),sound:()=>{}}});body.set({roam:'off',hold:999});body.place(410,1);sim=0;eventIndex=0;cursorPoint=null;}
function word(w){checks.push({time:sim,word:w,accepted:body.do(w)});}
function hit(){return body.layout().hit[0];}
const schedule=[
 [0,()=>word('wave')],
 [4,()=>word('neutral')],
 [4.55,()=>{body.talk();body.cue('cheer');}],
 [9.65,()=>{const h=hit();cursorPoint={x:h.x,y:h.y-80,t:9650};body.pointer('down',cursorPoint);}],
 [9.78,()=>body.pointer('up',{...cursorPoint,t:9780})],
 [11,()=>{const h=hit();cursorPoint={x:h.x,y:h.y-45,t:11000};body.pointer('down',cursorPoint);}],
 [13,()=>body.pointer('up',{x:410,y:185,t:13000})],
 [14,()=>{body.place(410,1);word('stand');word('wave');}],
 [16,()=>word('flap')],
 [17.8,()=>word('dance')],
 [20,()=>{body.place(410,1);word('sit');}],
 [22.15,()=>word('dizzy')],
 [25,()=>{body.place(410,1);word('stand');word('happy');}],
 [26,()=>word('wave')]
];
function at(t){
 for(const[id,start,end]of scenes){const p=t-start;const visible=t>=start&&t<end;$ (id).setAttribute('opacity',visible?clamp(p/.32):0);$(id).setAttribute('transform',`translate(${visible?mix(20,0,p/.4):0} 0)`);}
 $('bgLines').setAttribute('transform',`translate(${t*.9} 0)`);
 $('introRule').setAttribute('stroke-dasharray','670');$('introRule').setAttribute('stroke-dashoffset',670*(1-clamp((t-.8)/.6)));
 $('progress').setAttribute('stroke-dasharray','1680');$('progress').setAttribute('stroke-dashoffset',1680*(1-t/30));
 const talking=t>=4&&t<9;$('desktop').setAttribute('opacity',talking?clamp((t-4)/.3):0);$('bubble').setAttribute('opacity',talking?clamp((t-4.5)/.3):0);
 $('touchTitle').textContent=t<11?'点一下，回应你。':'提起时，也会挣扎。';$('touchSub').textContent=t<11?'呆毛轻晃，小情绪跟着冒出来。':'慌张的表情，配上快速振翅。';
 $('seatTitle').textContent=t<22.15?'坐下来，歇一会儿。':'晕乎，也有小情绪。';
 let px=1030,py=120,scale=1;
 if(talking){scale=.68;px=1085;py=308;}
 if(t>=20&&t<25){py=105;}
 $('petFrame').setAttribute('transform',`matrix(${scale} 0 0 ${scale} ${px-1030*scale} ${py-120*scale})`);
 for(let i=0;i<3;i++){const selected=t>=14&&t<20&&i===(t<16?0:t<17.8?1:2);$('chip'+i).querySelector('rect').setAttribute('fill',selected?'#b79cde':'#30263e');$('chip'+i).querySelector('text').style.fill=selected?'#21172d':'#f0edf8';}
 const cur=t>=9.25&&t<13.35;$('cursor').setAttribute('opacity',cur?1:0);
 if(cur){const h=hit();let x=h.x,y=h.y-80;if(t<9.65){x=mix(730,x,(t-9.25)/.4);y=mix(560,y,(t-9.25)/.4);}else if(t>=11){x=410;y=mix(330,185,(t-11)/.6);}
  $('cursor').setAttribute('transform',`translate(${1030+x} ${120+y})`);$('clickRing').setAttribute('cx',1030+x);$('clickRing').setAttribute('cy',120+y);}
 const pulse=clamp((t-9.65)/.35);$('clickRing').setAttribute('r',18+24*pulse);$('clickRing').setAttribute('opacity',t>=9.65&&t<10?1-pulse:0);
 $('bottomLabel').textContent=t>=25?'Asryto · GPT 龙娘 · 2026':'Coopanion 桌宠功能演示';
}
window.renderAt=async time=>{
 if(time<sim-.001)await reset();
 while(sim<time-1e-6){const next=Math.min(time,sim+1/60);while(eventIndex<schedule.length&&schedule[eventIndex][0]<=next+1e-7){schedule[eventIndex++][1]();}
  if(next>=11.03&&next<13){body.pointer('move',{x:410,y:mix(330,185,(next-11)/.6),t:next*1000});}
  body.step(next-sim);sim=next;
 }
 if(eventIndex===0&&time===0){schedule[eventIndex++][1]();body.step(0);}
 at(time);window.promoState={time,layout:body.layout(),visual:body.visualState(),secondary:body.secondaryState(),checks,events};
};
await reset();await window.renderAt(0);window.promoReady=true;
if(new URLSearchParams(location.search).has('review')){$('reviewControls').style.display='block';$('reviewSeek').onclick=()=>{playing=false;window.renderAt(Number($('reviewTime').value));};$('reviewPlay').onclick=()=>{playing=!playing;lastPlay=performance.now();};const frame=async now=>{if(playing){const t=sim+(now-lastPlay)/1000;if(t<30)await window.renderAt(t);else playing=false;}lastPlay=now;requestAnimationFrame(frame);};requestAnimationFrame(frame);}
