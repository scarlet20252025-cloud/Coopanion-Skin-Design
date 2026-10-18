const $=id=>document.getElementById(id),frame=$('preview');let direction=1;
async function ready(){while(!frame.contentWindow?.engineeringReady)await new Promise(r=>setTimeout(r,100));return frame.contentWindow}
const w=await ready();
function reference(){const d=frame.contentDocument,p=d.querySelector('[data-pose="standing"]');if(!p)return;let im=d.querySelector('[data-mother-reference]');if(!im){im=d.createElementNS('http://www.w3.org/2000/svg','image');for(const[k,v]of Object.entries({'data-mother-reference':'true',href:'/characters/atri-01/master.png',width:1145,height:1374,'pointer-events':'none'}))im.setAttribute(k,v);p.append(im)}im.setAttribute('opacity',Number($('reference').value)/100)}
async function pose(words,seconds){await w.setEngineeringFrame({words,seconds,direction});reference();$('status').textContent=JSON.stringify(w.engineeringState().layout)}
$('rest').onclick=()=>pose(['neutral','stand'],.05);$('wave').onclick=()=>pose(['wave'],.85);$('sit').onclick=()=>pose(['sit'],1.2);$('happy').onclick=()=>pose(['happy'],.5);$('scared').onclick=()=>pose(['scared'],.5);$('flip').onclick=()=>{direction=-direction;pose(['neutral','stand'],.05)};$('dark').onclick=()=>frame.contentDocument.getElementById('background').click();$('reference').oninput=reference;
async function capture(){
 const d=frame.contentDocument,svg=d.getElementById('root').querySelector('svg').cloneNode(true),width=d.getElementById('stage').clientWidth;
 svg.querySelectorAll('[data-mother-reference]').forEach(e=>e.remove());svg.setAttribute('xmlns','http://www.w3.org/2000/svg');svg.setAttribute('viewBox',`0 0 ${width} 800`);svg.setAttribute('width',width);svg.setAttribute('height',800);
 const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml'}));
 try{const im=new Image();im.src=url;await im.decode();const c=document.createElement('canvas');c.width=width;c.height=800;c.getContext('2d').drawImage(im,0,0);return c.toDataURL()}finally{URL.revokeObjectURL(url)}
}
$('frame').onclick=async()=>{$('one').replaceChildren();const im=new Image();im.alt='真实渲染器当前帧导出';im.src=await capture();$('one').append(im);$('status').textContent='已导出实际 SVG 渲染帧；浏览器截图接口不可用时也可检查这些实际像素。'};
$('qa').onclick=async()=>{
 $('qa').disabled=true;$('reference').value=0;reference();$('shots').replaceChildren();frame.style.width='1680px';$('status').textContent='正在宽舞台采集两个朝向的真实动作、表情和恢复……';
 const cases=[
  {id:'neutral',steps:[{word:'neutral',phase:'rest',seconds:.05,samples:[.05]}]},
  {id:'wave',steps:[{word:'wave',phase:'action',seconds:3.2,samples:[.3,.85,1.5]},{word:'stand',phase:'recovery',seconds:2.2,samples:[.4,2.2]}]},
  {id:'run',travel:true,steps:[{word:'run',phase:'action',seconds:.6,samples:[.15,.35,.6]},{word:'stand',phase:'recovery',seconds:.8,samples:[.8]}]},
  {id:'walk',travel:true,directed:true,steps:[{word:'walk',phase:'action',seconds:.8,samples:[.2,.8]},{word:'stand',phase:'recovery',seconds:.8,samples:[.8]}]},
  {id:'shake',steps:[{word:'shake',phase:'action',seconds:1.2,samples:[.2,.5,.8]},{word:'stand',phase:'recovery',seconds:.8,samples:[.8]}]},
  {id:'nod',steps:[{word:'nod',phase:'action',seconds:1.2,samples:[.2,.5,.8]},{word:'stand',phase:'recovery',seconds:.8,samples:[.8]}]},
  {id:'jump',steps:[{word:'jump',phase:'action',seconds:1.8,samples:[.2,.5,1.2]},{word:'stand',phase:'recovery',seconds:1,samples:[1]}]},
  {id:'dance',steps:[{word:'dance',phase:'action',seconds:1.6,samples:[.3,.8,1.6]},{word:'stand',phase:'recovery',seconds:1,samples:[1]}]},
  {id:'sit',steps:[{word:'sit',phase:'action',seconds:1.2,samples:[0,.1,.3,.7,1.2]},{word:'stand',phase:'recovery',seconds:2.2,samples:[.1,.3,.7,1.4,2.2]}]},
  {id:'moods',steps:[{word:'happy',phase:'happy',seconds:.5,samples:[.5]},{word:'scared',phase:'scared',seconds:.5,samples:[.5]},{word:'flustered',phase:'flustered',seconds:.5,samples:[.5]},{word:'neutral',phase:'recovery',seconds:.5,samples:[.5]}]},
  {id:'blink',steps:[{word:'neutral',phase:'blink',seconds:.9,samples:[.45,.53,.59,.66,.8]}]},
  {id:'pointer',pointer:true}
 ];
 const expected=[];for(const dir of[1,-1])for(const c of cases)if(c.pointer)for(const p of ['click','held','released','recovery'])expected.push(`${dir}:${c.id}:${p}`);else for(const step of c.steps)for(const t of step.samples)expected.push(`${dir}:${c.id}:${step.phase}:${t}`);
 try{
  const result=await w.runEngineeringQA({cases,expected});
  for(const shot of result.samples){const figure=document.createElement('figure'),caption=document.createElement('figcaption'),im=new Image();caption.textContent=shot.key;im.src=shot.png;im.alt=shot.key;figure.append(caption,im);$('shots').append(figure)}
  const {samples,...metadata}=result;metadata.samples=samples.map(({png,...s})=>s);metadata.expected=expected;metadata.kind='actual renderer PNG exports, not browser screenshots';
  $('results').textContent=JSON.stringify(metadata);$('status').textContent=`采样完成：${samples.length} 帧，契约拒绝 ${result.checks.filter(c=>!c.accepted).length} 项；仍需看图验收。`;
 }catch(e){$('status').textContent='QA失败：'+e.message}finally{const message=$('status').textContent;frame.style.width='100%';await pose(['neutral'],.05);$('status').textContent=message;$('qa').disabled=false}
};
await pose(['neutral'],.05);$('status').textContent='真实候选已载入。母版叠图只用于校验，不属于候选像素。';document.body.dataset.ready='true';
