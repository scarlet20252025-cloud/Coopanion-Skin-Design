import { createServer } from 'node:http';
import { readFile, readdir, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { extname, resolve, sep } from 'node:path';

const here=resolve(fileURLToPath(new URL('.',import.meta.url)));
const upstream=resolve(here,'vendor/Coopanion-web');
const model=resolve(here,'pack/star-witch');
const source=resolve(here,'parts');
const port=+(process.argv[2]??4334);
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8',
  '.json':'application/json; charset=utf-8','.png':'image/png'};

function inside(root,path) {
  const file=resolve(root,path);
  return file.startsWith(root+sep)?file:null;
}

async function revision() {
  const packFiles=['figure.js','figure.json','model.json','effects.js',
    ...(await readdir(resolve(model,'tex'))).filter(name=>name.endsWith('.png')).map(name=>'tex/'+name)];
  const sources=(await readdir(source)).filter(name=>name.endsWith('.png')).map(name=>resolve(source,name));
  const stamps=await Promise.all([
    ...packFiles.map(path=>resolve(model,path)),...sources,
  ].map(async path=>(await stat(path)).mtimeMs));
  return stamps.join(',');
}

createServer(async (req,res)=>{
  try {
    const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    if(pathname==='/revision') {
      res.writeHead(200,{'Content-Type':'text/plain','Cache-Control':'no-store'}).end(await revision());
      return;
    }
    let file;
    if(pathname==='/') file=resolve(here,'preview.html');
    else if(['/preview.html','/preview.js'].includes(pathname)) file=inside(here,pathname.slice(1));
    else if(pathname.startsWith('/pack/star-witch/')) file=inside(model,pathname.slice('/pack/star-witch/'.length));
    else if(/^\/parts\/[a-zA-Z][a-zA-Z0-9]*\.png$/.test(pathname)) file=inside(source,pathname.slice(7));
    else if(pathname.startsWith('/upstream/')) file=inside(upstream,pathname.slice('/upstream/'.length));
    if(!file||!mime[extname(file)]) {res.writeHead(404).end();return;}
    const body=await readFile(file);
    res.writeHead(200,{'Content-Type':mime[extname(file)],'Cache-Control':'no-store'}).end(body);
  } catch {
    res.writeHead(404).end();
  }
}).listen(port,'127.0.0.1',()=>console.log('Star Witch preview at http://127.0.0.1:'+port+'/'));
