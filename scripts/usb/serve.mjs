// Offline server for the USB copy of 나주 산책. No packages: serves ../app on this computer only
// (127.0.0.1), picks a free port, and opens the default browser. Close the window to stop.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {exec} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..','app');
const args=new Set(process.argv.slice(2));
const fixedPort=Number(process.argv.find(a=>a.startsWith('--port='))?.slice(7));
const types={
  '.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8',
  '.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml',
  '.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.ico':'image/x-icon',
  '.glb':'model/gltf-binary','.gz':'application/gzip','.mp3':'audio/mpeg','.wasm':'application/wasm',
  '.txt':'text/plain; charset=utf-8','.woff2':'font/woff2',
};

function resolveFile(urlPath){
  let decoded;
  try{decoded=decodeURIComponent(urlPath);}catch{return null;}
  const file=path.resolve(root,'.'+path.posix.normalize('/'+decoded));
  if(file!==root&&!file.startsWith(root+path.sep))return null;
  if(fs.existsSync(file)&&fs.statSync(file).isFile())return file;
  // Pages are chosen with ?place=…, so any other extensionless path shows the app.
  return path.extname(decoded)?null:path.join(root,'index.html');
}

const server=http.createServer((req,res)=>{
  if(req.method!=='GET'&&req.method!=='HEAD'){res.writeHead(405).end();return;}
  const file=resolveFile(new URL(req.url,'http://localhost').pathname);
  if(!file){res.writeHead(404,{'content-type':'text/plain; charset=utf-8'}).end('찾을 수 없습니다');return;}
  const size=fs.statSync(file).size;
  const headers={'content-type':types[path.extname(file).toLowerCase()]??'application/octet-stream','accept-ranges':'bytes','cache-control':'no-cache'};
  const range=/^bytes=(\d*)-(\d*)$/.exec(req.headers.range??'');
  if(range&&(range[1]||range[2])){
    let start=range[1]?Number(range[1]):size-Number(range[2]);
    let end=range[1]&&range[2]?Number(range[2]):size-1;
    start=Math.max(0,start);end=Math.min(size-1,end);
    if(start>end){res.writeHead(416,{'content-range':`bytes */${size}`}).end();return;}
    res.writeHead(206,{...headers,'content-range':`bytes ${start}-${end}/${size}`,'content-length':end-start+1});
    if(req.method==='HEAD')res.end();else fs.createReadStream(file,{start,end}).pipe(res);
    return;
  }
  res.writeHead(200,{...headers,'content-length':size});
  if(req.method==='HEAD')res.end();else fs.createReadStream(file).pipe(res);
});

function listen(port,last){
  server.once('error',error=>{
    if(error.code==='EADDRINUSE'&&!fixedPort&&port<last){listen(port+1,last);return;}
    console.error(`\n  서버를 시작하지 못했습니다: ${error.message}`);process.exitCode=1;
  });
  server.listen(port,'127.0.0.1',()=>{
    const url=`http://127.0.0.1:${port}/`;
    console.log('\n  나주 산책이 준비되었습니다.');
    console.log(`  브라우저 주소: ${url}`);
    console.log('\n  이 창을 닫으면 나주 산책이 종료됩니다.\n');
    if(!args.has('--no-open'))exec(`start "" "${url}"`);
  });
}

if(!fs.existsSync(path.join(root,'index.html'))){console.error(`\n  앱 파일을 찾을 수 없습니다: ${root}`);process.exit(1);}
listen(fixedPort||3000,fixedPort||3020);
