import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import * as THREE from 'three';
import {readModel} from './gltf-geometry.mjs';
import {canTravelTo} from '../lib/map-navigation.ts';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const w=read('public/yeongsanpo-world.json'),report=read('knowledge/sources/yeongsanpo-crop-v90.json');
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const hash=v=>createHash('sha256').update(JSON.stringify(canonical(v))).digest('hex');
let modelScene;
const scene=()=>modelScene??=(readModel(new URL('../public/models/yeongsanpo.glb',import.meta.url)).scene);
test('exported geometry no longer contains the marked opposite-bank background',()=>{
 const extent=new THREE.Box3().setFromObject(scene());
 assert.ok(extent.min.z>=report.northCutMetres-.002,`Geometry remains outside crop: ${extent.min.z}`);
 assert.ok(report.removedObjects.some(n=>n.startsWith('north_bank_background')));
 assert.ok(report.afterVisualExtent[2]>report.beforeVisualExtent[2]);
 assert.ok(extent.max.z>=290,'South-side streets are retained');
});
test('river, bridge floors, roads and walking bounds stop at the same crop',()=>{
 assert.equal(w.bounds[2],report.northCutMetres);
 for(const s of w.solids)for(const p of s.footprint??[])assert.ok(p[1]>=w.bounds[2]-1e-7,s.name);
 for(const poly of [...w.navigationWater.polygons,...w.navigationWater.obstacles])for(const p of poly)assert.ok(p[1]>=w.bounds[2]-1e-7);
 for(const r of w.roads)for(const p of r.points)assert.ok(p[1]>=w.bounds[2]-1e-7,r.id);
 assert.equal(canTravelTo([-190,-260],w,0),false,'The removed bridge end cannot be reached through the map');
 const bridge=w.roads.find(r=>r.id==='way/303738250').points;
 const a=bridge.at(-2),b=bridge.at(-1),t=.99;
 assert.ok(canTravelTo([a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])],w,0),'Retained bridge approach remains walkable');
});
test('crop preserves the exact riverfront arrivals, museum portals and authored boats',()=>{
 for(const [key,r] of Object.entries(report.preservedNavigation)){
  assert.equal(r.beforeSha256,r.afterSha256,key+' preservation');
  assert.equal(hash(w[key]??null),r.beforeSha256,key+' current data');
 }
 assert.equal(w.boats.length,2);assert.equal(w.portals.length,2);
 assert.ok(report.uncroppedSolidCount>w.solids.length-10,'Only far-north collision footprints may change');
});
test('western bridge stops at the mapped opposite bank without a floating extension',()=>{
 const route=w.roads.find(r=>r.id==='way/303738250').points,a=route.at(-2),b=route.at(-1);
 const [p,q]=report.westernBridgeEndBoundary;
 const cross=(q[0]-p[0])*(b[1]-p[1])-(q[1]-p[1])*(b[0]-p[0]);
 assert.ok(Math.abs(cross)/Math.hypot(q[0]-p[0],q[1]-p[1])<.002,'Bridge end must meet the recorded river bank');
 const length=Math.hypot(b[0]-a[0],b[1]-a[1]),x=b[0]+(b[0]-a[0])/length*10,z=b[1]+(b[1]-a[1])/length*10;
 const hits=new THREE.Raycaster(new THREE.Vector3(x,1,z),new THREE.Vector3(0,-1,0),0,2).intersectObject(scene(),true);
 assert.equal(hits.length,0,'Bridge road remains suspended beyond the cropped shore');
 assert.equal(canTravelTo([x,z],w,0),false);
});
