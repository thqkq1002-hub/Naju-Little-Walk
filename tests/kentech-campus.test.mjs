import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import zlib from 'node:zlib';
import {canTravelTo} from '../lib/map-navigation.ts';
import {worldObstacles,worldFloors,moveOnFloors} from '../lib/world.ts';
const world=JSON.parse(fs.readFileSync(new URL('../public/bitgaram-kentech-world.json',import.meta.url)));
const floors=worldFloors(world.solids),obstacles=worldObstacles(world.solids);
test('KENTECH entrance halls and campus approaches remain continuously walkable',()=>{
 for(const route of world.validationRoutes){
  let p={x:route[0][0],z:route[0][1],height:0};
  for(const [x,z] of route.slice(1)){
   p=moveOnFloors(p.x,p.z,p.height,x-p.x,z-p.z,obstacles,floors,world.bounds,true);
   assert.ok(Math.hypot(p.x-x,p.z-z)<.04,`Blocked campus waypoint ${x},${z}: ${JSON.stringify(p)}`);
   assert.ok(p.height<.2,'No teleport onto the upper floors');
  }
 }
 for(const place of world.places)assert.ok(canTravelTo(place.arrival,world),place.id);
});
test('glass walls, residence and library remain solid while front doors open',()=>{
 const wall=moveOnFloors(15,20,0,0,-18,obstacles,floors,world.bounds,true);
 assert.ok(wall.z>10,'A closed facade cannot be walked through');
 assert.equal(canTravelTo([200,133],world),false,'Residence interiors stay closed');
 assert.equal(canTravelTo([145,-133],world),false,'Library wall stays closed');
 assert.ok(canTravelTo([-5,3],world),'Ground-floor entrance is open');
});
test('campus has visible upper walls and roofs in overview, with bounded compressed geometry',()=>{
 const raw=fs.readFileSync(new URL('../public/models/bitgaram-kentech.glb',import.meta.url));
 const packed=fs.readFileSync(new URL('../public/models/bitgaram-kentech.glb.gz',import.meta.url));
 assert.deepEqual(zlib.gunzipSync(packed),raw);assert.ok(raw.length<32*1024*1024);
 const gltf=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
 assert.match(gltf.asset.generator,/Blender/);
 assert.equal(gltf.nodes.some(n=>n.extras?.hide_in_overview),false,'Exterior must never become a bare frame in overview');
 for(const id of ['1065747586','1201084332'])assert.ok(gltf.nodes.some(n=>n.extras?.campus_landmark===id),'Missing main-building envelope '+id);
 assert.ok(gltf.nodes.filter(n=>n.mesh!==undefined).length<120,'Opaque details are batched before delivery while preserving glass panes');
 assert.ok(world.provenance.landmarks.length>=11);
});
