/**
 * The pages' sounds: tones synthesized with Web Audio, and a figure pack's own audio files
 * (`sounds` in its figure.json). The body in the figure frame asks for its sounds by name
 * (`play`); the page plays them here, so the settings' switches by kind and the master switch
 * hold for every pack.
 */
/** Which kind each sound belongs to; a kind can be silenced on its own (`sfx.configure`). */
export const SOUND_KINDS = {
  move: ['step', 'skid', 'jump', 'land', 'whoosh', 'chirps', 'shake', 'nod', 'spin', 'shiver', 'dance', 'look'],
  touch: ['grab', 'squeak', 'purr', 'poke'],
  face: ['happy', 'wink', 'love', 'surprised', 'angry', 'sad', 'shy', 'yawn'],
  snore: ['snore'],
  talk: ['babble', 'blub'],
  ui: ['tick', 'pop', 'sparkle', 'select', 'listenStart', 'listenEnd'],
};
/** The kinds a body's sounds are filed under; the rest belong to the page (talk, ui). */
export const BODY_SOUND_KINDS = ['move', 'touch', 'face', 'snore'];
const KIND_OF = Object.fromEntries(Object.entries(SOUND_KINDS).flatMap(([kind, names]) => names.map((n) => [n, kind])));
export function createSfx({ storageKey = 'cortico-pet.sound.v1', volume = .55 } = {}) {
  let ctx = null, master = null, unlocked = false, on = true, noiseBuf = null, gainValue = volume;
  // kinds turned off, and seconds of snoring per sleep (0 = the whole sleep)
  let muted = new Set(), snoreSeconds = 0;
  // whether the window is shown: a window that does not throttle its page keeps document.hidden false while hidden
  let shown = true;
  try { on = localStorage.getItem(storageKey) !== 'off'; } catch (e) { /* default on */ }
  const R = (a, b) => a + Math.random() * (b - a);
  function ready() {
    if (!on || !unlocked || !shown || document.hidden) return null;
    if (!ctx) {
      const C = window.AudioContext || window.webkitAudioContext;
      if (!C) return null;
      ctx = new C();
      master = ctx.createGain(); master.gain.value = gainValue;
      const comp = ctx.createDynamicsCompressor();
      master.connect(comp); comp.connect(ctx.destination);
    }
    if (ctx.state === 'suspended') ctx.resume();
    for (const o of own.values()) decode(o);
    return ctx;
  }
  function tone({ type = 'sine', f0 = 440, f1 = f0, dur = .1, vol = .2, at = 0, attack = .005, vib = 0, vibRate = 0, filter = 0 }) {
    const c = ready(); if (!c) return;
    const t0 = c.currentTime + at, o = c.createOscillator(), g = c.createGain();
    o.type = type;
    o.frequency.setValueAtTime(f0, t0);
    o.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t0 + dur);
    if (vib) {
      const l = c.createOscillator(), lg = c.createGain();
      l.frequency.value = vibRate; lg.gain.value = vib;
      l.connect(lg); lg.connect(o.frequency); l.start(t0); l.stop(t0 + dur + .05);
    }
    g.gain.setValueAtTime(.0001, t0);
    g.gain.exponentialRampToValueAtTime(vol, t0 + attack);
    g.gain.exponentialRampToValueAtTime(.0001, t0 + dur);
    let node = o;
    if (filter) { const bq = c.createBiquadFilter(); bq.type = 'lowpass'; bq.frequency.value = filter; o.connect(bq); node = bq; }
    node.connect(g); g.connect(master);
    o.start(t0); o.stop(t0 + dur + .03);
  }
  function noise({ type = 'bandpass', f0 = 1000, f1 = f0, q = 1, dur = .2, vol = .15, at = 0, attack = .01 }) {
    const c = ready(); if (!c) return;
    if (!noiseBuf) {
      noiseBuf = c.createBuffer(1, c.sampleRate, c.sampleRate);
      const d = noiseBuf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    }
    const t0 = c.currentTime + at, s = c.createBufferSource(), bq = c.createBiquadFilter(), g = c.createGain();
    s.buffer = noiseBuf; bq.type = type; bq.Q.value = q;
    bq.frequency.setValueAtTime(f0, t0);
    bq.frequency.exponentialRampToValueAtTime(f1, t0 + dur);
    g.gain.setValueAtTime(.0001, t0);
    g.gain.exponentialRampToValueAtTime(vol, t0 + attack);
    g.gain.exponentialRampToValueAtTime(.0001, t0 + dur);
    s.connect(bq); bq.connect(g); g.connect(master);
    s.start(t0, Math.random() * .5); s.stop(t0 + dur + .03);
  }
  /** The pack's own sounds by name: kind, volume, the file's bytes, and the buffer once an audio context decoded them. */
  let own = new Map();
  function decode(o) {
    if (o.buffer || o.decoding || !ctx) return;
    o.decoding = o.bytes.then((b) => ctx.decodeAudioData(b.slice(0))).then((buf) => { o.buffer = buf; }, (err) => console.error(`音效 ${o.name} 没能解码:`, err));
  }
  function playOwn(o) {
    const c = ready(); if (!c) return;
    // the first ask before the file is decoded goes unheard; the decode starts with the audio context
    if (!o.buffer) { decode(o); return; }
    const src = c.createBufferSource(), g = c.createGain();
    src.buffer = o.buffer; g.gain.value = o.volume;
    src.connect(g); g.connect(master);
    src.start();
  }
  const tones = {
    step(run, i) {
      const k = run ? 1.25 : 1;
      tone({ f0: (i ? 520 : 440) * k, f1: (i ? 380 : 330) * k, dur: .06, vol: run ? .07 : .05 });
      if (run) noise({ f0: 2500, q: .8, dur: .05, vol: .03 });
    },
    skid() { noise({ type: 'highpass', f0: 1800, f1: 900, dur: .22, vol: .08 }); },
    jump() { tone({ type: 'triangle', f0: 200, f1: 720, dur: .24, vol: .22, vib: 40, vibRate: 22 }); },
    land(hard) {
      tone({ f0: hard ? 160 : 190, f1: 48, dur: hard ? .28 : .16, vol: hard ? .4 : .25 });
      noise({ type: 'lowpass', f0: hard ? 700 : 500, f1: 120, dur: .12, vol: hard ? .25 : .12 });
      if (hard) tone({ type: 'square', f0: 420, f1: 300, dur: .08, vol: .06, at: .02, filter: 1600 });
    },
    grab() { tone({ type: 'triangle', f0: 680, f1: 1500, dur: .14, vol: .18, vib: 60, vibRate: 30 }); },
    squeak() { tone({ type: 'triangle', f0: R(900, 1200), f1: R(1300, 1700), dur: .09, vol: .08, vib: 40, vibRate: 35 }); },
    whoosh() { noise({ f0: 300, f1: 2400, q: 1.4, dur: .38, vol: .22, attack: .08 }); },
    chirps() { for (let i = 0; i < 3; i++) tone({ f0: 2300 + i * 120, f1: 3200, dur: .06, vol: .06, at: i * .11 }); },
    shake() { for (let i = 0; i < 5; i++) tone({ type: 'square', f0: 180, f1: 160, dur: .05, vol: .05, at: i * .06, filter: 900 }); },
    hmm() { tone({ type: 'triangle', f0: 330, f1: 360, dur: .12, vol: .08 }); tone({ type: 'triangle', f0: 392, f1: 470, dur: .16, vol: .08, at: .14 }); },
    yawn() { tone({ type: 'triangle', f0: 520, f1: 240, dur: 1, vol: .1, vib: 12, vibRate: 5, filter: 1500, attack: .15 }); },
    snore() {
      noise({ type: 'lowpass', f0: 250, f1: 700, dur: .7, vol: .09, attack: .35 });
    },
    purr() { tone({ type: 'sawtooth', f0: 62, f1: 58, dur: .9, vol: .08, vib: 6, vibRate: 24, filter: 320, attack: .1 }); },
    poke() { tone({ f0: 320, f1: 200, dur: .09, vol: .16 }); },
    shiver() { for (let i = 0; i < 8; i++) tone({ type: 'square', f0: 900, f1: 820, dur: .03, vol: .035, at: i * .07, filter: 2400 }); },
    // looking about hums like the thinking 'hmm', but counts as a motion sound
    look() { tones.hmm(); },
    dance() { [523, 659, 784, 659, 880].forEach((fr, i) => tone({ type: 'triangle', f0: fr, dur: .13, vol: .09, at: i * .15 })); },
    nod() { tone({ type: 'triangle', f0: 520, f1: 440, dur: .07, vol: .08 }); tone({ type: 'triangle', f0: 520, f1: 440, dur: .07, vol: .08, at: .2 }); },
    spin() { tone({ type: 'triangle', f0: 300, f1: 1200, dur: .3, vol: .12, vib: 30, vibRate: 18 }); },
    happy() { tone({ type: 'triangle', f0: 660, f1: 700, dur: .1, vol: .14 }); tone({ type: 'triangle', f0: 990, f1: 1050, dur: .14, vol: .14, at: .09 }); },
    wink() { tone({ f0: 1760, dur: .5, vol: .1 }); tone({ f0: 2637, dur: .45, vol: .06, at: .04 }); },
    love() { tone({ f0: 480, f1: 820, dur: .1, vol: .14 }); tone({ f0: 600, f1: 1000, dur: .12, vol: .14, at: .13 }); },
    surprised() { tone({ f0: 380, f1: 1500, dur: .2, vol: .16, vib: 15, vibRate: 12 }); },
    angry() { tone({ type: 'sawtooth', f0: 120, f1: 95, dur: .5, vol: .12, vib: 12, vibRate: 14, filter: 700 }); },
    sad() { tone({ type: 'triangle', f0: 440, f1: 392, dur: .3, vol: .13, vib: 8, vibRate: 6 }); tone({ type: 'triangle', f0: 392, f1: 262, dur: .55, vol: .13, at: .3, vib: 10, vibRate: 5 }); },
    shy() { tone({ f0: 1300, f1: 1600, dur: .07, vol: .07 }); tone({ f0: 1450, f1: 1750, dur: .07, vol: .06, at: .1 }); },
    tick() { tone({ f0: 1200, f1: 1000, dur: .03, vol: .05 }); },
    pop() { tone({ f0: 240, f1: 720, dur: .07, vol: .14 }); },
    sparkle() { [1568, 2093, 2637].forEach((fr, i) => tone({ f0: fr, dur: .25, vol: .06, at: i * .06 })); },
    select() { tone({ type: 'triangle', f0: 520, f1: 1040, dur: .1, vol: .12 }); },
    babble(ch) {
      const fr = 330 + (ch.codePointAt(0) % 9) * 28;
      tone({ type: 'square', f0: fr, f1: fr * R(.85, 1.1), dur: .05, vol: .05, filter: 1800 });
    },
    blub() { tone({ f0: R(500, 700), f1: R(900, 1200), dur: .05, vol: .05 }); },
    listenStart() { tone({ f0: 880, dur: .12, vol: .1 }); tone({ f0: 1320, dur: .16, vol: .1, at: .1 }); },
    listenEnd() { tone({ f0: 1320, dur: .1, vol: .09 }); tone({ f0: 990, dur: .16, vol: .09, at: .09 }); },
  };
  const api = {
    unlock() { unlocked = true; ready(); },
    isOn: () => on,
    set(v) { on = v; try { localStorage.setItem(storageKey, v ? 'on' : 'off'); } catch (e) { /* not persisted */ } },
    volume(v) { gainValue = v; if (master) master.gain.value = v; },
    /** The window was shown or hidden (by hand or while something is full screen); hidden, nothing plays. */
    setShown(v) { shown = v; },
    /** `kinds`: kind → on (SOUND_KINDS); `snoreSeconds`: snoring stops this long into a sleep, 0 = never. */
    configure({ kinds, snoreSeconds: s } = {}) {
      if (kinds) muted = new Set(Object.keys(SOUND_KINDS).filter((k) => kinds[k] === false));
      if (typeof s === 'number' && s >= 0) snoreSeconds = s;
    },
    /**
     * The body's sounds (`sounds` of the pack on screen, from `base`): each is fetched now and decoded once
     * there is an audio context. `null` drops them.
     */
    usePack(base, sounds) {
      own = new Map(Object.entries(sounds ?? {}).map(([name, d]) => {
        const bytes = fetch(new URL(d.file, new URL(base, location.href))).then((r) => (r.ok ? r.arrayBuffer() : Promise.reject(new Error(`HTTP ${r.status}`))));
        bytes.catch((err) => console.error(`音效 ${name}(${d.file})没能载入:`, err));
        return [name, { name, kind: d.kind, volume: d.volume ?? 1, bytes }];
      }));
      if (ctx) for (const o of own.values()) decode(o);
    },
    /**
     * A sound the body asks for: the pack's own by that name (filed under the kind its manifest gives), else the
     * synthesized tone, filed under `kind` when that is a body's kind (a face that borrows the 'pop' tone is a
     * face sound) and under the tone's own kind otherwise. Snoring (args[0]: seconds asleep) stops after `snoreSeconds`.
     */
    play(name, kind, ...args) {
      const o = own.get(name);
      const k = o ? o.kind : BODY_SOUND_KINDS.includes(kind) ? kind : KIND_OF[name];
      if (muted.has(k)) return;
      if (k === 'snore' && snoreSeconds > 0 && args[0] > snoreSeconds) return;
      if (o) playOwn(o);
      else if (Object.hasOwn(tones, name)) tones[name](...args);
    },
  };
  // the page's own calls by name (sfx.pop()) play the tone, muted with its kind; a pack's sound never stands in for them
  for (const name of Object.keys(tones)) api[name] = (...args) => { if (!muted.has(KIND_OF[name])) tones[name](...args); };
  return api;
}
