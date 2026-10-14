"""Render this repository's isolated SVG movie; never operates a user's browser session."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')

def main():
    from playwright.sync_api import sync_playwright
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:4319/promo/assets/src/01-film/01-film.html')
    parser.add_argument('--browser',help='Existing browser executable; otherwise use installed Chromium')
    parser.add_argument('--ffmpeg',default=shutil.which('ffmpeg'))
    parser.add_argument('--out',default='promo/assets/GPT 龙娘宣传片.mp4')
    parser.add_argument('--music',help='Authorized optional WAV/music file')
    parser.add_argument('--duration',type=float,default=30)
    parser.add_argument('--fps',type=int,default=30)
    parser.add_argument('--samples',help='Comma-separated key-frame times; no encoding')
    args=parser.parse_args()
    if urlparse(args.url).hostname not in ['127.0.0.1','localhost']:
        parser.error('Only an isolated localhost movie page is supported')
    if not 0<args.duration<=30 or not 1<=args.fps<=60:parser.error('Use duration (0,30] and fps [1,60]')
    out=(ROOT/args.out).resolve()
    if not out.is_relative_to(ROOT):parser.error('Output must stay in this repository')
    if not args.samples and not args.ffmpeg:parser.error('Supply --ffmpeg or add it to PATH')
    out.parent.mkdir(parents=True,exist_ok=True);qa=out.parent/'qa';qa.mkdir(exist_ok=True)
    times=[float(t) for t in args.samples.split(',')] if args.samples else [i/args.fps for i in range(round(args.duration*args.fps))]
    if not times or any(not 0<=t<30 for t in times):parser.error('Frame times must be in [0,30)')
    with tempfile.TemporaryDirectory(prefix='.render-',dir=out.parent) as temporary:
        frames=Path(temporary)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=args.browser)
            page=browser.new_page(viewport={'width':1920,'height':1080})
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(args.url);page.wait_for_function('window.promoReady === true',timeout=60000);page.evaluate('document.fonts.ready')
            page.evaluate('() => {for(const a of document.getAnimations())a.pause()}')
            states=[]
            for i,t in enumerate(times):
                page.evaluate('async t => {for(const a of document.getAnimations())a.currentTime=t*1000;await window.renderAt(t)}',t)
                target=qa/f'sample-{t:05.2f}.png' if args.samples else frames/f'frame_{i:05d}.png'
                page.screenshot(path=str(target))
                if args.samples:states.append(page.evaluate('window.promoState'))
                if (i+1)%30==0 or i+1==len(times):print(f'frame {i+1}/{len(times)}',flush=True)
            final=page.evaluate('window.promoState');browser.close()
        if errors:raise RuntimeError('Movie page errors: '+' | '.join(errors))
        if any(x['accepted'] is False for x in final['checks']):raise RuntimeError('Movie action rejected')
        (qa/'render-state.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if args.samples:
            (qa/'states.json').write_text(json.dumps(states,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            print('Samples ready; review full character and text before encoding');return
        silent=frames/'silent.mp4'
        subprocess.run([args.ffmpeg,'-y','-v','error','-framerate',str(args.fps),'-i',str(frames/'frame_%05d.png'),'-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(silent)],check=True)
        if args.music:
            music=Path(args.music).resolve()
            subprocess.run([args.ffmpeg,'-y','-v','error','-i',str(silent),'-i',str(music),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k','-af','loudnorm=I=-24:TP=-3:LRA=7','-ar','48000','-t',str(args.duration),'-movflags','+faststart','-metadata','artist=Asryto',str(out)],check=True)
        else:shutil.copy2(silent,out)
        subprocess.run([args.ffmpeg,'-v','error','-i',str(out),'-f','null','-'],check=True,stdout=subprocess.DEVNULL)
        report={'duration_seconds':args.duration,'frames':len(times),'fps':args.fps,'resolution':[1920,1080],'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'full_decode':'passed','page_errors':errors,'visual_review':'required','music':bool(args.music),'actions_accepted':len(final['checks'])}
        (qa/'video-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(str(out))

if __name__=='__main__':main()
