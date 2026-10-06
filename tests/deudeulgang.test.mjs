import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import zlib from 'node:zlib';
import {canTravelTo,regionalPoint,regionalSize} from '../lib/map-navigation.ts';
import {destinations,destinationFromSearch} from '../lib/destinations.ts';
import {moveOnFloors,solidCollider,worldFloors,worldObstacles} from '../lib/world.ts';
const root=new URL('../',import.meta.url);
const world=JSON.parse(fs.readFileSync(new URL('public/deudeulgang-world.json',root)));
const osm=JSON.parse(fs.readFileSync(new URL('knowledge/sources/deudeulgang/geometry.json',root)));
const geo=([lon,lat])=>[(lon-126.85475)*91175,(35.0185-lat)*111195];

test('far water is cropped in both the authored GLB and navigation footprint',()=>{
 const report=JSON.parse(fs.readFileSync(new URL('knowledge/sources/deudeulgang/river-trim-v82.json',root)));
 const river=world.solids.find(s=>s.name==='mapped_river_water').footprint;
 assert.deepEqual(river,world.solids.find(s=>s.name==='river_no_walking').footprint);
 assert.deepEqual(river,report.riverFootprint);
 assert.equal(world.bounds[0],report.cutMinimumX);
 assert.ok(river.every(p=>p[0]>=report.cutMinimumX));
 const area=p=>Math.abs(p.reduce((sum,a,i)=>{const b=p[(i+1)%p.length];return sum+a[0]*b[1]-b[0]*a[1]},0))/2;
 assert.ok(Math.abs(area(river)-report.riverAreaAfter)<.001);
 assert.ok(report.removedPercent>45&&report.removedPercent<60);
 assert.ok(report.sourceUnchanged&&report.allNonWaterMeshesUnchanged);
 assert.ok(report.protectedMeshObjects>=560);
 const raw=fs.readFileSync(new URL('public/models/deudeulgang.glb',root));
 const d=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
 const water=d.nodes.find(n=>n.name==='mapped_river_water');
 for(const p of d.meshes[water.mesh].primitives)
  assert.ok(d.accessors[p.attributes.POSITION].min[0]>=report.cutMinimumX-.001);
});

test('Drdeulgang is selectable and its geographic pin is inside the regional map',()=>{
 assert.equal(destinationFromSearch('?place=deudeulgang'),'deudeulgang');
 const {lon,lat}=destinations.deudeulgang.coordinates,p=regionalPoint(lon,lat);
 assert.ok(p[0]>0&&p[0]<regionalSize[0]&&p[1]>0&&p[1]<regionalSize[1]);
 assert.ok(canTravelTo([world.spawn.x,world.spawn.z],world));
 for(const p of world.places)assert.ok(canTravelTo(p.arrival,world),p.name);
});
test('mapped pine-grove centreline remains walkable continuously',()=>{
 const colliders=world.solids.filter(s=>s.collision).map(solidCollider);
 for(const id of ['1306096510','1306096511']){
  const path=osm.ways.find(w=>w.id===id).points.map(geo);
  for(let i=1;i<path.length;i++){
   const a=path[i-1],b=path[i],len=Math.hypot(b[0]-a[0],b[1]-a[1]);
   for(let j=0;j<=Math.ceil(len*2);j++){
    const t=j/Math.ceil(len*2),p=[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t];
    if(p[1]>world.cropRevision.trailEnd)continue; // off-grove continuation was intentionally removed
    assert.ok(canTravelTo(p,world),`Blocked retained OSM path ${id}, segment ${i}: ${p}`);
   }
  }
 }
 // A point in the river cannot be used as a map teleport destination.
 assert.equal(canTravelTo([-150,50],world),false);
 assert.equal(canTravelTo([-225,0],world),false,'Background hillside cannot be used as a flat walking surface');
 const trunk=world.solids.find(s=>s.name.startsWith('pine_trunk_'));
 assert.equal(canTravelTo([trunk.position[0],trunk.position[2]],world),false);
});
test('pine canopy has paired authored LOD, alpha-tested needles and exact gzip transport',()=>{
 const raw=fs.readFileSync(new URL('public/models/deudeulgang.glb',root));
 const packed=fs.readFileSync(new URL('public/models/deudeulgang.glb.gz',root));
 assert.deepEqual(zlib.gunzipSync(packed),raw);assert.ok(raw.length<32*1024*1024);
 const d=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
 const near=d.nodes.filter(n=>n.name?.startsWith('old_pine_')),far=d.nodes.filter(n=>n.name?.startsWith('distant_pine_'));
 assert.equal(near.length,280);assert.equal(far.length,near.length);
 const material=d.materials.find(m=>m.name==='Pine_needles_alpha_clip');
 assert.equal(material.alphaMode,'MASK');assert.ok(material.pbrMetallicRoughness.baseColorTexture);
 for(const n of near){assert.equal(n.extras.authored_vegetation,true);assert.equal(n.extras.vegetation_lod,'near');}
 // Distant alpha minification must not remove the whole needle-bearing crown.
 const crownIndex=d.materials.findIndex(m=>m.name==='Pine_layered_crown_opaque_v70');
 assert.ok(crownIndex>=0);assert.ok(!d.materials[crownIndex].alphaMode||d.materials[crownIndex].alphaMode==='OPAQUE');
 const count=n=>d.meshes[n.mesh].primitives.reduce((sum,p)=>sum+d.accessors[p.indices].count/3,0);
 for(let i=0;i<near.length;i++){
  const a=near.find(n=>n.name==='old_pine_'+i),b=far.find(n=>n.name==='distant_pine_'+i);
  for(const key of ['translation','rotation','scale'])assert.deepEqual(a[key],b[key],`Mismatched distance pair ${i}: ${key}`);
  for(const n of [a,b])assert.ok(d.meshes[n.mesh].primitives.some(p=>p.material===crownIndex));
  assert.ok(count(b)<count(a)*.7,'Distant trees must reduce geometry');
 }
});

