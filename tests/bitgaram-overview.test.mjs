import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import zlib from 'node:zlib';
const read=p=>fs.readFileSync(new URL('../'+p,import.meta.url));
test('district overview transports exact geometry and retains destination pins',()=>{
 let triangles=0;
 for(const name of ['bitgaram-overview','bitgaram-overview-part2']){
 const raw=read(`public/models/${name}.glb`);assert.ok(raw.length<32*1024*1024);assert.ok(zlib.gunzipSync(read(`public/models/${name}.glb.gz`)).equals(raw));
 const g=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
 assert.ok(g.meshes.length>10);assert.ok(g.buffers.every(b=>!b.uri));
 for(const mesh of g.meshes)for(const p of mesh.primitives){const a=g.accessors[p.indices];assert.equal(a.componentType,5123);assert.ok(a.max[0]<g.accessors[p.attributes.POSITION].count);triangles+=a.count/3;}
 for(const a of g.accessors)for(const values of [a.min,a.max])if(values)assert.ok(values.every(Number.isFinite));
 }
 assert.equal(triangles,JSON.parse(read('knowledge/sources/bitgaram/district-color-metrics.json')).triangles,'Both transport parts together keep every triangle');
 const pins=JSON.parse(read('public/bitgaram-orbit.json')).pins;
 assert.deepEqual(pins.map(p=>p.id).sort(),['bitgaram-kentech','bitgaram-kepco','bitgaram-park']);
 for(const p of pins)assert.ok(p.position.every(Number.isFinite));
});
test('Blender roof and wall palette survives both GLB transport parts',()=>{
 const palette=JSON.parse(read('knowledge/sources/bitgaram/district-palette.json'));
 const revision=JSON.parse(read('knowledge/sources/palette-v51/bitgaram-overview.json')).changes;
 const linear=h=>[1,3,5].map(i=>{const v=parseInt(h.slice(i,i+2),16)/255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;});
 const used=[];
 for(const name of ['bitgaram-overview','bitgaram-overview-part2']){
  const raw=read(`public/models/${name}.glb`),g=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
  for(const mesh of g.meshes)for(const p of mesh.primitives)used.push(g.materials[p.material].pbrMetallicRoughness.baseColorFactor);
 }
 const has=hex=>{
  const original=linear(hex);
  // The broad palette families remain; compare against Blender's current colour revision.
  const expected=revision.find(s=>original.every((v,i)=>Math.abs(v-s.before[i])<.00001))?.after??original;
  return used.some(c=>c&&expected.slice(0,3).every((v,i)=>Math.abs(v-c[i])<.00001));
 };
 assert.ok(palette.walls.filter(has).length>=4);assert.ok(palette.roofs.filter(has).length>=4);assert.ok(has(palette.water));
 const m=JSON.parse(read('knowledge/sources/bitgaram/district-color-metrics.json'));assert.ok(m.counts.building_shells>400&&m.counts.roof_faces>400);assert.ok(m.counts.sports_courts>10);
});
test('apartment window finishes retain outward faces and compact normals in transport',()=>{
 const seen=new Set();let panes=0,frames=0;
 for(const name of ['bitgaram-overview','bitgaram-overview-part2']){
  const raw=read(`public/models/${name}.glb`),g=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
  for(const mesh of g.meshes)for(const p of mesh.primitives){
   const material=g.materials[p.material];
   if(!material.name.startsWith('Apartment_'))continue;
   seen.add(material.name);assert.equal(material.doubleSided??false,false);
   const normals=g.accessors[p.attributes.NORMAL];assert.equal(normals.componentType,5120);assert.equal(normals.normalized,true);
   const triangles=g.accessors[p.indices].count/3;
   if(material.name.startsWith('Apartment_glass_stack_'))panes+=triangles;else frames+=triangles;
  }
 }
 const verification=JSON.parse(read('knowledge/sources/bitgaram/district-facade-v60-verification.json'));
 assert.equal(seen.size,4);assert.equal(panes,verification.outward_window_faces*2);assert.equal(frames,verification.frame_faces*2);
 assert.equal(verification.all_windows_outward,true);assert.equal(verification.protected_geometry_matches_source,true);
});
test('parked cars stay within mapped parking polygons',()=>{
 const m=JSON.parse(read('knowledge/sources/bitgaram/district-street-detail-metrics.json'));
 const sources=new Map(JSON.parse(read('knowledge/sources/bitgaram/district-2026-09-20.json')).ways.map(w=>[w.id,w]));
 const old=JSON.parse(read('knowledge/sources/bitgaram/geometry.json')).ways;for(const w of old)if(!sources.has(w.id))sources.set(w.id,w);
 const inside=([x,z],p)=>{let hit=false;for(let i=0,j=p.length-1;i<p.length;j=i++){const a=p[i],b=p[j];if((a[1]>z)!==(b[1]>z)&&x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0])hit=!hit;}return hit;};
 const cars=m.placements.filter(p=>p.type==='car');assert.equal(cars.length,m.counts.parked_cars);assert.ok(cars.length>20);
 for(const c of cars){const source=sources.get(c.source_id);assert.equal(source.tags.amenity,'parking');assert.ok(c.polygon.every(pt=>inside(pt,source.points)));}
 assert.ok(m.counts.facades>100&&m.counts.window_panels>1000);
});
test('satellite block infill remains outside mapped buildings and water',()=>{
 const m=JSON.parse(read('knowledge/sources/bitgaram/district-block-infill-metrics.json'));
 assert.equal(m.added,m.buildings.length);assert.ok(m.apartments>=30);assert.ok(m.houses>=100);
 const ways=JSON.parse(read('knowledge/sources/bitgaram/district-2026-09-20.json')).ways;
 const blocked=ways.filter(w=>w.tags.building||w.tags.natural==='water').map(w=>w.points);
 const inside=([x,z],p)=>{let hit=false;for(let i=0,j=p.length-1;i<p.length;j=i++){const a=p[i],b=p[j];if((a[1]>z)!==(b[1]>z)&&x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0])hit=!hit;}return hit;};
 for(const b of m.buildings){
  assert.ok(b.estimated_footprint&&b.source);assert.ok(b.height>0&&b.height<80);
  assert.ok(b.polygon.flat().every(Number.isFinite));
  const center=b.polygon.reduce((a,p)=>[a[0]+p[0]/b.polygon.length,a[1]+p[1]/b.polygon.length],[0,0]);
  assert.ok(!blocked.some(p=>inside(center,p)),`Building ${b.id} overlaps mapped footprint`);
 }
});
test('district additions distinguish mapped buildings and estimated satellite roofs',()=>{
 const m=JSON.parse(read('knowledge/sources/bitgaram/district-completion-metrics.json'));
 const source=new Map(JSON.parse(read('knowledge/sources/bitgaram/district-2026-09-20.json')).ways.map(w=>[w.id,w]));
 assert.ok(m.counts.mapped_buildings>=80);assert.ok(m.counts.parking_areas>0);assert.ok(m.counts.sports_areas>0);
 assert.equal(m.buildings.filter(b=>b.estimated_footprint).length,m.counts.estimated_roofs);
 for(const b of m.buildings){assert.ok(b.height>0&&b.height<=160);if(!b.estimated_footprint)assert.ok(source.get(b.id)?.tags.building);}
});
