import {readFile,readdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {KIT_EXPRESSIONS,KIT_MOTIONS} from '../preview/vendor/kit/body.js';
const root=new URL('../',import.meta.url),json=async p=>JSON.parse(await readFile(new URL(p,root)));
const lock=await json('characters/original-01/production-lock.json'),model=await json('packs/gpt-dragon-v005-r07/model.json'),manifest=await json('packs/gpt-dragon-v005-r07/figure.json');
assert.equal(createHash('sha256').update(await readFile(new URL(lock.active_master,root))).digest('hex'),lock.sha256);
assert.equal(model.master_sha256,lock.sha256);
assert.equal(model.leg_rig.elasticity.idle_strength,.7);assert.equal(model.leg_rig.elasticity.strength,.65);
assert.deepEqual(manifest.vocab.map(x=>x.id).sort(),[...KIT_EXPRESSIONS,...KIT_MOTIONS,'working','listening'].sort());
for(const v of manifest.vocab){assert(v.seconds>0&&Number.isFinite(v.seconds));if(['sit','sleep'].includes(v.id))assert.equal(v.lasting,true);}
let preserved=0;for(const name of await readdir(new URL('packs/gpt-dragon-v005-r07/tex/',root))){const a=await readFile(new URL('packs/gpt-dragon-v005-r07/tex/'+name,root)),b=await readFile(new URL('packs/gpt-dragon-v005-r06/tex/'+name,root));assert(a.equals(b),name+' changed');preserved++;}
console.log(JSON.stringify({version:manifest.version,master:'passed',vocab:manifest.vocab.length,spring:'preserved',textures_unchanged:preserved,lasting_states:'passed'}));
