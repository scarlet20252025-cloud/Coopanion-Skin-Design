import * as kit from '../../../../preview/vendor/kit/body.js';
import { createLayeredBody } from '../../../../packs/atri-v011/figure.js';

const base = new URL('../../../../packs/atri-v011/', import.meta.url);
const model = await (await fetch(new URL('model.json', base))).json();

const $ = (id) => document.getElementById(id);
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const mix = (a, b, p) => a + (b - a) * clamp(p);
const ease = (p) => { p = clamp(p); return p * p * (3 - 2 * p); };
const easeOut = (p) => 1 - Math.pow(1 - clamp(p), 3);
const lerpLog = (a, b, p) => a * Math.pow(b / a, clamp(p));

const DURATION = 36;

// 七段分镜。对话段里再细分三轮（用 turnMarks 指示），这一版主打"多演示交互"。
const scenes = [
  ['intro', 0, 4],
  ['talk', 4, 13],
  ['touch', 13, 18.5],
  ['actions', 18.5, 23.5],
  ['radish', 23.5, 30],
  ['seated', 30, 33],
  ['outro', 33, 36],
];

// 确定性伪随机：同一时刻永远得到同一画面
let seed = 4021;
const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };

const events = [];
const checks = [];
let body, sim = 0, eventIndex = 0, cursorPoint = null, playing = false, lastPlay = 0;

// ---------------------------------------------------------------------------
// 背景装饰：一次生成，之后只按时间做纯函数位移
// ---------------------------------------------------------------------------
const bubbles = [];
{
  const host = $('bubbles');
  const NS = 'http://www.w3.org/2000/svg';
  for (let i = 0; i < 34; i++) {
    const x = 60 + rnd() * 1800;
    const r = 2.5 + rnd() * 8;
    const speed = 26 + rnd() * 70;
    const wob = 12 + rnd() * 26;
    const wf = 0.5 + rnd() * 1.1;
    const phase = rnd() * Math.PI * 2;
    const y0 = 1080 + rnd() * 260;
    const op = 0.10 + rnd() * 0.30;
    const c = document.createElementNS(NS, 'circle');
    c.setAttribute('cx', x); c.setAttribute('cy', y0); c.setAttribute('r', r);
    c.setAttribute('fill', 'none');
    c.setAttribute('stroke', '#bfe4f5');
    c.setAttribute('stroke-width', (0.8 + rnd() * 1.2).toFixed(2));
    host.append(c);
    bubbles.push({ el: c, x, y0, r, speed, wob, wf, phase, op });
  }
}

{
  const host = $('waves');
  const NS = 'http://www.w3.org/2000/svg';
  for (let i = 0; i < 7; i++) {
    const y = 220 + i * 128;
    const p = document.createElementNS(NS, 'path');
    p.setAttribute('d', `M-120 ${y}Q360 ${y - 16} 960 ${y}T2040 ${y}`);
    p.setAttribute('opacity', (0.05 + (i % 3) * 0.03).toFixed(3));
    host.append(p);
  }
}

// ---------------------------------------------------------------------------
// 对话脚本：三轮，第三轮是"叫她萝卜子"的引子
// 每轮 = [开始, 结束, 标题, 副标题, 说话人, 第一行, 第二行]
// ---------------------------------------------------------------------------
const turns = [
  [4.4, 7.2, '她就在那儿。', '一句气泡，接住你的一段话。', '亚托利',
   '别担心，这点事情我一下就做完了。', '毕竟——我可是高性能的。'],
  [7.4, 10.2, '也会撒娇。', '不是冷冰冰的应答，是有情绪的回应。', '亚托利',
   '累了就靠一会儿嘛，我陪着你。', '……不过只准靠一小会儿哦。'],
  [10.4, 13.0, '也会闹别扭。', '试试看，说一句她不爱听的话。', '亚托利',
   '诶，你刚才嘀咕什么？', '……我好像听到一个很失礼的词。'],
];

// ---------------------------------------------------------------------------
// 角色
// ---------------------------------------------------------------------------
async function reset() {
  body?.dispose();
  $('petMount').replaceChildren();
  seed = 4021;
  body = await createLayeredBody(base, {
    kit,
    model,
    host: {
      root: $('petMount'),
      bounds: () => ({ W: 800, H: 880, floorY: 828, S: 2.55 }),
      start: { x: 400, facing: -1, enter: 'stand' },
      emit: (kind, detail) => events.push({ kind, detail, time: sim }),
      sound: () => {},
    },
  });
  body.set({ roam: 'off', hold: 999 });
  body.place(400, -1);
  sim = 0; eventIndex = 0; cursorPoint = null;
  checks.length = 0;
  events.length = 0;
}

