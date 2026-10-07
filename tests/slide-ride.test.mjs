import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import {readModel} from './gltf-geometry.mjs';
import {SlideRide,slideRideUrl,withSlideLanding} from '../lib/slide-ride.ts';
import {blocksWalking,hitsPolygon,moveOnFloors,reachableFloor,worldFloors,worldObstacles} from '../lib/world.ts';

const read=path=>JSON.parse(fs.readFileSync(new URL('../'+path,import.meta.url),'utf8'));
const ride=read('public/bitgaram-slide-ride.json');
const original=read('public/bitgaram-park-world.json');
const world=withSlideLanding(original,ride);
const floors=worldFloors(world.solids),obstacles=worldObstacles(world.solids);
const runToEnd=(reduced=false)=>{const r=new SlideRide(ride);const poses=[];let t=0;while(!r.done&&t<60){poses.push(r.update(1/60,reduced));t+=1/60;}return {r,poses,t};};

test('the ride follows the v101 slide centreline from the summit lip to the mat',()=>{
  assert.equal(slideRideUrl('bitgaram-park')?.split('?')[0],'/bitgaram-slide-ride.json');
  assert.equal(slideRideUrl('dasi'),undefined);
  const centre=read('knowledge/sources/bitgaram/access-v101/navigation-profiles.json').slide_route;
  const near=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2])<.01;
  assert.ok(near(ride.route[0],centre[0])&&near(ride.route.at(-3),centre.at(-1)),'Trough part is the authored centreline');
  assert.ok(ride.route.slice(-2).every(p=>Math.abs(p[1]-ride.mat.height)<1e-9),'Run-out lies on the mat top');
  assert.ok(ride.route[0][1]-ride.route.at(-1)[1]>34,'Descends the whole hillside');
});

test('visitors can reach the chute mouth from the summit shelter',()=>{
  const {entry}=ride,summit=original.places.find(p=>p.id==='summit');
  const floor=reachableFloor(entry.x,entry.z,entry.height,floors,world.requireFloor);
  assert.ok(Math.abs(floor-summit.arrivalHeight)<.01&&!blocksWalking(entry.x,entry.z,floor,obstacles));
  assert.ok(Math.hypot(entry.x-ride.route[0][0],entry.z-ride.route[0][2])<1.2,'Walking forward from here starts the ride');
});

test('a ride takes about fifteen seconds, feels fast, and slows onto the mat',()=>{
  const {r,poses,t}=runToEnd();
  assert.ok(t>10&&t<25,`ride ${t.toFixed(1)} s`);
  const top=Math.max(...poses.map(p=>p.speed));
  assert.ok(top>=25&&top<=45,`top speed ${top} km/h`);
  const touch=poses.find(p=>p.landed);
  assert.ok(touch.speed<=15,`reaches the mat at ${touch.speed} km/h`);
  assert.ok(poses.every(p=>Math.abs(p.roll)<=.22+1e-9&&p.fov>=60&&p.fov<=74.01));
  assert.ok(poses.some(p=>Math.abs(p.roll)>.1),'Banks through the curves');
  const end=poses.at(-1);
  assert.ok(end.done&&end.speed===0&&Math.abs(end.eye-1.72)<1e-9&&end.roll===0&&end.fov===60,'Stands up at normal eye height');
  assert.ok(hitsPolygon(end.x,end.z,ride.mat.floor,0),'Stops on the mat');
  assert.ok(r.s-r.troughEnd>.8,'Slides well onto the mat, not at its edge');
});

test('reduced motion keeps the descent but drops shake, banking and the speed zoom',()=>{
  const {poses}=runToEnd(true);
  assert.ok(poses.every(p=>p.roll===0&&p.fov===60));
  assert.ok(poses.at(-1).done);
});

test('the landing mat is walkable and joins the stair landing and lower paths',()=>{
  const end=runToEnd().poses.at(-1);
  const start=reachableFloor(end.x,end.z,end.y,floors,world.requireFloor);
  assert.ok(Math.abs(start-ride.mat.height)<1e-6);
  assert.equal(reachableFloor(end.x,end.z,end.y,worldFloors(original.solids),original.requireFloor),null,'Without the mat this spot is unwalkable lawn');
  const walk=(to)=>{let p={x:end.x,z:end.z,height:start};for(let i=0;i<400&&Math.hypot(p.x-to[0],p.z-to[1])>.05;i++){const d=Math.min(.1,Math.hypot(to[0]-p.x,to[1]-p.z)),a=Math.atan2(to[1]-p.z,to[0]-p.x);p=moveOnFloors(p.x,p.z,p.height,Math.cos(a)*d,Math.sin(a)*d,obstacles,floors,world.bounds,world.requireFloor);}return p;};
  const arrival=original.arrivals.slide;
  const off=walk([arrival.x,arrival.z]);
  assert.ok(Math.hypot(off.x-arrival.x,off.z-arrival.z)<.06&&Math.abs(off.height-arrival.height)<.05,'Steps off to the foot of the side stairs');
});

test('the Blender mat lies on the lawn without floating or sinking out of sight',()=>{
  const bytes=fs.readFileSync(new URL('../public'+ride.mat.modelUrl,import.meta.url));
  assert.ok(bytes.length<200_000);
  const {scene:mat}=readModel(new URL('../public'+ride.mat.modelUrl,import.meta.url));
  const box=new THREE.Box3().setFromObject(mat);
  assert.ok(Math.abs(box.max.y)<.02&&box.min.y<-.55&&Math.abs(box.max.x-box.min.x-2.05)<.05&&Math.abs(box.max.z-box.min.z-3.11)<.05);
  const {scene}=readModel(new URL('../public/models/bitgaram-park.glb',import.meta.url));scene.updateMatrixWorld(true);
  const bottom=ride.mat.height+box.min.y;
  for(const [x,z] of ride.mat.floor){
    const ground=new THREE.Raycaster(new THREE.Vector3(x,ride.mat.height+1,z),new THREE.Vector3(0,-1,0),0,3).intersectObject(scene,true)[0].point.y;
    assert.ok(ground<ride.mat.height-.03,'Mat top stays above the lawn and deck');
    assert.ok(ground>bottom,'Mat body reaches into the ground: no gap under its edge');
  }
  scene.traverse(o=>o.geometry?.dispose());
});
