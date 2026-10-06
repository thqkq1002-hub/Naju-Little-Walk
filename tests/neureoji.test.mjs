import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {destinations} from '../lib/destinations.ts';
import {mapArrival,canTravelTo,regionalPoint,regionalSize} from '../lib/map-navigation.ts';
import {moveOnFloors,worldFloors,worldObstacles,reachableFloor} from '../lib/world.ts';
import {sceneArrival} from '../lib/scene-travel.ts';
import * as THREE from 'three';
import {readModel} from './gltf-geometry.mjs';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const w=read('public/neureoji-world.json');
test('all tower levels are reached by actual steps and can be descended without teleporting',()=>{
 const floors=worldFloors(w.solids),obstacles=worldObstacles(w.solids);
 let p={x:w.spawn.x,z:w.spawn.z,height:w.spawn.height};
 for(const [x,z,h] of [...w.walkRoute.slice(1),...w.walkRoute.slice(0,-1).reverse()]){
  p=moveOnFloors(p.x,p.z,p.height,x-p.x,z-p.z,obstacles,floors,w.bounds,w.requireFloor);
  assert.ok(Math.hypot(p.x-x,p.z-z)<.05,`route ${x},${z},${h}: ${JSON.stringify(p)}`);
  assert.ok(Math.abs(p.height-h)<.22,`floor elevation ${h}: ${p.height}`);
 }
 assert.ok(Math.abs(p.height-w.spawn.height)<.001);
 assert.ok(!canTravelTo([-1000,-1000],w),'River scenery is outside the local walking map');
});
test('arrival links and local map destinations land on the intended floor',()=>{
 const top=sceneArrival(w,'?place=neureoji&at=top');assert.ok(top.entered);assert.equal(top.height,w.topDeckHeightMetres);
 for(const place of w.places){const p=mapArrival(place,w);assert.ok(p,place.id);assert.ok(canTravelTo(p,w,place.arrivalHeight));}
 const p=regionalPoint(destinations.neureoji.coordinates.lon,destinations.neureoji.coordinates.lat);
 assert.ok(p[0]>0&&p[0]<regionalSize[0]&&p[1]>0&&p[1]<regionalSize[1]);
});
test('present tower, native DSM limitations and true concave river are recorded',()=>{
 const g=read('knowledge/sources/neureoji-v92/geography.json'),t=read('knowledge/sources/neureoji-v92/native-terrain.json');
 assert.deepEqual(g.originWGS84,{lat:34.9159348,lon:126.5419381});assert.equal(t.nativeResolutionMetres,30);
 assert.ok(w.towerHeightMetres<16&&w.towerHeightMetres>14);assert.ok(w.limitations.some(x=>x.includes('측량')));
 assert.ok(g.water.some(p=>p.points.length>100));assert.ok(!g.water.every(p=>p.points.length===4));
 const raw=fs.readFileSync(new URL('../public/models/neureoji.glb',import.meta.url)),packed=fs.readFileSync(new URL('../public/models/neureoji.glb.gz',import.meta.url));assert.deepEqual(gunzipSync(packed),raw);
 const gltf=JSON.parse(raw.toString('utf8',20,20+raw.readUInt32LE(12)));assert.ok(gltf.meshes.length<100);assert.ok(packed.length<16*1024*1024);
 assert.ok(gltf.nodes.some(n=>n.name==='mapped_river_water_neureoji'));assert.ok(gltf.nodes.some(n=>n.name==='walk-floor_top_deck'));
 assert.ok(gltf.images.every(i=>i.bufferView!==undefined&&!i.uri));
});
test('walkers stand on exported Blender floors and the normal-height panorama sightline is open',()=>{
 const {scene}=readModel(new URL('../public/models/neureoji.glb',import.meta.url));
 for(const n of [0,6,21,28,44,52,67,w.walkRoute.length-1]){
  const [x,z,h]=w.walkRoute[n];const hits=new THREE.Raycaster(new THREE.Vector3(x,h+.12,z),new THREE.Vector3(0,-1,0),0,.25).intersectObject(scene,true);
  assert.ok(hits.length,`No visible floor at route ${n}: ${x},${z},${h}`);
  assert.ok(Math.abs(hits[0].point.y-h)<.03,`Visible floor and walking height disagree at ${n}`);
 }
 const a=w.arrivals.top,origin=new THREE.Vector3(a.x,w.topDeckHeightMetres+1.72,a.z);
 const direction=new THREE.Vector3(-Math.sin(a.yaw),Math.tan(a.pitch),-Math.cos(a.yaw)).normalize();
 const hits=new THREE.Raycaster(origin,direction,.1,200).intersectObject(scene,true);
 assert.equal(hits.length,0,'Roof, pillars and nearby trees must not hide the peninsula view');
 scene.traverse(o=>o.geometry?.dispose());
});

