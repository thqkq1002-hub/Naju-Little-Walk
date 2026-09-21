import {readFileSync,writeFileSync} from 'node:fs';
import {gzipSync,gunzipSync} from 'node:zlib';
for(const id of ['park','overview','observatory']){
  const path=new URL(`../public/models/bitgaram-${id}.glb`,import.meta.url);
  const raw=readFileSync(path),packed=gzipSync(raw,{level:9});
  if(!gunzipSync(packed).equals(raw))throw new Error('Model transport mismatch');
  writeFileSync(new URL(path.href+'.gz'),packed);
  console.log(`${id}: ${raw.length} -> ${packed.length} bytes`);
}
