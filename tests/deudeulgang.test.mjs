import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import zlib from 'node:zlib';
import {canTravelTo,regionalPoint,regionalSize} from '../lib/map-navigation.ts';
import {destinations,destinationFromSearch} from '../lib/destinations.ts';
import {movePlayer,solidCollider} from '../lib/world.ts';
const root=new URL('../',import.meta.url);
const world=JSON.parse(fs.readFileSync(new URL('public/deudeulgang-world.json',root)));
const osm=JSON.parse(fs.readFileSync(new URL('knowledge/sources/deudeulgang/geometry.json',root)));
const geo=([lon,lat])=>[(lon-126.85475)*91175,(35.0185-lat)*111195];

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
    assert.ok(canTravelTo(p,world),`Blocked OSM path ${id}, segment ${i}: ${p}`);
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

test('distant wooded background stays opaque and outside the walking shadow pass',()=>{
 const raw=fs.readFileSync(new URL('public/models/deudeulgang.glb',root));
 const d=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
 const backdrop=d.nodes.filter(n=>n.extras?.background_only);
 assert.ok(backdrop.length>=3&&backdrop.length<=16,'Background is delivered as a bounded set of batched meshes');
 assert.equal(d.nodes.some(n=>n.name?.startsWith('west_bank_background_pine')),false,'Sparse alpha needle trees were replaced');
 for(const n of backdrop){
  assert.equal(n.extras.no_shadow,true);assert.equal(n.extras.no_receive_shadow,true);
  for(const p of d.meshes[n.mesh].primitives){
   const m=d.materials[p.material];
   assert.ok(!m.alphaMode||m.alphaMode==='OPAQUE','Canopies must not disappear from distant alpha testing');
   const t=m.pbrMetallicRoughness.baseColorTexture;
   assert.ok(t,'Wooded hills must retain their detailed forest surface');
   assert.ok(Number.isInteger(d.images[d.textures[t.index].source].bufferView),'Texture is embedded, with no external image dependency');
  }
 }
 assert.ok(world.solids.some(s=>s.name==='background_ridge_boundary'&&s.collision),'Background remains inaccessible');
});
