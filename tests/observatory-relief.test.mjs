import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import {readModel} from './gltf-geometry.mjs';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
test('Neureoji relief uses the cross-checked surface level while retaining the 12m climb',()=>{
 const w=read('public/neureoji-world.json');
 const t=read('knowledge/sources/neureoji-v92/native-terrain.json');
 const evidence=read('knowledge/sources/observatory-relief-v96/independent-terrain.json');
 assert.ok(Math.abs(w.spawn.height-t.towerSurfaceMetres)<.0001);
 assert.ok(Math.abs(w.spawn.height-evidence.sites.neureoji[0].heightMetres)<.2);
 assert.equal(w.topDeckHeightMetres-w.spawn.height,12);
 assert.equal(w.reliefInterpretation.canopyDeductionMetres,0);
 assert.equal(w.reliefInterpretation.surveyed,false);
});
test('Bitgaram overview summit agrees with the walking scene rather than the old 16m hill',()=>{
 const w=read('public/bitgaram-park-world.json');
 const scenes=['bitgaram-overview','bitgaram-overview-part2'].map(name=>readModel(new URL(`../public/models/${name}.glb`,import.meta.url)).scene);
 const floor=scenes.map(s=>s.getObjectByName('ground_floor_summit')).find(o=>o?.children.length);
 const box=new THREE.Box3().setFromObject(floor);
 assert.ok(Math.abs(box.max.y-w.spawn.height)<.002,`${box.max.y} vs ${w.spawn.height}`);
 assert.ok(box.max.y>50,'The overview must not silently retain the previous low hill');
 const pin=read('public/bitgaram-orbit.json').pins.find(p=>p.id==='bitgaram-park');
 assert.ok(Math.abs(pin.position[1]-(w.spawn.height+18))<.001);
 for(const s of scenes)s.traverse(o=>o.geometry?.dispose());
});
test('Overview hillside follows the native geographic profile in three directions',()=>{
 const scenes=['bitgaram-overview','bitgaram-overview-part2'].map(name=>readModel(new URL(`../public/models/${name}.glb`,import.meta.url)).scene);
 const land=scenes.map(s=>s.getObjectByName('estimated_hill')).find(o=>o?.children.length);
 const g=read('knowledge/sources/bitgaram/terrain-v89/native-surface-grid.json');
 const upper=read('public/bitgaram-park-world.json').spawn.height;
 function height(x,z){
  const lat=g.originWGS84.lat-z/111320,lon=g.originWGS84.lon+x/(111320*Math.cos(g.originWGS84.lat*Math.PI/180));
  const u=(lon-g.sampleOriginLongitude)/g.longitudeSpacingDegrees,v=(g.sampleOriginLatitude-lat)/g.latitudeSpacingDegrees;
  const i=Math.floor(u),j=Math.floor(v),a=u-i,b=v-j,h=g.heightsMetres;
  return Math.max(0,Math.min(upper-.18,(h[j][i]*(1-a)+h[j][i+1]*a)*(1-b)+(h[j+1][i]*(1-a)+h[j+1][i+1]*a)*b-g.modelDatumMetres))+.02;
 }
 for(const [x,z] of [[-60,0],[60,0],[0,-60]]){
  const hits=new THREE.Raycaster(new THREE.Vector3(x,150,z),new THREE.Vector3(0,-1,0),0,160).intersectObject(land,true);
  assert.ok(hits.length);assert.ok(Math.abs(hits[0].point.y-height(x,z))<.12,`${x},${z} relief mismatch`);
 }
 for(const s of scenes)s.traverse(o=>o.geometry?.dispose());
});
