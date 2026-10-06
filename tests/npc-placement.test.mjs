import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import {destinations} from '../lib/destinations.ts';
import {guidePlacements,withNpcObstacle} from '../lib/npc-placement.ts';
import {canTravelTo,mapArrival} from '../lib/map-navigation.ts';
import {floorHeight,reachableFloor,worldFloors,movePlayer,solidCollider} from '../lib/world.ts';
import {readModel} from './gltf-geometry.mjs';

const manifest=JSON.parse(fs.readFileSync(new URL('../public/npc-placements.json',import.meta.url),'utf8'));
const expected={geumseonggwan:'beodeuri',bogam:'beodeuri','bitgaram-park':'baedoli','bitgaram-kepco':'baedoli','bitgaram-kentech':'baedoli',yeongsanpo:'hongdoli','yeongsanpo-literature':'beodeuri',deudeulgang:'baedoli','naju-arboretum':'baedoli',dasi:'teacher'};
// These floors are drawn slightly above their flat collision ground; the guide stands on what visitors see.
const visibleGround={'naju-arboretum':.1,'yeongsanpo-literature':.0355};
test('regional guides follow the user assignments; unassigned maps and empty panorama stay empty',()=>{
  assert.deepEqual(Object.fromEntries(Object.entries(manifest.placements).map(([id,p])=>[id,p.character])),expected);
  assert.equal(manifest.placements['bitgaram-observatory'],undefined);
});
for(const [id,character] of Object.entries(expected)){
  test(`${id}: guide is grounded, faces the start and leaves the first steps open`,()=>{
    const original=JSON.parse(fs.readFileSync(new URL('../public'+destinations[id].worldUrl.split('?')[0],import.meta.url),'utf8'));
    const placement=manifest.placements[id],world=withNpcObstacle(original,placement),spawn=world.spawn;
    assert.equal(placement.character,character);
    const [x,y,z]=placement.position,floors=worldFloors(original.solids);
    const startHeight=original.verticalNavigation?(reachableFloor(spawn.x,spawn.z,spawn.height??0,floors)??0):floorHeight(spawn.x,spawn.z,floors);
    const floor=original.verticalNavigation?reachableFloor(x,z,startHeight,floors,original.requireFloor):floorHeight(x,z,floors);
    assert.ok(Math.abs(y-(visibleGround[id]??floor))<.001,'Feet match the walking surface');
    assert.ok(canTravelTo([x,z],original,floor),'Guide occupies an existing walkable location');
    assert.ok(!canTravelTo([x,z],world,floor),'Visitors cannot walk through the guide');
    assert.ok(canTravelTo([spawn.x,spawn.z],world,startHeight),'Spawn remains accessible');
    assert.equal(original.solids.length+1,world.solids.length,'Source world is not mutated');
    const colliders=world.solids.filter(s=>s.collision).map(solidCollider);
    const started=movePlayer(spawn.x,spawn.z,-Math.sin(spawn.yaw)*2,-Math.cos(spawn.yaw)*2,colliders,world.bounds);
    assert.ok(Math.hypot(started.x-spawn.x,started.z-spawn.z)>1.95,'Forward path is clear');
    const offset=new THREE.Vector3(x-spawn.x,0,z-spawn.z),forward=new THREE.Vector3(-Math.sin(spawn.yaw),0,-Math.cos(spawn.yaw));
    assert.ok(offset.length()<6 && offset.dot(forward)>3);
    assert.ok(offset.angleTo(forward)<Math.PI/6,'Guide is inside the initial view');
    assert.ok(new THREE.Vector3(Math.sin(placement.yaw),0,Math.cos(placement.yaw)).dot(offset.clone().normalize().negate())>.9999,'Authored +Z front faces visitor');
    assert.ok(!original.portals?.some(p=>Math.hypot(x-p.position[0],z-p.position[1])<p.radius+placement.collisionRadius),'Doors are clear');
    const {scene}=readModel(new URL('../public'+destinations[id].modelUrl.split('?')[0].replace(/\.gz$/,''),import.meta.url));
    if(visibleGround[id]!==undefined){
      const surface=new THREE.Raycaster(new THREE.Vector3(x,y+1.5,z),new THREE.Vector3(0,-1,0),0,3).intersectObject(scene,true)[0];
      assert.ok(Math.abs(surface.point.y-y)<.001,'Guide feet sit on the visible GLB ground');
    }
    const origin=new THREE.Vector3(spawn.x,startHeight+1.72,spawn.z),target=new THREE.Vector3(x,y+placement.height*.6,z),direction=target.clone().sub(origin);
    assert.equal(new THREE.Raycaster(origin,direction.clone().normalize(),.05,direction.length()-.15).intersectObject(scene,true).length,0,'The city does not hide the guide at the start');
    scene.traverse(o=>o.geometry?.dispose());
  });
}
test('Yeongsanpo keeps Hongdoli at the start and greets pier arrivals with Beodeul-nangja before the lighthouse',()=>{
  assert.deepEqual(guidePlacements(manifest,'yeongsanpo').map(g=>[g.character,g.script]),[['hongdoli','yeongsanpo'],['beodeuri','yeongsanpo-pier']]);
  assert.deepEqual(guidePlacements(manifest,'dasi').map(g=>g.script),['dasi']);
  assert.deepEqual(guidePlacements(manifest,'bitgaram-observatory'),[]);
  const original=JSON.parse(fs.readFileSync(new URL('../public/yeongsanpo-world.json',import.meta.url),'utf8'));
  const world=guidePlacements(manifest,'yeongsanpo').reduce(withNpcObstacle,original);
  const [pier]=manifest.extraPlacements.yeongsanpo,[x,y,z]=pier.position;
  const landing=original.places.find(p=>p.id===pier.arrival),lighthouse=original.places.find(p=>p.name==='영산포 등대');
  const tower=solidCollider(original.solids.find(s=>s.name==='lighthouse_collision'));
  const towerCenter=[tower.reduce((t,p)=>t+p[0],0)/tower.length,tower.reduce((t,p)=>t+p[1],0)/tower.length];
  // The map jump lands exactly on the authored arrival, so its yaw applies.
  assert.deepEqual(mapArrival(landing,world),landing.arrival);
  const [ax,az]=landing.arrival,forward=new THREE.Vector3(-Math.sin(landing.arrivalYaw),0,-Math.cos(landing.arrivalYaw));
  assert.ok(Math.hypot(ax-towerCenter[0],az-towerCenter[1])<Math.hypot(landing.position[0]-towerCenter[0],landing.position[1]-towerCenter[1])-3,'Arrival moved toward the lighthouse');
  assert.ok(forward.dot(new THREE.Vector3(towerCenter[0]-ax,0,towerCenter[1]-az).normalize())>Math.cos(Math.PI/18),'Arrival looks at the lighthouse');
  const offset=new THREE.Vector3(x-ax,0,z-az);
  assert.ok(offset.length()<6&&offset.dot(forward)>3,'Within talking range right after arrival');
  assert.ok(offset.angleTo(forward)<Math.PI/6,'Guide is inside the arrival view');
  assert.ok(new THREE.Vector3(Math.sin(pier.yaw),0,Math.cos(pier.yaw)).dot(offset.clone().normalize().negate())>.9999,'Faces the arriving visitor');
  const floors=worldFloors(original.solids),floor=reachableFloor(x,z,y,floors,original.requireFloor);
  assert.ok(Math.abs(floor-y)<.001&&Math.abs(landing.arrivalHeight-y)<.001,'Feet on the lower riverside deck');
  assert.ok(canTravelTo([x,z],original,floor)&&!canTravelTo([x,z],world,floor),'Stands on open deck and blocks walking through');
  assert.ok(canTravelTo(landing.position,world,floor)&&canTravelTo(lighthouse.position,world,floor),'Dock and lighthouse stay reachable');
  const started=movePlayer(ax,az,forward.x*2,forward.z*2,world.solids.filter(s=>s.collision).map(solidCollider),world.bounds);
  assert.ok(Math.hypot(started.x-ax,started.z-az)>1.95,'Forward path is clear');
  const {scene}=readModel(new URL('../public/models/yeongsanpo.glb',import.meta.url));
  const surface=new THREE.Raycaster(new THREE.Vector3(x,y+1.5,z),new THREE.Vector3(0,-1,0),0,3).intersectObject(scene,true)[0];
  assert.ok(Math.abs(surface.point.y-y)<.001,'Guide feet sit on the visible deck');
  const origin=new THREE.Vector3(ax,y+1.72,az),target=new THREE.Vector3(x,y+pier.height*.6,z),direction=target.clone().sub(origin);
  assert.equal(new THREE.Raycaster(origin,direction.clone().normalize(),.05,direction.length()-.15).intersectObject(scene,true).length,0,'Nothing hides the guide at arrival');
  scene.traverse(o=>o.geometry?.dispose());
});
test('public guides match their rigged Blender exports and preserve embedded materials',()=>{
  for(const character of Object.keys(manifest.assets)){
    const raw=fs.readFileSync(new URL('../public'+manifest.assets[character].modelUrl,import.meta.url));
    const source=fs.readFileSync(new URL('../'+manifest.assets[character].authoredExport,import.meta.url));
    assert.ok(raw.equals(source),'Deployment GLB must match authored GLB exactly');
    const gltf=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)).toString());
    assert.ok(gltf.images.every(i=>i.bufferView!==undefined),'Colors need no external atlas request');
    assert.ok(gltf.nodes.some(n=>n.skin!==undefined),'Character has deforming skin');
    assert.ok(gltf.skins[0].joints.length>=18,'Skeleton is inside the model');
    assert.deepEqual(gltf.animations.map(a=>a.name).sort(),['Idle','Greeting','Explain','Nod','Listen'].sort());
    assert.ok(raw.length<5000000,'Download stays under 5MB per region guide');
    assert.ok(gltf.meshes.every(m=>m.primitives.every(p=>p.attributes.JOINTS_0!==undefined&&p.attributes.WEIGHTS_0!==undefined)));
  }
});

