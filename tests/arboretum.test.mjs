import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import zlib from 'node:zlib';
import {movePlayer,solidCollider,worldFloors,floorHeight,worldObstacles,moveOnFloors} from '../lib/world.ts';
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

test('clipped evergreens keep matching habits and one continuous leaf-bearing crown',()=>{
 const raw=fs.readFileSync(new URL('../public/models/naju-arboretum.glb',import.meta.url));
 const size=raw.readUInt32LE(12),g=JSON.parse(raw.subarray(20,20+size)),bin=28+size;
 const trees=g.nodes.filter(n=>n.extras?.juniper_revision);
 assert.equal(trees.length,492,'Both representations of the 246 planted evergreens remain');
 const signature=n=>JSON.stringify([n.translation,n.rotation,n.scale,n.extras.reference_habit,n.extras.juniper_variant,n.extras.vegetation_distance]);
 assert.deepEqual(trees.filter(n=>n.extras.vegetation_lod==='near').map(signature).sort(),trees.filter(n=>n.extras.vegetation_lod==='far').map(signature).sort());
 const read=(id,component=0)=>{
  const a=g.accessors[id],v=g.bufferViews[a.bufferView],width={5121:1,5123:2,5125:4,5126:4}[a.componentType],components=a.type==='VEC3'?3:1;
  assert.ok(width);return Array.from({length:a.count},(_,i)=>{const offset=bin+v.byteOffset+(a.byteOffset??0)+i*(v.byteStride??width*components)+component*width;return a.componentType===5126?raw.readFloatLE(offset):a.componentType===5125?raw.readUInt32LE(offset):a.componentType===5123?raw.readUInt16LE(offset):raw.readUInt8(offset);});
 };
 for(const id of new Set(trees.map(n=>n.mesh))){
  const crown=g.meshes[id].primitives.find(p=>g.materials[p.material].name==='Clipped_juniper_dense_veins');
  assert.ok(crown,'A continuous dense crown remains below the fine sprays');
  const xyz=[0,1,2].map(c=>read(crown.attributes.POSITION,c));
  const keys=xyz[0].map((_,i)=>xyz.map(v=>Math.round(v[i]*10000)).join(','));
  const indices=read(crown.indices),edges=new Map();
  for(const key of keys)edges.set(key,new Set());
  for(let i=0;i<indices.length;i+=3){const tri=indices.slice(i,i+3).map(j=>keys[j]);for(const a of tri)for(const b of tri)if(a!==b)edges.get(a).add(b);}
  const visited=new Set(),queue=[keys[0]];
  for(let i=0;i<queue.length;i++){const key=queue[i];if(visited.has(key))continue;visited.add(key);for(const neighbor of edges.get(key))if(!visited.has(neighbor))queue.push(neighbor);}
  assert.equal(visited.size,edges.size,'Crown is connected across its height instead of separate stacked blobs');
 }
});
test('arboretum download is exact and regional destination stays inside the map',()=>{
 const raw=fs.readFileSync(new URL('../public/models/naju-arboretum.glb',import.meta.url));
 assert.ok(zlib.gunzipSync(fs.readFileSync(new URL('../public/models/naju-arboretum.glb.gz',import.meta.url))).equals(raw));
 const d=destinations['naju-arboretum'],p=regionalPoint(d.coordinates.lon,d.coordinates.lat);
 assert.ok(p[0]>0&&p[0]<regionalSize[0]&&p[1]>0&&p[1]<regionalSize[1]);
});

