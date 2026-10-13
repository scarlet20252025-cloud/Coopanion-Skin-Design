"""Extract generated component sheets and assemble the native Coopanion rig.

Artwork comes from imagegen. This script only extracts/masks, sizes and packs it.
Motion code is adapted from the pinned Pal-AI-Lab whale figure (AGPL-3.0).
"""
from pathlib import Path
import argparse
import json
import shutil
import zipfile
import io
import hashlib
import xml.etree.ElementTree as ET
import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'characters/original-01'
PACK = ROOT / 'packs/gpt-dragon'


def save_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def clean(im, keep=1):
    a = np.array(im.convert('RGBA')).copy()
    # Generated transparent sheets have disconnected alpha=1 noise. Never binarize
    # the character: preserve antialiasing around the connected opaque components.
    n, labels, stats, _ = cv2.connectedComponentsWithStats((a[:, :, 3] > 32).astype('uint8'), 8)
    ids = sorted(range(1, n), key=lambda i: stats[i, cv2.CC_STAT_AREA], reverse=True)[:keep]
    if not ids:
        raise ValueError('Empty atlas crop')
    mask = np.isin(labels, ids).astype('uint8')
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
    a[:, :, 3] = np.where((mask != 0) & (a[:, :, 3] > 8), a[:, :, 3], 0)
    a[a[:, :, 3] == 0] = 0
    im = Image.fromarray(a)
    return im.crop(im.getbbox())


def crop_sheet(sheet, box, keep=1):
    # Atlas specification coordinates use a 1254 square; scale to actual output.
    w, h = sheet.size
    b = tuple(round(v * (w if i % 2 == 0 else h) / 1254) for i, v in enumerate(box))
    return clean(sheet.crop(b), keep)


def sized(im, size):
    return im.resize(tuple(max(1, round(x)) for x in size), Image.Resampling.LANCZOS)


