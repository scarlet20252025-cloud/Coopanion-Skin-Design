import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createReadStream, existsSync } from 'node:fs';
import { mkdir, readFile, writeFile, rename, rm, stat } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import { setTimeout as sleep } from 'node:timers/promises';

const here = fileURLToPath(new URL('./',import.meta.url));
const root = resolve(here,'..');
const checkOnly = process.argv.includes('--check');
const coverOnly = process.argv.includes('--cover');
const edgePath = process.env.FILM_EDGE ?? 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const ffmpegPath = process.env.FILM_FFMPEG ?? 'C:/Program Files/Virtual Desktop Streamer/ffmpeg.exe';
const prefix = resolve(here,'.capture');
const profile = join(prefix,'edge-'+randomUUID());
const MIME = {'.html':'text/html','.js':'text/javascript','.json':'application/json',
  '.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp'};
const folders=['/xingyun-xingmian-film/','/delivery/coopanion-sheep-03-v2.0.4/pack/coopanion-sheep-03/',
  '/xingyun-v2/pack/xingyun-v2/','/xingyun-v2/vendor/Coopanion-web/'];
const server = createServer(async (req,res)=>{
  try{
    const path=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname);
    const file=resolve(root,'.'+path);
    if (!folders.some(p=>path.startsWith(p)) || !file.startsWith(root+sep) || !MIME[extname(file)]) {
      res.writeHead(404).end();
      return;
    }
    const info=await stat(file);
    if(!info.isFile()) throw Error('Not a file');
    res.writeHead(200,{'Content-Type':MIME[extname(file)],'Content-Length':info.size});
    createReadStream(file).pipe(res);
  }catch{
    res.writeHead(404).end();
  }
});

async function connect(url){
  const socket=new WebSocket(url);
  await new Promise((ok,bad)=>{
    socket.addEventListener('open',ok,{once:true});
    socket.addEventListener('error',bad,{once:true});
  });
  const responses=new Map();
  let id=0;
  socket.addEventListener('message',({data})=>{
    const msg=JSON.parse(data);
    if(msg.id){
      const pending=responses.get(msg.id);
      responses.delete(msg.id);
      if(msg.error)pending?.reject(Error(JSON.stringify(msg.error)));
      else pending?.resolve(msg.result);
    }else if(msg.method==='Runtime.exceptionThrown'){
      console.error(msg.params.exceptionDetails.exception?.description??msg.params.exceptionDetails.text);
    }
  });
  socket.addEventListener('close',()=>{
    for(const p of responses.values())p.reject(Error('Browser closed'));
    responses.clear();
  });
  return {
    close:()=>socket.close(),
    send(method,params={}){
      return new Promise((resolve,reject)=>{
        const key=++id;
        responses.set(key,{resolve,reject});
        socket.send(JSON.stringify({id:key,method,params}));
      });
    },
  };
}

async function value(cdp,expression){
  const reply=await cdp.send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
  if(reply.exceptionDetails) throw Error(reply.exceptionDetails.exception?.description??reply.exceptionDetails.text);
  return reply.result.value;
}

async function debuggingPort(browser){
  for(let i=0;i<140;i++){
    if(browser.exitCode!==null) throw Error('Edge exited before initialization: '+browser.exitCode);
    try{
      const p=+(await readFile(join(profile,'DevToolsActivePort'),'utf8')).split(/\r?\n/)[0];
      if(p)return p;
    }catch(error){ if(error.code!=='ENOENT')throw error; }
    await sleep(100);
  }
  throw Error('Edge did not open a DevTools port');
}

