import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import zlib from 'node:zlib';
import {movePlayer,solidCollider} from '../lib/world.ts';
import {canTravelTo,regionalPoint,regionalSize} from '../lib/map-navigation.ts';
import {destinations} from '../lib/destinations.ts';
import {sceneArrival} from '../lib/scene-travel.ts';
const w=JSON.parse(fs.readFileSync(new URL('../public/naju-arboretum-world.json',import.meta.url)));

test('photo-informed plants export matching near and far instances with embedded materials',()=>{
 const raw=fs.readFileSync(new URL('../public/models/naju-arboretum.glb',import.meta.url));
 const g=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
 const plants=g.nodes.filter(n=>n.extras?.vegetation_lod);
 const signature=n=>JSON.stringify([n.translation,n.rotation,n.scale,n.extras.vegetation_distance]);
 const near=plants.filter(n=>n.extras.vegetation_lod==='near').map(signature).sort();
 const far=plants.filter(n=>n.extras.vegetation_lod==='far').map(signature).sort();
 assert.ok(near.length>6000);assert.deepEqual(near,far,'Distance switching must not shift or lose any plant');
 for(const kind of ['column','oval','meta','broad'])assert.ok(g.nodes.some(n=>n.extras?.reference_habit===kind));
 assert.ok(g.images.every(i=>i.bufferView!==undefined),'All authored image textures must be embedded');
});
test('arboretum main avenue is continuous, and trunks and pond block walking',()=>{
 const obstacles=w.solids.filter(s=>s.collision).map(solidCollider);
 assert.ok(canTravelTo([w.spawn.x,w.spawn.z],w));
 let p={x:w.spawn.x,z:w.spawn.z};
 for(let i=0;i<1600;i++)p=movePlayer(p.x,p.z,.245,.05,obstacles,w.bounds);
 assert.ok(Math.hypot(p.x-w.spawn.x,p.z-w.spawn.z)>390,'Walk the whole main avenue');
 const trunk=w.solids.find(s=>s.name==='tree_trunk');assert.equal(canTravelTo([trunk.position[0],trunk.position[2]],w),false);
 const pond=w.solids.find(s=>s.name==='pond_boundary');
 const a=pond.footprint[0],b=pond.footprint[1];assert.equal(canTravelTo([(a[0]+b[0])/2,(a[1]+b[1])/2],w),false);
});
test('arboretum download is exact and regional destination stays inside the map',()=>{
 const raw=fs.readFileSync(new URL('../public/models/naju-arboretum.glb',import.meta.url));
 assert.ok(zlib.gunzipSync(fs.readFileSync(new URL('../public/models/naju-arboretum.glb.gz',import.meta.url))).equals(raw));
 const d=destinations['naju-arboretum'],p=regionalPoint(d.coordinates.lon,d.coordinates.lat);
 assert.ok(p[0]>0&&p[0]<regionalSize[0]&&p[1]>0&&p[1]<regionalSize[1]);
});
test('satellite revision replaces old building collisions and keeps garden arrival open',()=>{
 assert.ok(w.solids.filter(s=>s.name.startsWith('traced_building_')&&s.collision).length>=4);
 assert.ok(!w.solids.some(s=>s.name.startsWith('estimated_building_')||s.name==='estimated_greenhouse'));
 const garden=w.places.find(p=>p.id==='garden');assert.ok(canTravelTo(garden.arrival,w));
 for(const building of w.solids.filter(s=>s.name.startsWith('traced_building_'))){
  const p=building.footprint;const center=[p.reduce((n,a)=>n+a[0],0)/p.length,p.reduce((n,a)=>n+a[1],0)/p.length];
  assert.equal(canTravelTo(center,w),false);
 }
});
test('walking surfaces carry embedded color and normal textures',()=>{
 const raw=fs.readFileSync(new URL('../public/models/naju-arboretum.glb',import.meta.url));
 const g=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
 for(const name of ['Authored_bark_grain','Authored_fine_path','Authored_meadow','Authored_timber']){
  const m=g.materials.find(m=>m.name===name);assert.ok(m?.pbrMetallicRoughness?.baseColorTexture,name);assert.ok(m.normalTexture,name);
 }
 assert.ok(g.images.every(i=>i.bufferView!==undefined),'Materials do not depend on external photo servers');
});

test('playground and flowers have reachable arrivals and continuous access walks',()=>{
 const local=(s,t)=>[-475+.98*s-.2*t,-50+.2*s+.98*t];
 for(const id of ['playground','flowers']){
  const p=w.places.find(p=>p.id===id);assert.ok(p?.arrival,id);
  assert.ok(canTravelTo(p.arrival,w),id+' arrival');
  assert.equal(sceneArrival(w,'?at='+id).entered,true);
 }
 for(const route of [[[220,0],[220,-28],[217,-43],[220,-52]],[[181,0],[181,100]]]){
  for(let j=1;j<route.length;j++)for(let k=0;k<=100;k++){
   const t=k/100,a=route[j-1],b=route[j];
   assert.ok(canTravelTo(local(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t),w),'access walk '+j+' '+k);
  }
 }
 const slide=w.solids.find(s=>s.name==='play_slide_collision');assert.ok(slide?.collision);
 const center=[0,1].map(i=>slide.footprint.reduce((n,p)=>n+p[i],0)/slide.footprint.length);
 assert.equal(canTravelTo(center,w),false,'the slide cannot be walked through');
});
