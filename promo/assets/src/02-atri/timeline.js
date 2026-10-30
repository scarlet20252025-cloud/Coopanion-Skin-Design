import * as kit from '../../../../preview/vendor/kit/body.js';
import { createLayeredBody } from '../../../../packs/atri-v011/figure.js';

const base = new URL('../../../../packs/atri-v011/', import.meta.url);
const model = await (await fetch(new URL('model.json', base))).json();

const $ = (id) => document.getElementById(id);
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const mix = (a, b, p) => a + (b - a) * clamp(p);
const ease = (p) => { p = clamp(p); return p * p * (3 - 2 * p); };
const easeOut = (p) => 1 - Math.pow(1 - clamp(p), 3);

// 场景表：与 BRIEF 的六段分镜一一对应
const scenes = [
  ['intro', 0, 4],
  ['talk', 4, 9],
  ['touch', 9, 14],
  ['actions', 14, 20],
  ['seated', 20, 25],
  ['outro', 25, 30],
];

// 确定性伪随机：同一时刻永远得到同一画面，渲染可复现
let seed = 4021;
const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };

const events = [];
const checks = [];
let body, sim = 0, eventIndex = 0, cursorPoint = null, playing = false, lastPlay = 0;

// ---------------------------------------------------------------------------
// 背景装饰：气泡与光柱在页面初始化时一次生成，之后只按时间做线性位移
// ---------------------------------------------------------------------------
const BUBBLE_N = 34;
const bubbles = [];
{
  const host = $('bubbles');
  const NS = 'http://www.w3.org/2000/svg';
  for (let i = 0; i < BUBBLE_N; i++) {
    const x = 60 + rnd() * 1800;
    const r = 2.5 + rnd() * 8;
    const speed = 26 + rnd() * 70;      // px/s 上浮
    const wob = 12 + rnd() * 26;        // 横向摆动幅度
    const wf = 0.5 + rnd() * 1.1;       // 摆动频率
    const phase = rnd() * Math.PI * 2;
    const y0 = 1080 + rnd() * 260;
    const op = 0.10 + rnd() * 0.30;
    const c = document.createElementNS(NS, 'circle');
    c.setAttribute('cx', x); c.setAttribute('cy', y0); c.setAttribute('r', r);
    c.setAttribute('fill', 'none');
    c.setAttribute('stroke', '#bfe4f5');
    c.setAttribute('stroke-width', (0.8 + rnd() * 1.2).toFixed(2));
    c.setAttribute('opacity', op.toFixed(3));
    host.append(c);
    bubbles.push({ el: c, x, y0, r, speed, wob, wf, phase });
  }
}

// 水波横线：随镜头缓慢漂移，制造"水下"纵深
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

// 命中区取角色第一个 hit（头部呆毛附近），指针必须落在真实 hit 上
function hit() {
  const l = body.layout();
  return (l.hit && l.hit[0]) || { x: 400, y: 300 };
}

// 动作脚本：时间 / 行为
const schedule = [
  // 0–4 出场
  [0, () => word('wave')],
  [0.35, () => word('neutral')],
  [1.6, () => word('happy')],
  // 4–9 对话
  [4.2, () => { body.place(400, -1); word('stand'); word('neutral'); }],
  [4.6, () => { body.talk(); body.cue?.('cheer'); }],
  [6.9, () => word('smug')],
  // 9–14 点击与提起
  [9.7, () => { const h = hit(); cursorPoint = { x: h.x, y: h.y - 70, t: 9700 }; body.pointer('down', cursorPoint); }],
  [9.84, () => body.pointer('up', { ...cursorPoint, t: 9840 })],
  // 点击后的反应由 kit 自己播放；此处不再抢发表情，否则 busy() 会拒收（真实行为）
  [11.3, () => { const h = hit(); cursorPoint = { x: h.x, y: h.y - 40, t: 11300 }; body.pointer('down', cursorPoint); }],
  [13.1, () => body.pointer('up', { x: 400, y: 150, t: 13100 })],
  // 14–20 动作
  [14.1, () => { body.place(400, -1); word('stand'); word('wave'); }],
  [15.9, () => word('happy')],
  [17.2, () => word('dance')],
  [18.8, () => word('shy')],
  // 20–25 坐下
  [20.1, () => { body.place(400, -1); word('sit'); }],
  [22.2, () => word('dizzy')],
  // 25–30 片尾
  [25.1, () => { body.place(400, -1); word('stand'); word('happy'); }],
  [26.2, () => word('wave')],
];