test('KENTECH guide and visitor heights match the exported granite paving',()=>{
  const original=JSON.parse(fs.readFileSync(new URL('../public/bitgaram-kentech-world.json',import.meta.url)));
  const placement=manifest.placements['bitgaram-kentech'];
  const {scene}=readModel(new URL('../public/models/bitgaram-kentech.glb',import.meta.url));
  const [x,y,z]=placement.position;
  const surface=new THREE.Raycaster(new THREE.Vector3(x,1,z),new THREE.Vector3(0,-1,0),0,2).intersectObject(scene,true)[0];
  assert.ok(surface,'Authored paving exists beneath the guide');
  assert.ok(Math.abs(surface.point.y-y)<.001,'Guide feet must match the visible GLB surface, not only collision metadata');
  const floors=worldFloors(original.solids);
  assert.ok(Math.abs(reachableFloor(x,z,0,floors)-surface.point.y)<.001);
  assert.ok(Math.abs(original.spawn.height-y)<.001,'Visitors start at the same paving level');
  const obstacle=withNpcObstacle(original,placement).solids.at(-1);
  assert.ok(Math.abs(obstacle.position[1]-obstacle.size[1]/2-y)<.001,'Guide collision starts at the feet');
  scene.traverse(o=>o.geometry?.dispose());
});
