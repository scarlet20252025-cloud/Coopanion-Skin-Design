import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url);
const read=p=>readFile(new URL(p,root));
const json=async p=>JSON.parse(await read(p));
const lock=await json('characters/original-01/production-lock.json');
const hash=createHash('sha256').update(await read(lock.active_master)).digest('hex');
if(hash!==lock.sha256)throw Error('Active master changed');
for(const name of ['validation','blink-validation']){
 const report=await json(`characters/original-01/layers-v005-r01/${name}.json`);
 if(report.master_sha256!==hash)throw Error('Report uses an older master');
 if(report.visible_pixel_mismatches||report.alpha_mismatches||report.changed_pixels_outside_eye_roi)throw Error('Visual contract failed');
}
console.log('PASS: active v005 hash, layer source version and local-expression mask reports. Animation is NOT certified by this check.');
