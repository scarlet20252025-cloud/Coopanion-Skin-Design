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
const r02=await json('characters/original-01/rig-v005-r02/geometry.json');
if(r02.master_sha256!==hash||r02.rest_pixel_mismatches||r02.outside_eye_changes||r02.independent_scaling)throw Error('r02 geometry/source contract failed');
const pack=await json('packs/gpt-dragon-v005-r02/model.json');
if(pack.master_sha256!==hash)throw Error('Pack uses another master');
const r03=await json('packs/gpt-dragon-v005-r03/model.json');
if(r03.master_sha256!==hash||r03.leg_checks.master!==hash||r03.leg_checks.rest_mismatch)throw Error('r03 source/rest contract failed');
const cfg=await json('characters/original-01/rig-v005-r03/leg-config.json');
if(JSON.stringify(cfg)!==JSON.stringify(r03.leg_rig))throw Error('Rebuild r03 after editing leg config');
console.log('PASS: active v005 hash, r01/r02/r03 source versions, rest geometry, eye masks and leg config. This is not desktop-client certification.');
const r04=await json('packs/gpt-dragon-v005-r04/model.json');
if(r04.master_sha256!==hash||r04.arm_checks.rest_mismatches)throw Error('r04 source/rest contract failed');
if(JSON.stringify(r04.leg_rig.elasticity)!==JSON.stringify(r03.leg_rig.elasticity))throw Error('Accepted spring settings drifted');
if(JSON.stringify(r04.motion_rig)!==JSON.stringify(await json('characters/original-01/rig-v005-r04/motion-config.json')))throw Error('Rebuild r04 motion parameters');
console.log('PASS: r04 arm rest contract, motion config and inherited elasticity.');
