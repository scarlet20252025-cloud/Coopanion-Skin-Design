import {createServer} from 'node:http';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,extname,sep,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const official=resolve(root,'../Coopanion-reference/packages/cortico-world-desktop-pet/web');
const out=resolve(root,'tools-local/whale-reference-91293b3');
const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png','.webp':'image/webp'};
createServer(async(req,res)=>{
 try{
  const path=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  if(req.method==='POST'){
   if(req.headers.origin!=='http://127.0.0.1:4320'||!/^\/export\/[a-z0-9_-]+\/(?:[0-9]{4}\.png|timeline\.json)$/.test(path)){res.writeHead(403);res.end();return;}
   const file=resolve(out,path.slice(8));
   const chunks=[];let size=0;for await(const chunk of req){size+=chunk.length;if(size>8e6)throw Error('too large');chunks.push(chunk);}
   await mkdir(dirname(file),{recursive:true});await writeFile(file,Buffer.concat(chunks));res.end('saved');return;
  }
  const base=path.startsWith('/official/')?official:root;
  const relative=path==='/'?'preview/official-reference.html':path.startsWith('/official/')?path.slice(10):path.slice(1);
  const file=resolve(base,relative);if(!file.startsWith(resolve(base)+sep)){res.writeHead(403);res.end();return;}
  res.setHeader('Cache-Control','no-store');res.setHeader('Content-Type',mime[extname(file)]||'application/octet-stream');res.end(await readFile(file));
 }catch(e){res.writeHead(500);res.end(String(e));}
}).listen(4320,'127.0.0.1',()=>console.log('Official reference: http://127.0.0.1:4320/'));
