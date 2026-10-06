import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import {worldFloors,worldObstacles,moveOnFloors} from '../lib/world.ts';
import {readModel} from './gltf-geometry.mjs';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const world=read('public/bitgaram-park-world.json');
const profiles=read(world.accessReference.profiles);
test('park adopts the recorded native DSM height difference, not the old shallow Gaussian',()=>{
 const t=world.terrain;
 assert.equal(t.nativeResolutionMetres,30);assert.equal(t.surveyedBareEarth,false);
 assert.ok(t.platformDifferenceMetres>33&&t.platformDifferenceMetres<36);
 assert.ok(Math.abs(t.upperSurfaceElevationMetres-79.14)<.02);
 assert.ok(Math.abs(t.lowerSurfaceElevationMetres-44.71)<.02);
 assert.ok(Math.abs(world.spawn.height+ t.modelDatumMetres-t.upperSurfaceElevationMetres)<1e-6);
 assert.match(t.attribution,/Copernicus/);assert.ok(t.limitations.some(s=>s.includes('vegetation')||s.includes('NGII')));
});
test('the long mapped forest approach works uphill and downhill at the new elevations',()=>{
 const floors=worldFloors(world.solids),obstacles=worldObstacles(world.solids),route=profiles.forest_route;
 for(const points of [route,[...route].reverse()]){
  let [x,height,z]=points[0];
  for(const [tx,,tz] of points.slice(1)){
   const moved=moveOnFloors(x,z,height,tx-x,tz-z,obstacles,floors,world.bounds,world.requireFloor);
   assert.ok(Math.hypot(moved.x-tx,moved.z-tz)<.015,`Blocked approach at ${tx},${tz}, height ${height}`);
   ({x,z,height}=moved);
  }
  assert.ok(Math.abs(height-points.at(-1)[1])<.25);
 }
});
test('exported approach and stair surfaces match walking collision levels',()=>{
 const {scene}=readModel(new URL('../public/models/bitgaram-park.glb',import.meta.url));
 for(const name of ['walk-floor_mapped_forest_549492174','walk-floor_slide_side_stairs']){
  const mesh=scene.getObjectByName(name),solids=world.solids.filter(s=>s.name===name);
  assert.ok(mesh);
  for(const s of solids.filter((_,i)=>i%11===0)){
   const x=s.footprint.reduce((v,p)=>v+p[0],0)/s.footprint.length,z=s.footprint.reduce((v,p)=>v+p[1],0)/s.footprint.length;
   const height=s.position[1]+s.size[1];
   const hits=new THREE.Raycaster(new THREE.Vector3(x,height+.02,z),new THREE.Vector3(0,-1,0),0,.08).intersectObject(mesh,true);
   assert.ok(hits.some(h=>Math.abs(h.point.y-height)<.003),`Walking/render mismatch ${name} ${x},${z}`);
  }
 }
});
test('the new guideway clears the rendered hillside on its open middle section',()=>{
 const {scene,gltf}=readModel(new URL('../public/models/bitgaram-park.glb',import.meta.url));
 const hill=scene.getObjectByName('estimated_hill');
 assert.equal(hill.userData.surveyed_bare_earth,false);
 const node=gltf.nodes.find(n=>n.name==='estimated_hill');
 assert.ok(gltf.meshes[node.mesh].primitives.every(p=>p.attributes.COLOR_0!==undefined),'Terrain shader needs the retained vertex colour field');
 for(const [x,y,z] of world.monorail.route.filter((p,i)=>i%4===0&&p[2]>30&&p[2]<96)){
  const hit=new THREE.Raycaster(new THREE.Vector3(x,y+5,z),new THREE.Vector3(0,-1,0),0,12).intersectObject(hill,true)[0];
  assert.ok(hit,`No terrain under beam at ${x},${z}`);
  assert.ok(hit.point.y<y-.15,`Guideway buried in hillside at ${x},${z}: ${hit.point.y} vs ${y}`);
 }
});

test('the outer forest approach sits above the refined rendered lawn',()=>{
 const {scene}=readModel(new URL('../public/models/bitgaram-park.glb',import.meta.url));
 const lawn=scene.getObjectByName('mapped_park_lawn_shore_v75');
 const [x,y,z]=profiles.forest_route[0];
 assert.ok(lawn);
 const hit=new THREE.Raycaster(new THREE.Vector3(x,y+1,z),new THREE.Vector3(0,-1,0),0,2).intersectObject(lawn,true)[0];
 assert.ok(hit,'No ground within a metre below the forest entrance');
 assert.ok(y-hit.point.y>.10&&y-hit.point.y<.30,`Forest entrance floats above lawn: ${y-hit.point.y}m`);
});
