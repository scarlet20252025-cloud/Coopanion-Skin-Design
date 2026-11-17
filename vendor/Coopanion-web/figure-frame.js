/**
 * Inside the sandboxed figure frame: loads a figure pack's module and runs its body.
 *
 * The frame is an opaque origin with no network access (the server's CSP for `/figure-frame`);
 * it gets scripts and images from the pet server and everything else from the page that holds
 * it (`body-host.js`), by postMessage. The body is the pack's own: it walks, falls, is carried,
 * makes faces and draws itself; the page only hears what it reports and asks it to do things.
 *
 * The contract a pack implements (api 2): its module exports a factory, called as
 * `factory(base, { model, scheme, kit, loadImage, asset, host })`, that resolves to a body:
 *
 * - `host`: `root` (the element to draw in, filling the stage), `bounds()` ({ W, H, floorY, S } in stage
 *   pixels: the floor's height and the size the body is drawn at, 1 logo unit = S pixels, the body
 *   inside a 256-unit square), `emit(kind, detail)`, `sound(name, kind, ...args)` and `start`
 *   ({ x, facing, enter, skin }).
 * - `kit`: web/kit/body.js (createBody builds a whole body around a figure that only draws; createRig).
 * - the body: `step(dt)` advances and draws one frame; `layout()` says where it is ({ x, facing, mode,
 *   busy, moving, pressing, cursor, box, hit, bubble, side }, see the kit's `layout`); `resize()` takes new
 *   bounds (`set({ bounds })` from the page changes what `host.bounds()` returns, then calls it); `do(word)`, `walk(x, run, id)`, `stopWalk(id)`, `pointer(type, p)`, `drop(p)`, `shift(dx, dy)`, `place(x, facing)`,
 *   `set(state)`, `cue(kind)`, `talk()`, `setScheme(id, { fade })`, `z` (the colour of its sleep z's),
 *   `words` (every word `do` knows; the kit's bodies list theirs, and the manifest's words not in it are
 *   kept from the bot) and `dispose()`. Only `step`, `layout` and `do` are required.
 * - events (`emit`): `arrived` and `interrupted` ({ walkId, x, by }) for `walk`, `done` ({ word }) for a word
 *   that ends on its own, `touch` ({ kind: poke | pet | grab | drop | throw | crash, ... }), `mode` ({ mode }).
 *
 * Messages in: `init { entry, export, base, model, scheme, start, theme, bounds, language }` (the app language,
 * for the frame's own error messages), then `tick { dt }`
 * once a frame and the calls above by name. Out: `loaded`, `ready { z, words }`, `frame { layout, events: [{ kind,
 * detail }], sounds: [{ name, kind, args }], z }` after each tick, `scheme { seq, z }`, and `error { message }`
 * once, after which it stops.
 */
import * as kit from './kit/body.js';
import { t, useLanguage } from './i18n.js';

const root = document.getElementById('root');
let body = null, dead = false, bounds = { W: 0, H: 0, floorY: 0, S: .42 };
let events = [], sounds = [];
const post = (m) => parent.postMessage(m, '*');
function fail(err) {
  if (dead) return;
  dead = true;
  post({ t: 'error', message: String(err?.message ?? err).slice(0, 300) });
}
addEventListener('error', (e) => fail(e.error ?? e.message));
addEventListener('unhandledrejection', (e) => fail(e.reason));

function loadImage(url) {
  return new Promise((ok, bad) => {
    const im = new Image();
    im.crossOrigin = 'anonymous';
    im.onload = () => ok(im);
    im.onerror = () => bad(new Error(t('figure.imageFailed', { url })));
    im.src = String(url);
  });
}

const host = {
  root,
  bounds: () => bounds,
  emit: (kind, detail) => events.push({ kind, detail }),
  sound: (name, kind, ...args) => sounds.push({ name, kind, args }),
};

addEventListener('message', async (e) => {
  if (e.source !== parent || dead) return;
  const m = e.data || {};
  try {
    if (m.t === 'init') {
      bounds = m.bounds;
      document.documentElement.dataset.theme = m.theme;
      if (typeof m.language === 'string') await useLanguage(m.language);
      const mod = await import(m.entry);
      const make = mod[m.export];
      if (typeof make !== 'function') throw new Error(t('figure.notFunction', { name: m.export }));
      const base = new URL(m.base);
      body = await make(base, { model: m.model ?? undefined, scheme: m.scheme, kit, loadImage, asset: (p) => new URL(p, base), host: { ...host, start: m.start } });
      for (const fn of ['step', 'layout', 'do']) if (typeof body?.[fn] !== 'function') throw new Error(t('figure.missingMethod', { name: fn }));
      post({ t: 'ready', z: body.z ?? null, words: Array.isArray(body.words) ? body.words.filter((w) => typeof w === 'string') : null });
    } else if (!body) {
      // calls that come before the body is ready have nothing to act on
    } else if (m.t === 'tick') {
      body.step(m.dt);
      post({ t: 'frame', layout: body.layout(), events, sounds, z: body.z ?? null });
      events = []; sounds = [];
    } else if (m.t === 'scheme') {
      // the fade starts at the body's next frame: the page's clock is not the body's
      await body.setScheme?.(m.id, { fade: m.fade });
      post({ t: 'scheme', seq: m.seq, z: body.z ?? null });
    } else if (m.t === 'do') body.do(m.word);
    else if (m.t === 'walk') { if (!body.walk?.(m.x, m.run, m.id)) events.push({ kind: 'interrupted', detail: { walkId: m.id, by: 'busy' } }); }
    else if (m.t === 'stop-walk') body.stopWalk?.(m.id);
    else if (m.t === 'pointer') body.pointer?.(m.type, m.p);
    else if (m.t === 'drop') body.drop?.(m.p);
    else if (m.t === 'shift') body.shift?.(m.dx, m.dy);
    else if (m.t === 'place') body.place?.(m.x, m.facing);
    else if (m.t === 'set') {
      if (m.state?.bounds) { bounds = m.state.bounds; body.resize?.(); }
      body.set?.(m.state);
    }
    else if (m.t === 'cue') body.cue?.(m.kind);
    else if (m.t === 'talk') body.talk?.();
  } catch (err) {
    fail(err);
  }
});
post({ t: 'loaded' });