// ---------------------------------------------------------------------------
// 场景推进：所有形变都是时间 t 的纯函数
// ---------------------------------------------------------------------------
function at(t) {
  // 六段淡入 + 轻微横移
  for (const [id, start, end] of scenes) {
    const p = t - start;
    const visible = t >= start && t < end;
    const el = $(id);
    el.setAttribute('opacity', visible ? clamp(p / 0.34).toFixed(3) : 0);
    el.setAttribute('transform', `translate(${visible ? mix(26, 0, easeOut(p / 0.45)).toFixed(2) : 26} 0)`);
  }

  // 水下光柱：低频横向漂移 + 呼吸
  for (let i = 0; i < 3; i++) {
    const el = $('sh' + i);
    const dx = Math.sin(t * 0.42 + i * 2.1) * 34;
    const sc = 0.94 + Math.sin(t * 0.63 + i * 1.4) * 0.06;
    el.setAttribute('transform', `translate(${dx.toFixed(2)} 0) scale(1 ${sc.toFixed(4)})`);
    el.setAttribute('opacity', (0.75 + Math.sin(t * 0.9 + i) * 0.25).toFixed(3));
  }

  // 气泡上浮
  for (const b of bubbles) {
    let y = b.y0 - t * b.speed;
    const span = 1080 + 320;
    y = ((y % span) + span) % span - 220;
    const x = b.x + Math.sin(t * b.wf + b.phase) * b.wob;
    b.el.setAttribute('cx', x.toFixed(2));
    b.el.setAttribute('cy', y.toFixed(2));
    // 靠近顶部时淡出，避免硬边
    const fade = clamp((y - 40) / 260);
    b.el.setAttribute('opacity', (Number(b.el.getAttribute('opacity')) * 0 + fade * 0.34).toFixed(3));
  }

  // 水波横线漂移
  $('waves').setAttribute('transform', `translate(${(-t * 26).toFixed(2)} ${(Math.sin(t * 0.5) * 8).toFixed(2)})`);

  // 角色背后的光晕在出场和前两段渐显
  const haloIn = clamp((t - 0.4) / 1.4) * (1 - clamp((t - 13.6) / 1.2) * 0.45);
  $('halo').setAttribute('opacity', (haloIn * 0.9).toFixed(3));
  $('halo').setAttribute('r', (368 + Math.sin(t * 1.15) * 16).toFixed(1));

  // 顶部细线
  $('topRule').setAttribute('opacity', (0.28 * clamp((t - 0.2) / 1.0)).toFixed(3));

  // 出场横线伸展
  $('introRule').setAttribute('stroke-dasharray', '692');
  $('introRule').setAttribute('stroke-dashoffset', (692 * (1 - easeOut((t - 0.9) / 0.75))).toFixed(2));

  // 台词：先出背景，再出引号
  $('introQuote').setAttribute('opacity', clamp((t - 2.1) / 0.7).toFixed(3));

  // ---- 场景 2：对话气泡 ----
  const talking = t >= 4 && t < 9;
  $('bubbleGroup').setAttribute('opacity', talking ? clamp((t - 4.6) / 0.4).toFixed(3) : 0);
  if (talking) {
    const bp = clamp((t - 4.6) / 0.5);
    $('bubbleGroup').setAttribute('transform', `translate(${mix(120, 120, bp).toFixed(1)} ${(596 + mix(22, 0, easeOut(bp))).toFixed(1)})`);
  }

  // ---- 场景 3：点击 ----
  $('touchTitle').textContent = t < 11.0 ? '戳一下，她会回应。' : '提起来，也会挣扎。';
  $('touchSub').textContent = t < 11.0 ? '呆毛一晃，小情绪自己冒出来。' : '慌张的表情，配上轻轻的踢腿。';
  $('touchChips').setAttribute('opacity', clamp((t - 9.4) / 0.5).toFixed(3));
  {
    const hi = t < 11.0 ? 0 : 1;
    const chips = $('touchChips').children;
    for (let i = 0; i < chips.length; i++) {
      const r = chips[i].querySelector('rect');
      r.setAttribute('fill', i === hi ? '#2d6d8a' : '#16303f');
      r.setAttribute('stroke', i === hi ? '#9fdcf5' : '#3f7b94');
    }
  }

  // ---- 场景 4：动作 chips ----
  for (let i = 0; i < 4; i++) {
    const sel = t >= 14 && t < 20 && i === (t < 15.9 ? 0 : t < 17.2 ? 1 : t < 18.8 ? 2 : 3);
    const g = $('chip' + i);
    const r = g.querySelector('rect');
    r.setAttribute('fill', sel ? '#2d6d8a' : '#16303f');
    r.setAttribute('stroke', sel ? '#9fdcf5' : '#3f7b94');
    r.setAttribute('stroke-width', sel ? 2 : 1.5);
    g.querySelector('text').style.fill = sel ? '#eaf6fb' : '#9db6c6';
  }

  // ---- 场景 5：坐下 ----
  $('seatTitle').textContent = t < 22.2 ? '坐下，歇一会儿。' : '晕乎乎，也有小情绪。';
  $('seatSub').textContent = t < 22.2 ? '安安稳稳地坐着，尾巴轻轻晃。' : '圈圈眼一出来，就是想撒娇了。';
  // 横线伸展 + 三张卡片依次浮入 + 引号最后出现，保证坐姿段左侧不空
  $('seatRule').setAttribute('stroke-dasharray', '650');
  $('seatRule').setAttribute('stroke-dashoffset', (650 * (1 - easeOut((t - 20.2) / 0.7))).toFixed(2));
  for (let i = 0; i < 3; i++) {
    const g = $('sc' + i);
    const p = clamp((t - (20.45 + i * 0.22)) / 0.55);
    g.setAttribute('opacity', easeOut(p).toFixed(3));
    g.setAttribute('transform', `translate(${(238 * i).toFixed(1)} ${mix(18, 0, easeOut(p)).toFixed(1)})`);
    const r = g.querySelector('rect');
    const active = i === (t < 22.2 ? 0 : 1);
    r.setAttribute('fill', active ? '#173847' : '#0f2430');
    r.setAttribute('stroke', active ? '#9fdcf5' : '#2f5d73');
    r.setAttribute('stroke-width', active ? 2 : 1.5);
  }
  $('seatQuote').setAttribute('opacity', clamp((t - 22.6) / 0.7).toFixed(3));

  // ---- 角色构图 ----
  let px = 960, py = 96, scale = 1;
  if (talking) { scale = 0.66; px = 1010; py = 268; }          // 对话时缩小，给气泡让位
  if (t >= 20 && t < 25) { py = 84; }                            // 坐姿重心上移
  if (t >= 25) { scale = 0.94; px = 1010; py = 120; }            // 片尾略收
  const fp = $('petFrame');
  fp.setAttribute('transform', `matrix(${scale} 0 0 ${scale} ${(px - 960 * scale).toFixed(2)} ${(py - 96 * scale).toFixed(2)})`);

  // ---- 指针与点击波纹 ----
  const curVisible = t >= 9.2 && t < 13.4;
  $('cursor').setAttribute('opacity', curVisible ? 1 : 0);
  if (curVisible) {
    const h = hit();
    let x = h.x, y = h.y - 70;
    if (t < 9.7) {
      x = mix(700, h.x, ease((t - 9.2) / 0.5));
      y = mix(600, h.y - 70, ease((t - 9.2) / 0.5));
    } else if (t >= 11.3) {
      x = 400;
      y = mix(300, 150, ease((t - 11.3) / 1.8));
    }
    const cx = px + x * scale;
    const cy = py + y * scale;
    $('cursor').setAttribute('transform', `translate(${cx.toFixed(1)} ${cy.toFixed(1)}) scale(${scale.toFixed(2)})`);
    $('clickRing').setAttribute('cx', cx.toFixed(1));
    $('clickRing').setAttribute('cy', cy.toFixed(1));
    $('clickCore').setAttribute('cx', cx.toFixed(1));
    $('clickCore').setAttribute('cy', cy.toFixed(1));
  }
  // 两次点击各自一个扩散环
  let ringOp = 0, ringR = 20, coreOp = 0;
  for (const c of [9.7, 11.3]) {
    const p = clamp((t - c) / 0.55);
    if (t >= c && p < 1) { ringOp = Math.max(ringOp, 1 - p); ringR = Math.max(ringR, 18 + 46 * easeOut(p)); }
    if (t >= c && t < c + 0.18) coreOp = 1 - clamp((t - c) / 0.18);
  }
  $('clickRing').setAttribute('opacity', ringOp.toFixed(3));
  $('clickRing').setAttribute('r', ringR.toFixed(1));
  $('clickCore').setAttribute('opacity', coreOp.toFixed(3));

  // ---- 底部进度与说明 ----
  $('progress').setAttribute('stroke-dasharray', '1680');
  $('progress').setAttribute('stroke-dashoffset', (1680 * (1 - clamp(t / 30))).toFixed(2));
  $('bottomLabel').textContent =
    t >= 25 ? 'Asryto · 亚托利 · 2026' : '亚托利 · 基于 Coopanion 的发布动画';
}

// 每帧先以 60 Hz 推进角色逻辑，再把 SVG 场景对齐到目标时间
window.renderAt = async (time) => {
  if (time < sim - 0.001) await reset();
  while (sim < time - 1e-6) {
    const next = Math.min(time, sim + 1 / 60);
    while (eventIndex < schedule.length && schedule[eventIndex][0] <= next + 1e-7) {
      schedule[eventIndex++][1]();
    }
    // 提起阶段持续送 move 事件，真实拖拽才算成立
    if (next >= 11.35 && next < 13.1) {
      body.pointer('move', { x: 400, y: mix(300, 150, ease((next - 11.3) / 1.8)), t: next * 1000 });
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

// 手动审阅模式（?review=1）
if (new URLSearchParams(location.search).has('review')) {
  $('reviewControls').style.display = 'block';
  $('reviewSeek').onclick = () => { playing = false; window.renderAt(Number($('reviewTime').value)); };
  $('reviewPlay').onclick = () => { playing = !playing; lastPlay = performance.now(); };
  const frame = async (now) => {
    if (playing) {
      const t = sim + (now - lastPlay) / 1000;
      if (t < 30) await window.renderAt(t); else playing = false;
    }
    lastPlay = now;
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
}