await mkdir(profile,{recursive:true});
server.listen(0,'127.0.0.1');
await once(server,'listening');
const page = coverOnly ? 'cover.html' : 'index.html';
const url=`http://127.0.0.1:${server.address().port}/xingyun-xingmian-film/${page}`;
const browser=spawn(edgePath,[
  '--headless=new','--remote-debugging-port=0','--no-first-run','--no-default-browser-check',
  '--disable-background-timer-throttling','--disable-renderer-backgrounding',
  '--disable-extensions','--use-angle=swiftshader','--enable-unsafe-swiftshader',
  '--enable-logging=stderr',`--user-data-dir=${profile}`,'about:blank',
],{windowsHide:true,stdio:['ignore','ignore',process.env.FILM_BROWSER_LOG?'inherit':'ignore']});
let cdp, encoder;
try{
  const port=await debuggingPort(browser);
  const info=(await fetch(`http://127.0.0.1:${port}/json/list`).then(r=>r.json())).find(x=>x.type==='page');
  cdp=await connect(info.webSocketDebuggerUrl);
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  await cdp.send('Emulation.setDeviceMetricsOverride',{width:coverOnly?1080:1440,height:810,deviceScaleFactor:checkOnly?1:4/3,mobile:false});
  await cdp.send('Page.navigate',{url});
  let config;
  for(let i=0;i<200;i++){
    try{
      config=await value(cdp,'window.filmReady || null');
      if(config)break;
    }catch(e){
      if(!String(e).includes('Execution context was destroyed'))throw e;
    }
    await sleep(50);
  }
  if(!config)throw Error('Could not initialize the film stage');
  console.log('Loaded both original rigs',config);
  if(coverOnly){
    const screenshot=await cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true});
    const destination=join(here,'星眠与星云 · 4比3封面.png');
    await writeFile(destination,Buffer.from(screenshot.data,'base64'));
    console.log(destination);
  }else{
  const out=join(here,'星眠与星云 · 桌面短片 v2.mp4');
  const temporaryOutput=join(prefix,'desktop-film-v2.mp4');
  let encoded;
  if(!checkOnly){
    const audio=join(prefix,'score.wav');
    if(!existsSync(audio)) throw Error('Run score.py before rendering.');
    encoder=spawn(ffmpegPath,['-hide_banner','-loglevel','warning','-y','-f','image2pipe','-framerate',String(config.fps),
      '-vcodec','mjpeg','-i','pipe:0','-i',audio,'-map','0:v:0','-map','1:a:0',
      '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',
      '-shortest','-movflags','+faststart',temporaryOutput],{windowsHide:true,stdio:['pipe','inherit','inherit']});
    encoded=once(encoder,'close');
  }
  const checkpoints = [75,165,180,228,273,311,338,403,529,586,643,673,686,728,878,974,1055];
  const sequence=checkOnly?checkpoints:Array.from({length:config.frames},(_,i)=>i);
  let summary;
  for(const frame of sequence){
    summary=await value(cdp,`renderFilmFrame(${frame})`);
    const screenshot=await cdp.send('Page.captureScreenshot',{format:'jpeg',quality:94,fromSurface:true,optimizeForSpeed:true});
    const jpg=Buffer.from(screenshot.data,'base64');
    if(checkOnly||[273,586,673,974].includes(frame)) await writeFile(join(prefix,`v2-frame-${frame}.jpg`),jpg);
    if(!checkOnly&&!encoder.stdin.write(jpg)) await once(encoder.stdin,'drain');
    if(checkOnly||frame%120===0)console.log(JSON.stringify(summary));
  }
  const sheepTouches=summary?.touches.mian.map(e=>e.kind).join(',');
  const cloudTouches=summary?.touches.yun.map(e=>e.kind).join(',');
  if(!summary?.sawRun||!summary.sawWalk||!summary.sawDrag||!summary.sawDrop
      ||sheepTouches!=='poke,pet'||cloudTouches!=='grab,drop')
    throw Error('Unexpected states or pointer reactions: '+JSON.stringify(summary));
  if(encoder){
    encoder.stdin.end();
    const [exit]=await encoded;
    if(exit!==0)throw Error('FFmpeg exited with '+exit);
    await rename(temporaryOutput,out);
    console.log(out);
  }
  }
}finally{
  cdp?.close();
  server.close();
  if(encoder?.exitCode===null && !encoder.stdin.writableEnded)encoder.kill();
  if(browser.exitCode===null){
    browser.kill();
    await Promise.race([once(browser,'exit'),sleep(2000)]);
  }
  if(resolve(profile).startsWith(prefix+sep))
    await rm(profile,{recursive:true,force:true,maxRetries:4,retryDelay:100}).catch(()=>{});
}