test('mapped juniper avenue and its junctions remain walkable with matching physical trees',()=>{
 const source=JSON.parse(fs.readFileSync(new URL('../knowledge/sources/arboretum/geometry.json',import.meta.url)));
 const road=source.ways.find(x=>x.id==='1258471015').points;
 const arrival=sceneArrival(w,'?at=juniper');assert.equal(arrival.entered,true);
 const floors=worldFloors(w.solids),obstacles=worldObstacles(w.solids);
 assert.equal(arrival.height,.102);assert.equal(floorHeight(arrival.x,arrival.z,floors),arrival.height);
 const place=w.places.find(p=>p.id==='juniper');assert.deepEqual(place.position,place.arrival);
 const onRoad=p=>Math.min(...road.slice(1).map((b,i)=>{const a=road[i],dx=b[0]-a[0],dz=b[1]-a[1],t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dz)/(dx*dx+dz*dz)));return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dz);}));
 assert.ok(onRoad([arrival.x,arrival.z])<.001,'Arrival is on the retained mapped road');
 for(let j=1;j<road.length;j++)for(let i=0;i<=300;i++){const t=i/300,a=road[j-1],b=road[j];assert.ok(canTravelTo([a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t],w),'Mapped avenue centreline stays clear');}
 let player={x:road[0][0],z:road[0][1],height:0};
 for(let j=1;j<road.length;j++){
  const a=road[j-1],b=road[j],steps=Math.ceil(Math.hypot(b[0]-a[0],b[1]-a[1])/.35);
  for(let i=0;i<steps;i++)player=moveOnFloors(player.x,player.z,player.height,(b[0]-a[0])/steps,(b[1]-a[1])/steps,obstacles,floors,w.bounds);
  assert.ok(Math.hypot(player.x-b[0],player.z-b[1])<.01,'Walk the actual mapped avenue with synchronized floor elevations');
 }
 for(const id of ['1258471018','1258471019']){
  const branch=source.ways.find(x=>x.id===id).points;let junction=0;
  for(let i=1;i<branch.length;i++)if(onRoad(branch[i])<onRoad(branch[junction]))junction=i;
  assert.ok(onRoad(branch[junction])<.1);
  for(const index of [junction-1,junction+1].filter(i=>i>=0&&i<branch.length)){
   const a=branch[junction],b=branch[index],length=Math.hypot(b[0]-a[0],b[1]-a[1]),distance=Math.min(12,length);
   for(let i=0;i<=80;i++){const t=distance/length*i/80;assert.ok(canTravelTo([a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t],w),'Both sides of mapped junction stay open');}
  }
 }
 const raw=fs.readFileSync(new URL('../public/models/naju-arboretum.glb',import.meta.url)),g=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
 const trees=g.nodes.filter(n=>n.extras?.vegetation_lod==='near'&&n.extras.reference_habit);
 for(const solid of w.solids.filter(s=>s.name==='tree_trunk'))assert.ok(trees.some(n=>Math.hypot(n.translation[0]-solid.position[0],n.translation[2]-solid.position[2])<.02),'No invisible trunk proxy remains');
 const asphalt=g.materials.find(m=>m.name==='Avenue_fine_asphalt');assert.ok(asphalt?.pbrMetallicRoughness.baseColorTexture&&asphalt.normalTexture);
});
test('garden flowers are rooted and rose petals have a raised cup',()=>{
 const raw=fs.readFileSync(new URL('../public/models/naju-arboretum.glb',import.meta.url));
 const g=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
 const rooted=g.nodes.filter(n=>n.name.startsWith('botanical_flower')&&n.extras?.vegetation_lod==='near');
 assert.ok(rooted.length>2000);
 for(const n of rooted)assert.ok(Math.abs(n.translation[1]-.052)<.00001,'Flower root sits on the retained soil surface');
 const roses=g.nodes.filter(n=>n.extras?.garden_kind==='rose'&&n.extras?.vegetation_lod==='near');
 assert.ok(roses.length>700);
 for(const id of new Set(roses.map(n=>n.mesh))){
  const petals=g.meshes[id].primitives.filter(p=>g.materials[p.material].name.startsWith('Garden_petals_'));
  assert.ok(petals.length);
  for(const p of petals){
   const a=g.accessors[p.attributes.POSITION];assert.ok(a.max[1]-a.min[1]>.10,'Rose petals rise above their cupped base');
   const normal=g.accessors[p.attributes.NORMAL],view=g.bufferViews[normal.bufferView],bin=28+raw.readUInt32LE(12);
   let sum=0;for(let i=0;i<normal.count;i++){
    const offset=bin+view.byteOffset+(normal.byteOffset??0)+i*(view.byteStride??(normal.componentType===5126?12:3));
    sum+=normal.componentType===5126?raw.readFloatLE(offset+4):raw.readInt8(offset+1)/127;
   }
   assert.ok(sum/normal.count>.05,'Petal fronts face out of the cup towards daylight');
  }
 }
 for(const n of g.nodes.filter(n=>n.name.startsWith('play_canopy'))){
  for(const p of g.meshes[n.mesh].primitives){assert.ok(p.attributes.TEXCOORD_0!==undefined);assert.ok(g.materials[p.material].pbrMetallicRoughness.baseColorTexture);}
 }
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
