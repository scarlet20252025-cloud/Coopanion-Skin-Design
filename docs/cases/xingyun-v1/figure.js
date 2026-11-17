const SVG = 'http://www.w3.org/2000/svg';
const XHTML = 'http://www.w3.org/1999/xhtml';
const TAU = Math.PI * 2;
export const WALK_SWING_HZ = 1.48;
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const radians = degrees => degrees * Math.PI / 180;
const smooth = t => { const s = clamp(t, 0, 1); return s * s * (3 - 2 * s); };

function swingLeg(leg, low, inMotion, held, t, index) {
  if (held) {
    const kick = Math.sin(t * 14 + index * Math.PI);
    return { angle: kick * 4, lift: 7 + Math.max(0, kick) * 5 };
  }
  if (!inMotion || !leg) return { angle: 0, lift: 0 };
  // Keep the knee end under the skirt. The kit's stride is much wider
  // than the star traveler's painted pose can support.
  const advance = clamp((leg[2] - leg[0]) / 13, -1, 1);
  const upward = clamp((241 - leg[3]) / 13, 0, 1);
  return { angle: -advance * (index === 1 ? 3.1 : 4.2), lift: upward * 12 + low };
}

export function solvePose(frame, controls = {}) {
  const t = frame.t ?? 0;
  const mode = frame.mode ?? 'idle';
  const slowGait = mode === 'walk';
  const walking = slowGait || mode === 'run';
  const held = mode === 'drag' || mode === 'air';
  const gesture = frame.gesture;
  const phase = gesture?.k ?? 0;
  const nod = gesture?.kind === 'nod' ? Math.sin(phase * TAU) ** 2 * (1 - phase * .25) : 0;
  const shake = gesture?.kind === 'shake'
    ? Math.sin(phase * TAU * 2) * smooth(phase / .14) * smooth((1 - phase) / .3)
    : 0;
  if (controls.still) {
    return { head: 0, neckY: 0, swayL: 0, swayR: 0, rootY: 0,
      leftArm: 0, rightArm: 0, legs: [{ angle: 0, lift: 0 }, { angle: 0, lift: 0 }],
      blinkL: +Boolean(controls.closedEyes), blinkR: +Boolean(controls.closedEyes), mouth: 0 };
  }
  const look = frame.look ?? [0, 0];
  const head = clamp(.48 * look[0] + .18 * look[1] + .74 * Math.sin(t * 1.7)
    + nod * 3.1 + shake * 3.6 + (held ? (frame.swing ?? 0) * .16 : 0), -4, 4);
  const phaseWalk = (frame.modeT ?? t) * TAU * WALK_SWING_HZ;
  const ramp = smooth((frame.modeT ?? 1) / .27);
  const rootY = slowGait ? (1 + Math.cos(phaseWalk * 2)) * 2.05 * ramp
    : walking ? clamp((frame.low ?? 0) * 1.8, 0, 8) : 0;
  const legs = [0, 1].map(i => {
    if (!slowGait) return swingLeg(frame.legs?.[i], rootY, walking, held, t, i);
    const cycle = phaseWalk + i * Math.PI;
    return { angle: -Math.sin(cycle) * (i === 0 ? 4.2 : 3.1) * ramp,
      lift: Math.max(0, Math.cos(cycle)) * 10 * ramp + rootY };
  });
  const walkSwing = legs[0].angle / 4.2;
  // A small negative counter rotation moves the pointed end outward
  // during the stride, so it clears the right shoe.
  const rightArm = walking ? -2.07 + walkSwing * .73
    : held ? -1.6 + .8 * Math.sin(t * 8)
      : -.33 + .55 * Math.sin(t * 1.85);
  const blink = clamp(frame.blink ?? 0, 0, 1);
  return {
    head, neckY: nod * 2.5, rootY, legs,
    swayL: -head * 1.15 + Math.sin(t * (walking ? 8.1 : 2.4)) * (walking ? 2.6 : 1.1),
    swayR: -head * 1.02 + Math.sin(t * (walking ? 8.1 : 2.4) - .55) * (walking ? 2.3 : 1.0),
    leftArm: walking ? walkSwing * 5.8 : held ? -5.2 + 2.4 * Math.sin(t * 11) : .75 * Math.sin(t * 2.2),
    rightArm,
    blinkL: blink, blinkR: blink,
    mouth: clamp((frame.talk ?? 0) * (.72 + .28 * Math.sin(t * 31)), 0, 1),
  };
}

function rotate(ctx, [x, y], degrees, dx = 0, dy = 0) {
  ctx.translate(x + dx, y + dy);
  ctx.rotate(radians(degrees));
  ctx.translate(-x, -y);
}