def main():
    raise SystemExit('已停用：独立生成分件 + 上游五官坐标导致形象失真。见 docs/RIG_FAILURE_REVIEW.md；须从母版原位拆层后另建构建流程。')
    ap = argparse.ArgumentParser()
    ap.add_argument('--upstream', type=Path, default=ROOT.parent / 'Coopanion-reference')
    args = ap.parse_args()
    upstream = args.upstream / 'packages/cortico-world-desktop-pet'
    source = upstream / 'web/whale'
    for d in ('tex', 'feat', 'thumbs'):
        (PACK / d).mkdir(parents=True, exist_ok=True)
    vendor = ROOT / 'preview/vendor'
    (vendor / 'kit').mkdir(parents=True, exist_ok=True)
    for name in ('body.js', 'rig.js'):
        shutil.copyfile(upstream / 'web/kit' / name, vendor / 'kit' / name)
    shutil.copyfile(upstream / 'web/sound.js', vendor / 'sound.js')
    shutil.copyfile(args.upstream / 'LICENSE', ROOT / 'LICENSE')
    shutil.copyfile(args.upstream / 'LICENSE', PACK / 'LICENSE')
    shutil.copyfile(source / 'figure.js', ROOT / 'preview/vendor/whale-figure.upstream.js')
    model = json.loads((source / 'model.json').read_text(encoding='utf-8'))
    sheet = Image.open(ART / 'rig-atlas-v003.png')
    rects = {
        'hair_back': (8, 5, 324, 345), 'face': (340, 55, 635, 316),
        'bangs': (635, 15, 972, 337), 'torso_up': (1005, 49, 1240, 315),
        'skirt': (5, 355, 370, 641), 'arm_near': (375, 351, 565, 630),
        'arm_far': (709, 352, 916, 637), 'leg_back': (1023, 330, 1203, 639),
        'leg_front': (85, 648, 257, 942), 'tail': (327, 649, 634, 930),
        'fin_near': (630, 649, 955, 904), 'fin_far': (963, 642, 1254, 900),
        'horns': (5, 998, 325, 1227), 'ahoge': (377, 1000, 613, 1205),
        'bow': (724, 929, 889, 1237), 'skirt_sit': (899, 968, 1254, 1247),
    }
    images = {k: crop_sheet(sheet, b, 2 if k == 'horns' else 1) for k, b in rects.items()}
    # Placement in the upstream 256 logical-unit coordinate frame.
    placements = {
        'hair_back': ([42, 39, 158, 173], 1, 'hairSway'),
        'tail': ([27, 187, 86, 61], 1.5, 'tailBend'),
        'fin_near': ([43, 151, 69, 47], 2, 'finNear'),
        'fin_far': ([163, 151, 42, 40], 2.1, 'finFar'),
        'leg_front': ([131, 198, 30, 58], 3, 'legFront'),
        'leg_back': ([99, 198, 31, 58], 4, 'legBack'),
        'arm_far': ([144, 160, 36, 57], 4.5, 'armFar'),
        'torso_up': ([105, 145, 53, 47], 5, 'waist'),
        'skirt': ([78, 181, 108, 54], 5.2, 'skirt'),
        'skirt_sit': ([63, 182, 137, 54], 5.3, 'skirtSit'),
        'arm_near': ([82, 158, 45, 62], 6, 'armNear'),
        'face': ([79, 66, 112, 94], 8, 'headMid'),
        'horns': ([59, 25, 137, 62], 12, 'headMid'),
        'bangs': ([58, 42, 149, 129], 13, 'bangsSway'),
        'bow': ([172, 87, 22, 43], 13.8, 'headMid'),
        'ahoge': ([115, 12, 42, 27], 14, 'ahoge'),
    }
    model['parts'] = []
    for name, (box, z, parent) in placements.items():
        images[name].save(PACK / 'tex' / f'{name}.png')
        model['parts'].append(dict(id=name, tex=name, box=box, z=z, parent=parent, grid=[8, 10]))
    # Waist knot uses the same designed emblem, with independent seated positioning.
    for name, box, parent in [('waist_bow_front', [136, 181, 16, 31], 'skirt'),
                              ('waist_bow_sit_front', [133, 183, 16, 27], 'skirtSit')]:
        images[name] = images['bow']
        images[name].save(PACK / 'tex' / f'{name}.png')
        model['parts'].append(dict(id=name, tex=name, box=box, z=5.55, parent=parent, grid=[4, 6]))
    model['pivots'].update(body=[128, 256], waist=[131, 183], neck=[139, 150],
                           armNear=[119, 165], armFar=[149, 167],
                           legBack=[113, 204], legFront=[144, 204], tail=[102, 198],
                           finNear=[109, 157], finFar=[163, 156], ahoge=[128, 40])
    model['schemes'] = [dict(id='gpt', brand='GPT 龙娘', accent='#a48ad3')]
    model['outfits'] = [dict(id='dress')]
    model['view'] = [-12, -8, 268, 272]

    faces = Image.open(ART / 'face-atlas-v002.png')
    names = ['eyeL', 'eyeR', 'neutral_mouth', 'happy_mouth',
             'happy_eyeL', 'happy_eyeR', 'sleep_eyeL', 'sleep_eyeR',
             'drag_eyeL', 'drag_eyeR', 'love_eyeL', 'love_eyeR',
             'dizzy_eyeL', 'dizzy_eyeR', 'surprised_eyeL', 'surprised_eyeR']
    facial = {}
    for i, name in enumerate(names):
        x, y = i % 4 * 313.5, i // 4 * 313.5
        facial[name] = crop_sheet(faces, (x, y, x + 313.5, y + 313.5))
    sprites = model['feat']['sprites']
    for name, box in sprites.items():
        base = facial.get(name)
        if base is None:
            base = facial['neutral_mouth'] if name in ('sleep_mouth', 'dizzy_mouth') else facial['happy_mouth']
        sized(base, (box[2] - box[0], box[3] - box[1])).save(PACK / 'feat' / f'{name}.png')

    # Keep independently moving iris, sclera and upper lash. No face textures from upstream.
    for k in ('eyeL', 'eyeR'):
        e = model['feat']['eyes'][k]
        full = facial[k]
        a = np.array(full)
        hsv = cv2.cvtColor(a[:, :, :3], cv2.COLOR_RGB2HSV)
        h, w = a.shape[:2]
        yy, xx = np.mgrid[:h, :w]
        # Iris lies below the lash and is more chromatic than the grey-lavender lash.
        iris_mask = ((hsv[:, :, 1] > 53) & (yy > h * .24) &
                     (xx > w * .25) & (a[:, :, 3] > 100)).astype('uint8')
        n, lab, st, _ = cv2.connectedComponentsWithStats(iris_mask, 8)
        biggest = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        iris_mask = (lab == biggest).astype('uint8')
        contours, _ = cv2.findContours(iris_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(iris_mask, contours, -1, 1, cv2.FILLED)
        ia = a.copy(); ia[:, :, 3] = ia[:, :, 3] * iris_mask
        iris = Image.fromarray(ia); iris = iris.crop(iris.getbbox())
        # Opaque generated neutral eye supplies the outer contour. Hidden iris area
        # is filled with the adjacent sclera colour so gaze motion never leaves a hole.
        ball = a.copy(); ball[iris_mask != 0, :3] = [251, 250, 255]
        lash_mask = (yy < h * .38) & (hsv[:, :, 2] < 215) & (a[:, :, 3] > 32)
        la = a.copy(); la[:, :, 3] = np.where(lash_mask, la[:, :, 3], 0)
        lash = Image.fromarray(la); lash = lash.crop(lash.getbbox())
        # Use actual generated proportions within the upstream face positions.
        for tag, im in [('ball', Image.fromarray(ball)), ('iris', iris), ('lash', lash)]:
            b = e[tag]
            sized(im, (b[2] - b[0], b[3] - b[1])).save(PACK / 'feat' / f'{k}_{tag}.png')

    save_json(PACK / 'model.json', model)
    js = (source / 'figure.js').read_text(encoding='utf-8')
    js = '// Adapted for GPT Dragon; Pal-AI-Lab original, AGPL-3.0-or-later.\n' + js
    js = js.replace('createWhaleFigure', 'createDragonFigure').replace('createWhaleBody', 'createDragonBody')
    js = js.replace("import('../kit/rig.js')", "import('../../preview/vendor/kit/rig.js')")
    # The wings belong to the torso, not the head; timing and spring constants stay upstream.
    js = js.replace("finNear: { kind: 'rot', parent: 'headMid'", "finNear: { kind: 'rot', parent: 'waist'")
    js = js.replace("finFar: { kind: 'rot', parent: 'headBack'", "finFar: { kind: 'rot', parent: 'waist'")
    js = js.replace("const INK = '#5a2330';", "const INK = '#79658f';")
    js = js.replace('    anchors: {', '    extent: [24, 10, 210, 258],\n    hits: [[135, 100, 65], [131, 190, 47], [113, 241, 18], [146, 241, 18]],\n    anchors: {')
    (PACK / 'figure.js').write_text(js, encoding='utf-8')
    manifest = json.loads((source / 'figure.json').read_text(encoding='utf-8'))
    manifest.update(id='gpt-dragon', version='0.1.0', name={'zh': 'GPT 龙娘', 'en': 'GPT Dragon Girl'},
                    about={'zh': '银白渐变长发、浅紫龙角、龙翼与斑点卷尾的 Q 版龙娘；白色长袖短裙与结环饰物。',
                           'en': 'A silver-haired chibi dragon girl with lavender horns, wings and a spotted curled tail, wearing a white dress.'},
                    author='Coopanion-Skin-Design', license='AGPL-3.0-or-later',
                    credits=[{'role': '行为与动画源代码', 'name': 'Pal-AI-Lab / Coopanion'},
                             {'role': '参考形象与方向', 'name': '用户提供'},
                             {'role': '生成与分件适配', 'name': 'imagegen + Codex'}],
                    entry='figure.js', export='createDragonBody', model='model.json', thumb='thumbs/gpt.png',
                    axes=[{'id': 'scheme', 'name': {'zh': '配色', 'en': 'Palette'}, 'options': [
                        {'id': 'gpt', 'name': {'zh': '银白浅紫', 'en': 'Silver lavender'}, 'thumb': 'thumbs/gpt.png'}]}])
    manifest.pop('presets', None)
    # Vocab timing and IDs remain upstream, descriptions reflect the dragon anatomy.
    for word in manifest['vocab']:
        word['about'] = {lang: text.replace('鲸鳍', '龙翼').replace('whale fins', 'dragon wings')
                         for lang, text in word['about'].items()}
    save_json(PACK / 'figure.json', manifest)
    thumb = clean(Image.open(ART / 'gpt-dragon-master-v005.png'))
    thumb.thumbnail((256, 256), Image.Resampling.LANCZOS)
    thumb.save(PACK / 'thumbs/gpt.png')
    # Full-resolution editable layer interchange, same locations as the runtime.
    ora_path = ART / 'gpt-dragon-layers.ora'
    root = ET.Element('image', w='1120', h='1120', name='GPT Dragon native rig')
    stack = ET.SubElement(root, 'stack')
    merged = Image.new('RGBA', (1120, 1120))
    with zipfile.ZipFile(ora_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('mimetype', 'image/openraster')
        for p in sorted(model['parts'], key=lambda p: p['z']):
            if p['id'] in ('skirt_sit', 'waist_bow_sit_front'):
                continue
            x, y, w, h = p['box']
            im = sized(images[p['id']], (w * 4, h * 4))
            src = f"data/{p['id']}.png"
            buf = io.BytesIO(); im.save(buf, format='PNG'); zf.writestr(src, buf.getvalue())
            layer = ET.Element('layer', name=p['id'], src=src, x=str(round((x + 12) * 4)),
                               y=str(round((y + 8) * 4)), opacity='1.0', visibility='visible',
                               **{'composite-op': 'svg:src-over'})
            stack.insert(0, layer)
            merged.alpha_composite(im, (int(layer.attrib['x']), int(layer.attrib['y'])))
        zf.writestr('stack.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))
        buf = io.BytesIO(); merged.save(buf, format='PNG'); zf.writestr('mergedimage.png', buf.getvalue())
    merged.save(ART / 'rig-assembly-no-face.png')
    save_json(ROOT / 'preview/vendor/source.json', {
        'repository': 'https://github.com/Pal-AI-Lab/Coopanion',
        'commit': '91293b3e31b94397a8f2eb79dffec40f4c6d8817',
        'license': 'AGPL-3.0-or-later',
        'motion_changes': 'Wing attachment, identity, geometry and textures; spring and motion equations retained.',
        'artwork': 'Generated from user references; no upstream whale texture copied.',
    })
    print(json.dumps({'parts': len(model['parts']), 'vocab': len(manifest['vocab']),
                      'pack': str(PACK), 'layer_source': str(ora_path)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
