import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import zlib from 'node:zlib';
import {worldFloors,worldObstacles,moveOnFloors,blocksWalking} from '../lib/world.ts';
const w=JSON.parse(fs.readFileSync(new URL('../public/bitgaram-park-world.json',import.meta.url)));
const r=JSON.parse(fs.readFileSync(new URL('../knowledge/sources/bitgaram/access-v69.json',import.meta.url)));
test('mapped monorail is distinct from the forest walk and stone slide',()=>{
 const source=JSON.parse(fs.readFileSync(new URL('../knowledge/sources/bitgaram/geometry.json',import.meta.url)));
 assert.deepEqual(r.mapped_monorail_plan,source.ways.find(x=>x.id==='508048300').points);
 assert.ok(Math.abs(r.slide_authored_length-96)<.00001);
 assert.ok(!w.solids.some(s=>s.name.startsWith('walk-floor_approach')||s.name==='timber_walk_guard'));
 const raw=fs.readFileSync(new URL('../public/models/bitgaram-park.glb',import.meta.url)),g=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
 for(const name of ['mapped_monorail_508048300_beam','photo_monorail_cab_body','photo_stone_slide_U_trough','slide_gallery_timber_arch','slide_gallery_blue_side'])assert.ok(g.nodes.some(n=>n.name===name),name);
 assert.ok(g.materials.some(m=>m.name==='Stone_slide_polished_granite'&&m.pbrMetallicRoughness?.baseColorTexture));
 assert.ok(zlib.gunzipSync(fs.readFileSync(new URL('../public/models/bitgaram-park.glb.gz',import.meta.url))).equals(raw));
});
for(const [label,key] of [['mapped forest approach','forest_route'],['parallel gallery stairs','stairs_route']])test(`${label} connects downhill and uphill without invisible barriers or unreachable steps`,()=>{
 const route=r[key],floors=worldFloors(w.solids),obstacles=worldObstacles(w.solids);
 for(const points of [route,[...route].reverse()]){
  let p={x:points[0][0],z:points[0][2],height:points[0][1]};
  assert.equal(blocksWalking(p.x,p.z,p.height,obstacles),false,`${label} entrance blocked`);
  for(const b of points.slice(1)){
   for(let i=0;i<15;i++){const dx=b[0]-p.x,dz=b[2]-p.z;if(Math.hypot(dx,dz)<.001)break;const len=Math.hypot(dx,dz),step=Math.min(len,.11);p=moveOnFloors(p.x,p.z,p.height,dx/len*step,dz/len*step,obstacles,floors,w.bounds);}
   assert.ok(Math.hypot(p.x-b[0],p.z-b[2])<.02,`${label} blocked at ${JSON.stringify(b)} actual ${JSON.stringify(p)}`);
   assert.ok(Math.abs(p.height-b[1])<.2,`${label} walking floor does not match rendered stairs`);
  }
 }
});
