import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import {worldFloors,worldObstacles,moveOnFloors,blocksWalking} from '../lib/world.ts';
import {readModel} from './gltf-geometry.mjs';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const w=read('public/bitgaram-park-world.json');
const p=read(w.accessReference.profiles);

test('satellite-informed western slide stays separate from the monorail and records uncertainty',()=>{
 const b=read('knowledge/sources/bitgaram/access-v101/build.json');
 assert.equal(b.sourceUnchanged,true);assert.equal(b.surveyed,false);
 assert.ok(b.protectedMeshes>1000);assert.ok(b.maxGalleryStep<.17&&b.maxOutdoorStep<=.161);
 assert.ok(Math.min(...p.slide_route.map(q=>q[0])) < -30,'The former guessed near-rail curve must not return');
 for(const a of p.slide_route){
  const distance=Math.min(...w.monorail.route.map(b=>Math.hypot(a[0]-b[0],a[2]-b[2])));
  assert.ok(distance>20,'Slide and rail must remain physically distinct');
 }
 assert.match(w.limitations.join(' '),/추정/);
});

test('both stair routes and their station connectors can be walked in both directions',()=>{
 const floors=worldFloors(w.solids),obstacles=worldObstacles(w.solids);
 const routes={gallery:[...p.connectors.upper_gallery,...p.stairs_route,...p.connectors.lower_gallery],outdoor:[...p.connectors.upper_outdoor,...p.outdoor_route,...p.connectors.lower_outdoor]};
 for(const [name,route] of Object.entries(routes))for(const points of [route,[...route].reverse()]){
  let [x,height,z]=points[0];
  assert.equal(blocksWalking(x,z,height,obstacles),false,`${name} entry blocked`);
  for(const [tx,,tz] of points.slice(1)){
   for(let i=0;i<1000&&Math.hypot(tx-x,tz-z)>.001;i++){
    const L=Math.hypot(tx-x,tz-z),d=Math.min(.07,L);
    const q=moveOnFloors(x,z,height,(tx-x)*d/L,(tz-z)*d/L,obstacles,floors,w.bounds,w.requireFloor);
    if(Math.hypot(q.x-x,q.z-z)<.00001)break;
    ({x,height,z}=q);
   }
   assert.ok(Math.hypot(tx-x,tz-z)<.025,`${name} blocked toward ${tx},${tz}; actual ${x},${z},${height}`);
  }
  assert.ok(Math.abs(height-points.at(-1)[1])<.18);
 }
});

test('new stair and connector colliders meet their actual exported Blender surfaces',()=>{
 const {scene}=readModel(new URL('../public/models/bitgaram-park.glb',import.meta.url));
 const names=['walk-floor_outdoor_timber_stairs','walk-floor_slide_side_stairs','walk-floor_access101_turn_landings',...Object.keys(p.connectors).map(n=>'walk-floor_access101_'+n)];
 for(const name of names){
  const mesh=scene.getObjectByName(name);assert.ok(mesh,name);
  for(const s of w.solids.filter(s=>s.name===name)){
   const x=s.footprint.reduce((v,p)=>v+p[0],0)/4,z=s.footprint.reduce((v,p)=>v+p[1],0)/4,height=s.position[1]+s.size[1];
   const hits=new THREE.Raycaster(new THREE.Vector3(x,height+.02,z),new THREE.Vector3(0,-1,0),0,.05).intersectObject(mesh,true);
   assert.ok(hits.some(h=>Math.abs(h.point.y-height)<.003),`${name}: ${x},${z}`);
  }
 }
});

test('rounded photo-informed cabin retains transparent windows and independent sliding doors',()=>{
 const raw=fs.readFileSync(new URL('../public/models/bitgaram-monorail.glb',import.meta.url));
 const g=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
 assert.equal(g.nodes.filter(n=>n.name.startsWith('cab101_rounded_white_shell')).length,2);
 for(const name of ['monorail_door_left','monorail_door_right']){
  const door=g.nodes.find(n=>n.name===name);assert.ok(door?.extras?.authored_dynamic);
  assert.ok(door.children.some(i=>g.nodes[i].name.startsWith('cab101_door_orange_band')));
 }
 assert.ok(g.materials.some(m=>m.alphaMode==='BLEND'&&m.pbrMetallicRoughness.baseColorFactor[3]<.3));
});
