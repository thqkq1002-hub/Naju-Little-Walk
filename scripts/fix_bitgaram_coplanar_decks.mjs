// Bitgaram decks and floors were exported at exactly the same height where they overlap, so the browser
// flickered between them (z-fighting): timber strips speckled through the paving.
// - Below the slide (19.209 m): roof-garden paving, lower-station floor, outdoor and stair-landing decks;
//   the outdoor stair turn landings also lay exactly on the stair flight.
// - At the summit shelter (53.642 m): the shelter floor under the upper-station floor and both upper decks.
// The park uses a logarithmic depth buffer, so millimetres of separation are enough. Walking floors are
// unchanged (render/walk tolerance is 3 mm). Node translations only; mesh data and the binary chunk stay as
// exported. The applied offsets are recorded in the GLB, so re-running applies only what changed. Rewrites
// the gzip copy too.
import fs from 'node:fs';
import {gzipSync} from 'node:zlib';

const offsets={
  // Lower level, from low to high: paving, station floor, outdoor deck (0), stair-landing deck.
  'context_roof_garden_paving':-.006,
  'walk-floor_lower_station':-.002,
  'walk-floor_access101_lower_gallery':.002,
  // 2 mm under their stairs: one stair edge already sat 1.8 mm above a landing.
  'walk-floor_access101_turn_landings':-.002,
  // Summit: the shelter floor drops under the upper-station floor and the two deck heads.
  'ground_floor_summit':-.003,
};
const glbUrl=new URL('../public/models/bitgaram-park.glb',import.meta.url);
const raw=fs.readFileSync(glbUrl),jsonLength=raw.readUInt32LE(12);
const gltf=JSON.parse(raw.toString('utf8',20,20+jsonLength)),rest=raw.subarray(20+jsonLength);
gltf.extras??={};
const applied=gltf.extras.coplanarDeckFix??{};
const changed=[];
for(const [name,dy] of Object.entries(offsets)){
  const delta=dy-(applied[name]??0);
  if(Math.abs(delta)<1e-9)continue;
  const nodes=gltf.nodes.filter(n=>n.name===name);
  if(nodes.length!==1||nodes[0].matrix)throw new Error(`Expected one translatable node ${name}`);
  const t=nodes[0].translation??[0,0,0];nodes[0].translation=[t[0],t[1]+delta,t[2]];
  applied[name]=dy;changed.push(name);
}
if(!changed.length){console.log('already applied');process.exit(0);}
gltf.extras.coplanarDeckFix=applied;
let json=Buffer.from(JSON.stringify(gltf),'utf8');json=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,0x20)]);
const header=Buffer.alloc(20);header.write('glTF',0,'ascii');header.writeUInt32LE(2,4);header.writeUInt32LE(20+json.length+rest.length,8);header.writeUInt32LE(json.length,12);header.write('JSON',16,'ascii');
const patched=Buffer.concat([header,json,rest]);
fs.writeFileSync(glbUrl,patched);
fs.writeFileSync(new URL('../public/models/bitgaram-park.glb.gz',import.meta.url),gzipSync(patched,{level:9}));
console.log('separated',changed.join(', '),raw.length,'->',patched.length,'bytes');