function word(w) {
  const accepted = body.do(w);
  checks.push({ time: sim, word: w, accepted });
  return accepted;
}

function hit() {
  const l = body.layout();
  return (l.hit && l.hit[0]) || { x: 400, y: 300 };
}

// ---------------------------------------------------------------------------
// 动作脚本
// 关键约束：kit 的 doWord() 在 busy() 时拒收表情，所以每次发新动作前留足间隔，
// 并且同一时刻不要连发两个会互相打断的动作。
// ---------------------------------------------------------------------------
const schedule = [
  // 0–4 出场
  [0, () => word('wave')],
  [0.35, () => word('neutral')],
  [1.6, () => word('happy')],
  [3.0, () => word('wink')],

  // 4–13 三轮对话
  [4.3, () => { body.place(400, -1); word('stand'); word('neutral'); }],
  [4.7, () => { body.talk(); }],
  [6.2, () => word('smug')],

  [7.5, () => { body.place(400, -1); word('stand'); word('neutral'); body.talk(); }],
  [9.0, () => word('shy')],

  [10.5, () => { body.place(400, -1); word('stand'); word('neutral'); body.talk(); }],
  [11.9, () => word('confused')],
  [12.5, () => word('worried')],

  // 13–18.5 点击 / 提起 / 松手（三次交互，最后一次是摔落）
  [13.4, () => { body.place(400, -1); word('stand'); word('neutral'); }],
  [14.0, () => { const h = hit(); cursorPoint = { x: h.x, y: h.y - 70, t: 14000 }; body.pointer('down', cursorPoint); }],
  [14.14, () => body.pointer('up', { ...cursorPoint, t: 14140 })],
  // 等点击反应播完再发下一个动作
  [15.4, () => { const h = hit(); cursorPoint = { x: h.x, y: h.y - 40, t: 15400 }; body.pointer('down', cursorPoint); }],
  [17.2, () => body.pointer('up', { x: 400, y: 150, t: 17200 })],

  // 18.5–23.5 动作与表情轮播（八个 chip）
  [18.8, () => { body.place(400, -1); word('stand'); word('wave'); }],
  [19.9, () => word('happy')],
  [21.0, () => word('dance')],
  [22.2, () => word('shy')],
  [23.0, () => word('surprised')],

  // 23.5–30 叫她萝卜子 → 生气（本版重点）
  [23.8, () => { body.place(400, -1); word('stand'); word('neutral'); }],
  [24.4, () => word('surprised')],      // 「你刚才叫我什么？」
  [25.9, () => word('pout')],           // 嘟嘴
  [27.4, () => word('angry')],          // 生气 + 青筋
  [28.6, () => { body.talk(); word('determined'); }],

  // 30–33 坐下
  [30.1, () => { body.place(400, -1); word('sit'); }],
  [31.5, () => word('dizzy')],

  // 33–36 片尾
  [33.1, () => { body.place(400, -1); word('stand'); word('happy'); }],
  [34.3, () => word('wave')],
];

