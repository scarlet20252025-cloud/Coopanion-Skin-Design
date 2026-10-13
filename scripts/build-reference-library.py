"""Index sampled official frames; PNGs remain lossless, WebP is navigation only."""
from pathlib import Path
import json,html,hashlib
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tools-local/whale-reference-91293b3'
rows=[]
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
for timeline in sorted(OUT.glob('*/timeline.json')):
    meta=json.loads(timeline.read_text(encoding='utf-8'))
    paths=sorted(timeline.parent.glob('????.png'))
    if len(paths)!=meta['count']: raise ValueError(f'Frame count mismatch: {timeline}')
    images=[Image.open(p).convert('RGBA') for p in paths]
    empty=[i for i,im in enumerate(images) if im.getbbox() is None]
    if empty: raise ValueError(f'Empty frames: {timeline}: {empty}')
    # 30 fps playback copy; all 60 fps source PNGs and timeline retained unchanged.
    frames=[]
    for im in images[::2]:
        bg=Image.new('RGBA',im.size,(37,36,43,255));bg.alpha_composite(im);frames.append(bg.convert('RGB'))
    if not (timeline.parent/'preview.webp').exists():
        frames[0].save(timeline.parent/'preview.webp',save_all=True,append_images=frames[1:],duration=[33,33,34]*(len(frames)//3)+[33]*(len(frames)%3),loop=0,quality=88,method=3)
    contact=Image.new('RGB',(224*6,244*2),(244,242,249));d=ImageDraw.Draw(contact)
    for j in range(12):
        i=round(j*(len(images)-1)/11);im=images[i].resize((224,224),Image.Resampling.LANCZOS)
        x,y=(j%6)*224,(j//6)*244;contact.paste(im,(x,y),im)
        d.text((x+8,y+222),f'{i:04d} | {(i+1)/60:.3f}s',font=font,fill='#51435f')
    contact.save(timeline.parent/'contact.png')
    meta['checks']={'expected_frames':meta['count'],'actual_frames':len(paths),'nonempty':True,'unique_png_hashes':len({hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})}
    row={k:v for k,v in meta.items() if k!='frames'};rows.append(row)
    print(meta['id'],len(paths),flush=True)
(OUT/'index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
cards=[]
for r in rows:
    name=r.get('names',{}).get('zh',[r['id']])[0]
    cards.append(f'''<article><h2>{html.escape(name)} <small>{r['id']}</small></h2><img src="{r['id']}/preview.webp" loading="lazy"><p>{r['count']} 帧 · {r['seconds']} 秒 · PNG 60 fps</p><a href="{r['id']}/contact.png">关键帧总览</a> · <a href="{r['id']}/timeline.json">时间轴</a><details><summary>逐帧查看</summary><input type="range" min="0" max="{r['count']-1}" value="0" data-id="{r['id']}"><output>0000</output><img class="frame" src="{r['id']}/0000.png"></details></article>''')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>鲸鱼娘逐帧参考库</title><style>body{font:14px/1.6 system-ui;background:#f5f3f9;color:#42384f;margin:24px}h1{font-size:24px}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:18px}article{background:white;padding:16px;border-radius:14px}h2{font-size:17px}small{color:#908299;font-size:12px}img{width:100%;background:#25242b;border-radius:8px}a{color:#77559b}input{width:75%}</style><h1>鲸鱼娘逐帧参考库</h1><p>官方原始模型 · 91293b3 · DeepSeek 女仆装。有限时间窗口按 60 fps 连续采样；动态图为 30 fps 浏览副本。仅作本地参考，未混入龙娘素材。</p><p>COUNT 项 / TOTAL 张 PNG。展开卡片可拖动查看每一帧。</p><main>CARDS</main><script>document.querySelectorAll('input').forEach(el=>el.oninput=()=>{let n=String(el.value).padStart(4,'0');el.nextElementSibling.textContent=n;el.parentElement.querySelector('.frame').src=el.dataset.id+'/'+n+'.png';});</script></html>'''
page=page.replace('COUNT',str(len(rows))).replace('TOTAL',str(sum(r['count'] for r in rows))).replace('CARDS',''.join(cards))
(OUT/'index.html').write_text(page,encoding='utf-8')
print('Library complete:',len(rows),sum(r['count'] for r in rows))