test('top arrival and map travel face the mapped peninsula from the same normal-height position',()=>{
 const a=sceneArrival(w,'?place=neureoji&at=top'),p=w.places.find(p=>p.id==='peninsula-view');
 assert.deepEqual(p.arrival,[a.x,a.z]);assert.equal(p.arrivalHeight,a.height);
 assert.equal(p.arrivalYaw,a.yaw);assert.equal(p.arrivalPitch,a.pitch);
 const [x,z]=w.panoramaTargetMetres;
 assert.ok(Math.abs(Math.atan2(a.x-x,a.z-z)-a.yaw)<.001);
 const v=w.architectureViews.find(v=>v.id==='peninsula');
 assert.equal(v.center[1],a.height+1.72);assert.ok(Math.abs(a.pitch)<.15);
});

test('background terrain cannot fill the mapped river or change its bank line',()=>{
 const {scene}=readModel(new URL('../public/models/neureoji.glb',import.meta.url));
 const land=scene.getObjectByName('ground_native_DSM_interpreted'),water=scene.getObjectByName('mapped_river_water_neureoji');
 assert.ok(land&&water);
 // Water is authored as a two-sided thin surface; use the exported viewing semantics.
 water.traverse(o=>{if(o.material)o.material=new THREE.MeshBasicMaterial({side:THREE.DoubleSide});});
 for(const [x,z] of [[-100,-400],[-1500,-1500],[-600,-250],[-350,-200]]){
  const ray=new THREE.Raycaster(new THREE.Vector3(x,200,z),new THREE.Vector3(0,-1,0),0,210);
  assert.equal(ray.intersectObject(land,true).length,0,`Dry terrain protrudes into mapped water at ${x},${z}`);
  assert.ok(ray.intersectObject(water,true).length,`Mapped river missing at ${x},${z}`);
 }
 scene.traverse(o=>o.geometry?.dispose());
});

test('both hydrangea routes follow continuous slopes in both directions and connect to the tower',()=>{
 const floors=worldFloors(w.solids),obstacles=worldObstacles(w.solids);
 assert.ok(w.hydrangeaTrailLengthMetres>350&&w.hydrangeaTrailLengthMetres<380);
 for(const route of Object.values(w.hydrangeaRoutes)){
  let p={x:route[0][0],z:route[0][1],height:route[0][2]};
  for(const [x,z,h] of [...route.slice(1),...route.slice(0,-1).reverse()]){
   p=moveOnFloors(p.x,p.z,p.height,x-p.x,z-p.z,obstacles,floors,w.bounds,true);
   assert.ok(Math.hypot(p.x-x,p.z-z)<.035,`flower route blocked at ${x},${z}: ${JSON.stringify(p)}`);
   assert.ok(Math.abs(p.height-h)<.02,`Sloping visible floor differs at ${x},${z}: ${p.height} vs ${h}`);
  }
 }
 // Both links meet the existing plaza, rather than leaving disconnected walkable islands.
 let p={x:3.2,z:21,height:w.spawn.height};
 for(const [x,z,h] of w.hydrangeaConnector.slice(1)){
  p=moveOnFloors(p.x,p.z,p.height,x-p.x,z-p.z,obstacles,floors,w.bounds,true);
  assert.ok(Math.hypot(p.x-x,p.z-z)<.04&&Math.abs(p.height-h)<.02,'Plaza connection must bypass the actual stair guards');
 }
 assert.ok(Math.hypot(p.x-5,p.z+5.1)<.04);
 for(const key of ['hydrangea','forest','boardwalk']){const a=sceneArrival(w,'?place=neureoji&at='+key);assert.ok(a.entered);assert.ok(canTravelTo([a.x,a.z],w,a.height));}
 const tip=w.hydrangeaRoutes['woodland-hydrangea'].at(-1);
 assert.equal(reachableFloor(tip[0]+15,tip[1],tip[2],floors,true),null,'The landscape is scenery, not an invisible walking surface');
});

test('hydrangea walking planes agree with exported Blender triangles, including bend edges',()=>{
 const {scene}=readModel(new URL('../public/models/neureoji.glb',import.meta.url));
 const floors=worldFloors(w.solids),meshes=['flower-road','woodland-hydrangea'].map(id=>scene.getObjectByName('walk-floor_hydrangea_'+id));
 assert.ok(meshes.every(Boolean));
 for(const route of Object.values(w.hydrangeaRoutes))for(let i=2;i<route.length-2;i+=11){
  const [x,z,h]=route[i];const hits=new THREE.Raycaster(new THREE.Vector3(x,h+.2,z),new THREE.Vector3(0,-1,0),0,.4).intersectObjects(meshes,true);
  assert.ok(hits.length,`Sloped GLB floor missing at ${x},${z}`);
  assert.ok(Math.abs(hits[0].point.y-h)<.005);
  assert.ok(Math.abs(reachableFloor(x,z,h,floors,true)-hits[0].point.y)<.005);
 }
 scene.traverse(o=>o.geometry?.dispose());
});