// ---------------------------------------------------------------------------
// 场景推进：全部是 t 的纯函数
// ---------------------------------------------------------------------------
function at(t) {
  for (const [id, start, end] of scenes) {
    const p = t - start;
    const visible = t >= start && t < end;
    const el = $(id);
    // 用 style 而不是属性：SVG presentation attribute 的变更在暂停动画时可能不触发重绘
    el.style.opacity = visible ? clamp(p / 0.34).toFixed(3) : '0';
    el.setAttribute('transform', `translate(${(visible ? mix(26, 0, easeOut(p / 0.45)) : 26).toFixed(2)} 0)`);
    // 显示中的场景必须挡住点击测试，隐藏的让开（elementFromPoint 用来校验构图）
    el.style.pointerEvents = visible ? 'auto' : 'none';
  }

  // 光柱漂移
  for (let i = 0; i < 3; i++) {
    const el = $('sh' + i);
    const dx = Math.sin(t * 0.42 + i * 2.1) * 34;
    const sc = 0.94 + Math.sin(t * 0.63 + i * 1.4) * 0.06;
    el.setAttribute('transform', `translate(${dx.toFixed(2)} 0) scale(1 ${sc.toFixed(4)})`);
    el.setAttribute('opacity', (0.75 + Math.sin(t * 0.9 + i) * 0.25).toFixed(3));
  }

  // 气泡上浮
  const span = 1080 + 320;
  for (const b of bubbles) {
    let y = b.y0 - t * b.speed;
    y = ((y % span) + span) % span - 220;
    const x = b.x + Math.sin(t * b.wf + b.phase) * b.wob;
    b.el.setAttribute('cx', x.toFixed(2));
    b.el.setAttribute('cy', y.toFixed(2));
    b.el.setAttribute('opacity', (clamp((y - 40) / 260) * b.op).toFixed(3));
  }

  $('waves').setAttribute('transform', `translate(${(-t * 26).toFixed(2)} ${(Math.sin(t * 0.5) * 8).toFixed(2)})`);

  // 光晕：蓝色全程，红色只在生气段（27.4–29.6）压上来
  const haloIn = clamp((t - 0.4) / 1.4) * (1 - clamp((t - 17.6) / 1.2) * 0.35);
  $('halo').setAttribute('opacity', (haloIn * 0.9).toFixed(3));
  $('halo').setAttribute('r', (368 + Math.sin(t * 1.15) * 16).toFixed(1));
  const angerIn = clamp((t - 27.3) / 0.8) * (1 - clamp((t - 29.2) / 1.0));
  $('haloRed').setAttribute('opacity', (angerIn * 0.95).toFixed(3));
  $('haloRed').setAttribute('r', (330 + Math.sin(t * 3.1) * 26 + angerIn * 40).toFixed(1));

  $('topRule').setAttribute('opacity', (0.28 * clamp((t - 0.2) / 1.0)).toFixed(3));

  // 出场
  $('introRule').setAttribute('stroke-dasharray', '692');
  $('introRule').setAttribute('stroke-dashoffset', (692 * (1 - easeOut((t - 0.9) / 0.75))).toFixed(2));
  $('introQuote').setAttribute('opacity', clamp((t - 2.1) / 0.7).toFixed(3));

  // ---- 场景 2：三轮对话 ----
  const talking = t >= 4 && t < 13;
  if (talking) {
    let cur = 0;
    for (let i = 0; i < turns.length; i++) if (t >= turns[i][0]) cur = i;
    const [start, end, title, sub, name, l1, l2] = turns[cur];
    $('talkTitle').textContent = title;
    $('talkSub').textContent = sub;
    $('bubbleName').textContent = name;
    $('bubbleL1').textContent = l1;
    $('bubbleL2').textContent = l2;
    // 每轮进场的浮入
    const p = clamp((t - start) / 0.45);
    $('bubbleGroup').setAttribute('opacity', (0.15 + 0.85 * easeOut(p)).toFixed(3));
    $('bubbleGroup').setAttribute('transform', `translate(120 ${(566 + mix(20, 0, easeOut(p))).toFixed(1)})`);
    // 逐行出现：第一行先出，第二行延迟 0.55s
    $('bubbleL1').setAttribute('opacity', easeOut((t - start) / 0.4).toFixed(3));
    $('bubbleL2').setAttribute('opacity', easeOut((t - start - 0.55) / 0.45).toFixed(3));
    // 三颗轮次指示点
    $('turnMarks').setAttribute('opacity', clamp((t - 4.4) / 0.5).toFixed(3));
    const cols = ['#2f5d73', '#2f5d73', '#2f5d73'];
    cols[cur] = '#7fc4e0';
    for (let i = 0; i < 3; i++) $('tm' + i).setAttribute('fill', cols[i]);
  }

  // ---- 场景 3：点击与提起 ----
  const stage2 = t >= 13.4;
  $('touchTitle').textContent = t < 15.2 ? '戳一下，她会回应。' : '提起来，也会挣扎。';
  $('touchSub').textContent = t < 15.2 ? '呆毛一晃，小情绪自己冒出来。' : '慌张的表情，配上轻轻的踢腿。';
  $('touchChips').setAttribute('opacity', clamp((t - 13.6) / 0.5).toFixed(3));
  {
    const hi = t < 15.2 ? 0 : 1;
    const chips = $('touchChips').children;
    for (let i = 0; i < chips.length; i++) {
      const r = chips[i].querySelector('rect');
      r.setAttribute('fill', i === hi ? '#2d6d8a' : '#16303f');
      r.setAttribute('stroke', i === hi ? '#9fdcf5' : '#3f7b94');
    }
  }

  // ---- 场景 4：八个 chip 轮播 ----
  const actIdx = t < 19.9 ? 0 : t < 21.0 ? 1 : t < 22.2 ? 2 : t < 23.0 ? 3 : 4;
  const actTitles = ['招手，打招呼。', '开心，眼睛会弯。', '跳舞，音符跟着。', '害羞，脸红起来。', '惊讶，呆毛立起。'];
  $('actTitle').textContent = actTitles[Math.min(actIdx, actTitles.length - 1)];
  for (let i = 0; i < 8; i++) {
    const g = $('chip' + i);
    const sel = t >= 18.5 && t < 23.5 && i === actIdx;
    const r = g.querySelector('rect');
    r.setAttribute('fill', sel ? '#2d6d8a' : '#16303f');
    r.setAttribute('stroke', sel ? '#9fdcf5' : '#3f7b94');
    r.setAttribute('stroke-width', sel ? 2 : 1.5);
    g.querySelector('text').style.fill = sel ? '#eaf6fb' : '#9db6c6';
  }

  // ---- 场景 5：萝卜子 → 生气 ----
  const radOn = t >= 23.5 && t < 30;
  if (radOn) {
    // 三步依次点亮：惊讶 → 嘟嘴 → 生气
    const step = t < 25.9 ? 0 : t < 27.4 ? 1 : 2;
    $('radSteps').setAttribute('opacity', clamp((t - 23.9) / 0.5).toFixed(3));
    for (let i = 0; i < 3; i++) {
      const g = $('rs' + i);
      const on = i <= step;
      const r = g.querySelector('rect');
      r.setAttribute('fill', i === step ? '#5a2a22' : on ? '#331f20' : '#231a1c');
      r.setAttribute('stroke', i === step ? '#ff9b78' : on ? '#a45a45' : '#7a4034');
      r.setAttribute('stroke-width', i === step ? 2 : 1.5);
      g.querySelector('text').style.fill = i <= step ? '#ffe0d0' : '#8a6f68';
    }
    // 对话：先问，再否认
    const p = clamp((t - 24.0) / 0.45);
    $('radBubble').setAttribute('opacity', (0.15 + 0.85 * easeOut(p)).toFixed(3));
    $('radBubble').setAttribute('transform', `translate(120 ${(540 + mix(20, 0, easeOut(p))).toFixed(1)})`);
    const l1On = t < 27.4;
    $('radL1').textContent = l1On ? '……你刚才，叫我什么？' : '说了不是萝卜子！';
    $('radL2').textContent = l1On ? '（歪头，眉毛皱起来）' : '我可是高性能的！';
    $('radL1').setAttribute('opacity', easeOut((t - 24.2) / 0.4).toFixed(3));
    $('radL2').setAttribute('opacity', easeOut((t - (l1On ? 24.9 : 27.6)) / 0.4).toFixed(3));
    $('radL1').setAttribute('class', l1On ? '' : 'warn');
    // 生气时标题换色
    $('radTitle').textContent = l1On ? '「萝卜子？」' : '「我才不是萝卜子！」';
    $('radTitle').setAttribute('class', l1On ? 'large' : 'large warn');
    $('radSub').textContent = l1On ? '这个名字，她不太喜欢。' : '生气值拉满，青筋都出来了。';
    // 生气抖动：整块负片式的轻微位移
    if (t >= 27.4 && t < 29.6) {
      const sh = Math.sin(t * 46) * 3.2;
      $('radish').setAttribute('transform', `translate(${mix(0, 0, 1).toFixed(2)} 0) translate(${sh.toFixed(2)} 0)`);
    }
  }

  // ---- 场景 6：坐姿 ----
  $('seatTitle').textContent = t < 31.6 ? '坐下，歇一会儿。' : '晕乎乎，也有小情绪。';
  $('seatSub').textContent = t < 31.6 ? '安安稳稳地坐着，尾巴轻轻晃。' : '圈圈眼一出来，就是想撒娇了。';
  $('seatRule').setAttribute('stroke-dasharray', '650');
  $('seatRule').setAttribute('stroke-dashoffset', (650 * (1 - easeOut((t - 30.2) / 0.7))).toFixed(2));
  for (let i = 0; i < 3; i++) {
    const g = $('sc' + i);
    const p = clamp((t - (30.45 + i * 0.2)) / 0.5);
    g.setAttribute('opacity', easeOut(p).toFixed(3));
    g.setAttribute('transform', `translate(${(238 * i).toFixed(1)} ${mix(18, 0, easeOut(p)).toFixed(1)})`);
    const r = g.querySelector('rect');
    const active = i === (t < 31.6 ? 0 : 1);
    r.setAttribute('fill', active ? '#173847' : '#0f2430');
    r.setAttribute('stroke', active ? '#9fdcf5' : '#2f5d73');
    r.setAttribute('stroke-width', active ? 2 : 1.5);
  }
  $('seatQuote').setAttribute('opacity', clamp((t - 31.8) / 0.6).toFixed(3));

  // ---- 角色构图 ----
  let px = 960, py = 96, scale = 1;
  if (talking) { scale = 0.66; px = 1010; py = 250; }
  if (t >= 30 && t < 33) { py = 84; }
  if (t >= 33) { scale = 0.94; px = 1010; py = 120; }
  const fp = $('petFrame');
  fp.setAttribute('transform', `matrix(${scale} 0 0 ${scale} ${(px - 960 * scale).toFixed(2)} ${(py - 96 * scale).toFixed(2)})`);

  // ---- 指针 ----
  const curVisible = t >= 13.9 && t < 17.4;
  $('cursor').setAttribute('opacity', curVisible ? 1 : 0);
  let cx = 0, cy = 0;
  if (curVisible) {
    const h = hit();
    let x = h.x, y = h.y - 70;
    if (t < 14.0) {
      x = mix(700, h.x, ease((t - 13.9) / 0.1));
      y = mix(600, h.y - 70, ease((t - 13.9) / 0.1));
    } else if (t >= 15.4) {
      x = 400;
      y = mix(300, 150, ease((t - 15.4) / 1.8));
    }
    cx = px + x * scale;
    cy = py + y * scale;
    $('cursor').setAttribute('transform', `translate(${cx.toFixed(1)} ${cy.toFixed(1)}) scale(${scale.toFixed(2)})`);
    $('clickRing').setAttribute('cx', cx.toFixed(1));
    $('clickRing').setAttribute('cy', cy.toFixed(1));
    $('clickCore').setAttribute('cx', cx.toFixed(1));
    $('clickCore').setAttribute('cy', cy.toFixed(1));
  }
  let ringOp = 0, ringR = 20, coreOp = 0;
  for (const c of [13.85, 15.4]) {
    const p = clamp((t - c) / 0.55);
    if (t >= c && p < 1) { ringOp = Math.max(ringOp, 1 - p); ringR = Math.max(ringR, 18 + 46 * easeOut(p)); }
    if (t >= c && t < c + 0.18) coreOp = Math.max(coreOp, 1 - clamp((t - c) / 0.18));
  }
  $('clickRing').setAttribute('opacity', ringOp.toFixed(3));
  $('clickRing').setAttribute('r', ringR.toFixed(1));
  $('clickCore').setAttribute('opacity', coreOp.toFixed(3));

  // ---- 底部 ----
  $('progress').setAttribute('stroke-dasharray', '1680');
  $('progress').setAttribute('stroke-dashoffset', (1680 * (1 - clamp(t / DURATION))).toFixed(2));
  $('bottomLabel').textContent =
    t >= 33 ? 'Asryto · 亚托利 · 2026' : '亚托利 · 基于 Coopanion 的发布动画';
}

