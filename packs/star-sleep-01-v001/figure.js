// 星眠 v0.1.0: single-sprite Coopanion API 2 adapter.
export async function createStarSleepBody(base, opts) {
  const model = opts.model;
  const doc = opts.host.root.ownerDocument;
  const NS = 'http://www.w3.org/2000/svg';
  const load = opts.loadImage || (url => new Promise((resolve, reject) => {
    const image = new Image(); image.onload = () => resolve(image); image.onerror = reject; image.src = url;
  }));
  const source = await load(opts.asset ? opts.asset(model.parts[0].file) : new URL(model.parts[0].file, base));
  const [width, height] = model.canvas;
  const canvas = doc.createElement('canvas');
  canvas.width = source.naturalWidth || source.width;
  canvas.height = source.naturalHeight || source.height;
  canvas.getContext('2d').drawImage(source, 0, 0);
  const texture = canvas.toDataURL();
  const s = model.logo_scale;
  const tx = 128 - model.center_x * s;
  const ty = 256 - model.feet_y * s;
  const convert = ([x, y]) => [tx + x * s, ty + y * s];
  let mounted = null, root = null, pose = 'standing';
  const make = (tag, attrs = {}) => {
    const el = doc.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
    return el;
  };
  const figure = {
    colors: { z: model.accent },
    extent: [...convert(model.bounds.slice(0, 2)), ...convert(model.bounds.slice(2))],
    hits: model.hits.map(([x, y, r]) => [...convert([x, y]), r * s]),
    anchors: Object.fromEntries(Object.entries(model.anchors).map(([key, value]) => [key, [...convert(value.slice(0, 2)), ...value.slice(2).map(n => n * s)]])),
    draw(group, face, frame) {
      if (mounted !== group) {
        group.replaceChildren();
        root = make('g', { transform: `translate(${tx} ${ty}) scale(${s})` });
        root.append(make('image', { x: 0, y: 0, width, height, href: texture }));
        group.append(root);
        mounted = group;
      }
      pose = frame.sit > 0.5 ? (frame.mode === 'dizzy' ? 'dizzy' : 'seated') : 'standing';
      // Original illustration stays intact; only official whole-body movement is active.
      // Independent limb, blink, expression and seated artwork are intentionally not fabricated.
    },
    dispose() { mounted = null; root = null; }
  };
  const native = opts.kit.createBody(opts.host, { figure });
  return {
    ...native,
    visualState: () => ({ pose }),
    words: [...model.words],
    do: word => model.words.includes(word) ? native.do(word) : false
  };
}