function pointAfter([x, y], [px, py], angle, dy = 0) {
  const c = Math.cos(radians(angle)), s = Math.sin(radians(angle));
  return [px + (x - px) * c - (y - py) * s, py + (x - px) * s + (y - py) * c + dy];
}

export async function createXingyunFigure(base, { model, asset, loadImage, controls = {} }) {
  if (!model || model.canvas[0] !== 1139 || model.canvas[1] !== 1381) {
    throw new Error('Xingyun requires a 1139×1381 model.');
  }
  const parts = Object.fromEntries(await Promise.all(Object.entries(model.parts).map(async ([id, part]) =>
    [id, { ...part, image: await loadImage(asset ? asset(part.file) : new URL(part.file, base)) }]
  )));
  const joint = model.joints;
  const [vx, vy, vw, vh] = model.view;
  const [gx, gy] = model.ground;
  const unit = model.unitsPerPixel;
  const u = x => 128 + (x - gx) * unit;
  const v = y => 256 + (y - gy) * unit;
  const pixelScale = .8;
  let foreign, canvas, ctx, scratch, pen, headCanvas, headPen, mounted;
  let prevTime, wink = 0, rest = 0, swayLeft = 0, swayRight = 0;
  let eyeFrames = '';

  function frameIndex(id, progress) {
    return Math.round(clamp(progress, 0, 1) * (parts[id].count - 1));
  }

  function atlasFrame(context, id, index) {
    const {image, box: [x,y,w,h], columns} = parts[id];
    context.drawImage(image, index % columns * w, Math.floor(index / columns) * h,
      w,h,x,y,w,h);
  }

  function sprite(context, id) {
    const part = parts[id];
    context.drawImage(part.image, part.box[0], part.box[1]);
  }

  function mount(petG) {
    const doc = petG.ownerDocument;
    foreign = doc.createElementNS(SVG, 'foreignObject');
    foreign.setAttribute('x', u(vx));
    foreign.setAttribute('y', v(vy));
    foreign.setAttribute('width', vw * unit);
    foreign.setAttribute('height', vh * unit);
    foreign.setAttribute('pointer-events', 'none');
    foreign.dataset.figure = 'xingyun';
    canvas = doc.createElementNS(XHTML, 'canvas');
    canvas.width = Math.ceil(vw * pixelScale);
    canvas.height = Math.ceil(vh * pixelScale);
    canvas.style.cssText = 'display:block;width:100%;height:100%;';
    ctx = canvas.getContext('2d', { alpha: true });
    scratch = doc.createElement('canvas');
    [scratch.width, scratch.height] = [canvas.width, canvas.height];
    pen = scratch.getContext('2d', { alpha: true });
    headCanvas = doc.createElement('canvas');
    [headCanvas.width, headCanvas.height] = model.canvas;
    headPen = headCanvas.getContext('2d', { alpha: true });
    eyeFrames = '';
    if (!ctx || !pen || !headPen) throw new Error('Unable to open the Xingyun canvas.');
    foreign.appendChild(canvas);
    petG.prepend(foreign);
    mounted = petG;
  }

  function begin(context) {
    context.setTransform(1, 0, 0, 1, 0, 0);
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.setTransform(pixelScale, 0, 0, pixelScale, -vx * pixelScale, -vy * pixelScale);
    context.imageSmoothingEnabled = true;
    context.imageSmoothingQuality = 'medium';
  }

  function hand(id, cover, pivot, a, rootY) {
    begin(pen);
    pen.save();
    rotate(pen, pivot, a, 0, rootY);
    sprite(pen, id);
    pen.restore();
    pen.save();
    // The shoulder matte is fixed to the body, so it follows the bob
    // and stays in place while the arm rotates underneath.
    pen.translate(0, rootY);
    pen.globalCompositeOperation = 'destination-out';
    sprite(pen, cover);
    pen.restore();
    drawScratch();
  }

  function drawScratch() {
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.drawImage(scratch, 0, 0);
    ctx.restore();
  }

  function speech(context, energy) {
    if (energy < .025) return;
    const [x,y]=joint.mouth;
    context.save();
    context.globalAlpha = smooth(energy * 2);
    context.fillStyle = '#794e51';
    context.beginPath();
    context.ellipse(x, y+1, 6.7+energy*4, 1.4+energy*5, -.08, 0, TAU);
    context.fill();
    if (energy>.5) {
      context.fillStyle='#c77e7d';
      context.beginPath();
      context.ellipse(x, y+2.7, 5*energy, 2.4*energy, -.08, 0, TAU);
      context.fill();
    }
    context.restore();
  }

  function paintFace(left, right) {
    const key = left + ':' + right;
    if (key === eyeFrames) return;
    headPen.clearRect(0, 0, headCanvas.width, headCanvas.height);
    sprite(headPen, 'headOpen');
    for (const [id, index] of [['eyeLeft',left], ['eyeRight',right]]) {
      if (!index) continue;
      headPen.clearRect(...parts[id].box);
      atlasFrame(headPen, id, index);
    }
    eyeFrames = key;
  }

  function approach(value, target, step) {
    return value + clamp(target - value, -step, step);
  }

  function head(p, frame) {
    const time = frame.t ?? 0;
    const dt = prevTime === undefined ? 1 / 60 : clamp(time - prevTime, 0, .065);
    prevTime = time;
    const wantsWink = frame.face === 'wink';
    const wantsRest = frame.mode === 'sleep' || controls.closedEyes;
    wink = approach(wink, +wantsWink, dt / (wantsWink ? .075 : .105));
    rest = approach(rest, +Boolean(wantsRest), dt / (wantsRest ? .18 : .16));
    const change = wantsWink || wink > 0 ? 0 : frame.eyeClose ?? 0;
    const left = Math.max(p.blinkL, change, smooth(rest));
    const right = Math.max(p.blinkR, change, smooth(rest), smooth(wink));
    paintFace(frameIndex('eyeLeft', left), frameIndex('eyeRight', right));

    const follow = 1 - Math.exp(-dt * 8);
    swayLeft += (p.swayL - swayLeft) * follow;
    swayRight += (p.swayR - swayRight) * follow;
    ctx.save();
    rotate(ctx, joint.neck, p.head, 0, p.rootY + p.neckY);
    atlasFrame(ctx, 'lockLeftMotion', frameIndex('lockLeftMotion', .5 + swayLeft / 10));
    atlasFrame(ctx, 'lockRightMotion', frameIndex('lockRightMotion', .5 + swayRight / 10));
    ctx.restore();

    ctx.save();
    rotate(ctx, joint.neck, p.head, 0, p.rootY + p.neckY);
    ctx.drawImage(headCanvas, 0, 0);
    speech(ctx, p.mouth);
    ctx.restore();

    ctx.save();
    ctx.translate(0,p.rootY);
    sprite(ctx,'crow');
    ctx.restore();
  }

  function dot([x,y], color) {
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x,y,6.3,0,TAU);
    ctx.fill(); ctx.stroke();
  }

  function draw(petG, _face, frame) {
    if (mounted !== petG || !foreign.isConnected) mount(petG);
    const p = solvePose(frame,controls);
    begin(ctx);
    for (const [id,pivot,leg] of [
      ['legBack',joint.rightLeg,p.legs[1]], ['legNear',joint.leftLeg,p.legs[0]],
    ]) {
      ctx.save();
      rotate(ctx,pivot,leg.angle,0,p.rootY-leg.lift);
      sprite(ctx,id);
      ctx.restore();
    }
    ctx.save();
    ctx.translate(0,p.rootY); sprite(ctx,'body');
    ctx.restore();
    hand('leftArm','leftCover',joint.leftShoulder,p.leftArm,p.rootY);
    ctx.save();
    rotate(ctx,joint.rightShoulder,p.rightArm,0,p.rootY);
    sprite(ctx,'staff');
    ctx.restore();
    // The same pivot, angle and translation carry the hand and the staff.
    hand('rightArm','rightCover',joint.rightShoulder,p.rightArm,p.rootY);
    head(p, frame);
    if (controls.showJoints) {
      dot([joint.neck[0],joint.neck[1]+p.rootY], '#5073e1');
      dot([joint.leftShoulder[0],joint.leftShoulder[1]+p.rootY], '#5073e1');
      dot([joint.rightShoulder[0],joint.rightShoulder[1]+p.rootY], '#5073e1');
      dot(pointAfter(joint.grip,joint.rightShoulder,p.rightArm,p.rootY), '#d57d2c');
    }
  }

  return {
    draw,
    dispose() { foreign?.remove(); mounted = null; },
    gestures: ['nod','shake'],
    groupTilt(mode, tilt, lean) { return mode === 'drag' ? clamp(tilt,-11,11) : clamp(tilt+lean*.22,-3.5,3.5); },
    anchors: { gaze: [u(633),v(553)], bubble: [u(617),v(10)],
      z: [u(827),v(112)], hearts: [u(483),u(730),v(180)] },
    colors: { z: '#44aab7' },
    extent: [u(163),v(7),u(1080),v(1373)],
    hits: [[u(540),v(358),64], [u(601),v(780),43], [u(586),v(1105),35]],
  };
}

export async function createXingyunBody(base, opts) {
  const figure = await createXingyunFigure(base, opts);
  return opts.kit.createBody(opts.host,{ figure });
}
