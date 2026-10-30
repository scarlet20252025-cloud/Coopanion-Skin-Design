import fs from 'node:fs';
import assert from 'node:assert/strict';
import {WAG,createWhaleTailDriver} from '../packs/gpt-dragon-v005-r11/whale-tail-driver.js';
const source=fs.readFileSync(new URL('../preview/vendor/whale-figure.upstream.js',import.meta.url),'utf8');
const block=source.match(/const MOOD = \{([\s\S]*?)\n  \};/)[1];
const upstream=Object.fromEntries([...block.matchAll(/(\w+):\s*\[([^,]+),\s*([^\]]+)\]/g)].map(m=>[m[1],Number(m[3])]));
assert.deepEqual(WAG,upstream,'Every official mood tail amplitude must be represented exactly');
const cases=[];
for(const face of [...Object.keys(upstream),'working']){
 const d=createWhaleTailDriver(),values=[];
 for(let i=0;i<240;i++)values.push(d.step({t:i/60,face,mode:face==='sleep'?'sleep':'idle',sit:0,swing:0}));
 assert(values.every(v=>Number.isFinite(v.tail)&&Number.isFinite(v.bend)));
 const last=values.at(-1);assert(Math.abs(last.wag-(upstream[face==='working'?'thinking':face]))<.001);
 cases.push({face,amplitude:last.wag,min:Math.min(...values.map(v=>v.tail)),max:Math.max(...values.map(v=>v.tail))});
}
for(const swing of [-100,100]){const d=createWhaleTailDriver();let s;for(let i=0;i<600;i++)s=d.step({t:i/60,face:'dragged',mode:'drag',swing,sit:0});assert(Math.abs(s.spring)<=32&&Math.sign(s.spring)===Math.sign(swing));}
const seated=createWhaleTailDriver();let s;for(let i=0;i<180;i++)s=seated.step({t:i/60,face:'neutral',mode:'sit',sit:1,swing:0});assert(Math.abs(s.rotation-s.tail+10)<.001);
const report={upstream:'91293b3',official_moods:Object.keys(upstream).length,working_alias:'thinking',seated_offset:true,drag_spring_bounds:true,cases};
fs.writeFileSync(new URL('../characters/original-01/rig-v005-r11/wing-mapping-check.json',import.meta.url),JSON.stringify(report,null,2));
console.log(`PASS: ${report.official_moods} official mood mappings + working alias, seated offset and drag bounds`);