// 每帧先以 60 Hz 推进角色逻辑，再把场景对齐到目标时间
window.renderAt = async (time) => {
  if (time < sim - 0.001) await reset();
  while (sim < time - 1e-6) {
    const next = Math.min(time, sim + 1 / 60);
    while (eventIndex < schedule.length && schedule[eventIndex][0] <= next + 1e-7) {
      schedule[eventIndex++][1]();
    }
    if (next >= 15.45 && next < 17.2) {
      body.pointer('move', { x: 400, y: mix(300, 150, ease((next - 15.4) / 1.8)), t: next * 1000 });
    }
    body.step(next - sim);
    sim = next;
  }
  if (eventIndex === 0 && time === 0) { schedule[eventIndex++][1](); body.step(0); }
  at(time);
  window.promoState = {
    time,
    layout: body.layout(),
    visual: body.visualState(),
    secondary: body.secondaryState(),
    checks,
    events,
  };
};

await reset();
await window.renderAt(0);
window.promoReady = true;

if (new URLSearchParams(location.search).has('review')) {
  $('reviewControls').style.display = 'block';
  $('reviewSeek').onclick = () => { playing = false; window.renderAt(Number($('reviewTime').value)); };
  $('reviewPlay').onclick = () => { playing = !playing; lastPlay = performance.now(); };
  const frame = async (now) => {
    if (playing) {
      const t = sim + (now - lastPlay) / 1000;
      if (t < DURATION) await window.renderAt(t); else playing = false;
    }
    lastPlay = now;
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
}
