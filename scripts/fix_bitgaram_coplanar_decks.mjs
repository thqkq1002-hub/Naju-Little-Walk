// Below the Bitgaram slide, the roof-garden paving, the lower-station floor and two timber decks were exported
// at exactly 19.209 m where they overlap, and the outdoor stair turn landings lie exactly on the stair flight,
// so the browser flickered between them (z-fighting). The park uses a logarithmic depth buffer, so millimetres
// of separation are enough. Stack, from low to high: paving −6 mm, station floor −2 mm, outdoor deck 0,
// stair-landing deck +2 mm; turn landings 2 mm under their stairs (one stair edge already sat 1.8 mm above).
// Walking floors are unchanged (render/walk tolerance is 3 mm). Node translations only; mesh data and the
// binary chunk stay as exported. Rewrites the gzip copy too.
import fs from 'node:fs';
import {gzipSync} from 'node:zlib';

const offsets={
  'context_roof_garden_paving':-.006,
  'walk-floor_lower_station':-.002,
  'walk-floor_access101_lower_gallery':.002,
  'walk-floor_access101_turn_landings':-.002,
};
const glbUrl=new URL('../public/models/bitgaram-park.glb',import.meta.url);
const raw=fs.readFileSync(glbUrl),jsonLength=raw.readUInt32LE(12);
const gltf=JSON.parse(raw.toString('utf8',20,20+jsonLength)),rest=raw.subarray(20+jsonLength);
gltf.extras??={};
if(gltf.extras.coplanarDeckFix){console.log('already applied');process.exit(0);}
for(const [name,dy] of Object.entries(offsets)){
  const nodes=gltf.nodes.filter(n=>n.name===name);
  if(nodes.length!==1||nodes[0].matrix)throw new Error(`Expected one translatable node ${name}`);
  const t=nodes[0].translation??[0,0,0];nodes[0].translation=[t[0],t[1]+dy,t[2]];
}
gltf.extras.coplanarDeckFix=offsets;
let json=Buffer.from(JSON.stringify(gltf),'utf8');json=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,0x20)]);
const header=Buffer.alloc(20);header.write('glTF',0,'ascii');header.writeUInt32LE(2,4);header.writeUInt32LE(20+json.length+rest.length,8);header.writeUInt32LE(json.length,12);header.write('JSON',16,'ascii');
const patched=Buffer.concat([header,json,rest]);
fs.writeFileSync(glbUrl,patched);
fs.writeFileSync(new URL('../public/models/bitgaram-park.glb.gz',import.meta.url),gzipSync(patched,{level:9}));
console.log('separated',JSON.stringify(offsets),raw.length,'->',patched.length,'bytes');