test('compact grove contains no hills, fields, bridge or external roads',()=>{
 const raw=fs.readFileSync(new URL('public/models/deudeulgang.glb',root));
 const d=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
 const removed=/^(background_|estimated_|west_bank_|satellite_field|crop_row|bridge_|road_parking|ground_floor_landscape)/;
 assert.equal(d.nodes.some(n=>removed.test(n.name??'')),false);
 assert.equal(world.solids.some(s=>removed.test(s.name)),false);
 assert.ok(d.nodes.some(n=>n.name==='mapped_river_water'));
 assert.equal(d.materials.some(m=>m.name==='Background_mixed_woodland_texture'),false);
 assert.ok(packedSize()<6*1024*1024,'Removing the background must reduce the transport size');
 assert.ok(world.bounds[1]-world.bounds[0]<350);
 assert.ok(world.bounds[3]-world.bounds[2]<500);
 const river=world.solids.find(s=>s.name==='river_no_walking');
 for(const [x,z] of river.footprint)assert.ok(x>=world.bounds[0]&&x<=world.bounds[1]&&z>=world.bounds[2]&&z<=world.bounds[3]);
});
const packedSize=()=>fs.statSync(new URL('public/models/deudeulgang.glb.gz',root)).size;

test('removed land is inaccessible and retained paths cannot lead into water or empty sky',()=>{
 assert.equal(world.requireFloor,true);assert.equal(world.verticalNavigation,true);
 for(const p of [[75,0],[-228,0],[60,200],[-150,50],[0,279]])assert.equal(canTravelTo(p,world),false,String(p));
 const p=world.places.find(p=>p.id==='riverside').arrival;
 const result=moveOnFloors(...p,0,-200,0,worldObstacles(world.solids),worldFloors(world.solids),world.bounds,true);
 assert.ok(result.x>world.bounds[0]+1,'Crossing the entire river must be blocked');
 assert.ok(canTravelTo([result.x,result.z],world,result.height));
 const source=JSON.parse(fs.readFileSync(new URL('knowledge/sources/deudeulgang/crop-v81.json',root)));
 assert.equal(source.sourceUnchanged,true);assert.equal(source.pineObjectsPreserved,560);
});
