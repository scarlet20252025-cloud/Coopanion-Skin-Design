"""Start an isolated local server, exercise the real pack and write bound QA evidence."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import argparse
import json
import sys
import threading
import flow
import project
import qa

def plan(manifest, full=False):
    words={v['id']:v for v in manifest['vocab']}
    if not all(w in words for w in ['neutral','stand','wave','sit','happy','run']): raise ValueError('This QA profile needs neutral/stand/wave/sit/happy/run; define a profile for another adapter')
    selected=list(words) if full else [w for w in ['neutral','wave','flap','dance','sit','dizzy','turn'] if w in words]
    cases=[]
    for word in selected:
        duration=max(3.2,min(12,words[word]['seconds']+.4))
        cases.append({'id':word,'steps':[{'word':word,'phase':'action','seconds':duration,'samples':[0,.3,.8,duration]}, {'word':'stand','phase':'recovery','seconds':1.2,'samples':[.4,1.2]}]})
    for name,sequence in [('sit-happy-stand',['sit','happy','stand']),('run-wave-neutral',['run','wave','neutral'])]:
        cases.append({'id':name,'steps':[{'word':w,'phase':'recovery' if i==2 else str(i),'seconds':1.5 if w!='wave' else 3.2,'samples':[.4,1.5 if w!='wave' else 3.2]} for i,w in enumerate(sequence)]})
    cases.append({'id':'pointer','pointer':True})
    expected=[]
    for direction in [1,-1]:
        for case in cases:
            if case.get('pointer'):
                expected.extend(f'{direction}:pointer:{phase}' for phase in ['click','held','released','recovery'])
            else:
                for step in case['steps']:
                    expected.extend(f'{direction}:{case["id"]}:{step["phase"]}:{t}' for t in step['samples'])
    return {'cases':cases,'expected':expected}

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def collect(job,browser=None,full=False):
    from playwright.sync_api import sync_playwright
    directory,state,pack=flow.load(job);code,report=flow.validate(directory,state,pack)
    if code:raise ValueError('Machine check failed; see machine.json')
    before=flow.fingerprint(pack);test_plan=plan(project.read(pack/'figure.json'),full)
    flow.write(directory/'qa-plan.json',test_plan)
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(project.ROOT)))
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    errors=[];requests=[]
    try:
        with sync_playwright() as p:
            with p.chromium.launch(executable_path=browser) as b:
                page=b.new_page(viewport={'width':1200,'height':1100})
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('response',lambda r:requests.append(f'{r.status}: {r.url}') if r.status>=400 else None)
                page.goto(f'http://127.0.0.1:{server.server_port}/preview/engineering.html?pack={state["pack"]}')
                page.wait_for_function('window.engineeringReady === true',timeout=60000)
                page.set_default_timeout(180000)
                data=page.evaluate('plan => window.runEngineeringQA(plan)',test_plan)
        if flow.fingerprint(pack)!=before:raise ValueError('Candidate changed during capture; retry after editing stops')
        data.update(schema=2,pack_fingerprint=before,expected=test_plan['expected'],page_errors=errors,request_errors=requests)
        raw=directory/'qa-frames.json';flow.write(raw,data)
        result=qa.build(raw,directory/'qa');flow.write(directory/'qa.json',result)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        print('Review contacts and full images; fill review-template.json using these two hashes:')
        print(json.dumps({'qa_sha256':result['input_sha256'],'pack_fingerprint':before},indent=2))
        return 0 if result['machine_passed'] else 1
    finally:server.shutdown();server.server_close();worker.join(timeout=2)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--job',required=True);parser.add_argument('--browser',help='Existing Chromium/Edge executable; otherwise Playwright Chromium');parser.add_argument('--full',action='store_true',help='Exercise every declared word, plus transitions and pointer flow')
    args=parser.parse_args()
    try:return collect(args.job,args.browser,args.full)
    except ImportError:print('Install tools: uv sync --project engineering; uv run --project engineering playwright install chromium',file=sys.stderr);return 1
    except Exception as e:print('QA failed: '+str(e),file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
