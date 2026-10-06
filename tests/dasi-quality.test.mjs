import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import * as THREE from 'three';
import {appDestinationFromSearch} from '../lib/app-destination.ts';
const raw=fs.readFileSync(new URL('../public/models/dasi-neighborhood.glb',import.meta.url));
const gltf=JSON.parse(raw.toString('utf8',20,20+raw.readUInt32LE(12)));
const world=JSON.parse(fs.readFileSync(new URL('../public/dasi-neighborhood-world.json',import.meta.url),'utf8'));
test('Dasi detailed model remains standalone, compressed and suitable for tablet transport',()=>{
  const packed=fs.readFileSync(new URL('../public/models/dasi-neighborhood.glb.gz',import.meta.url));
  assert.deepEqual(gunzipSync(packed),raw);
  assert.ok(packed.length<12*1024*1024,'School and neighborhood download budget');
  assert.ok(gltf.meshes.length<850,'Small joinery must not produce thousands of draw calls');
  assert.ok(gltf.images.length>=20&&gltf.images.every(i=>!i.uri&&i.bufferView!==undefined));
  assert.ok(gltf.materials.filter(m=>m.normalTexture).length>=10);
  assert.ok(gltf.materials.some(m=>m.name.startsWith('D80_brick')&&m.pbrMetallicRoughness.metallicRoughnessTexture));
});
test('Dasi leaves retain silhouette transparency, and photographed landmarks stay identifiable',()=>{
  for(const name of ['D80_leaf_cutout','D80_ivy_cutout']){
    const mat=gltf.materials.find(m=>m.name===name);
    assert.equal(mat?.alphaMode,'MASK');assert.equal(mat.doubleSided,true);
  }
  for(const name of ['school_name_readable','school_round_emblem','roof_west_barrel','station_blue_nameboard'])assert.ok(gltf.nodes.some(n=>n.name===name));
  assert.ok(gltf.nodes.filter(n=>n.name?.startsWith('ground_v80_')).every(n=>n.extras?.no_shadow));
});
test('school camera presets do not remove other Naju destinations or alter floor navigation',()=>{
  assert.equal(appDestinationFromSearch('?place=dasi'),'dasi');
  assert.equal(appDestinationFromSearch('?place=bitgaram'),'bitgaram');
  assert.equal(appDestinationFromSearch('?place=yeongsanpo'),'yeongsanpo');
  assert.equal(world.architectureViews.length,4);
  assert.ok(world.interior.walkRoute.length>=7);
  assert.ok(world.solids.some(s=>s.collision&&s.name.startsWith('column_collision')));
});
test('Dasi navigation matches the independently captured pre-refinement data',()=>{
  const refs=JSON.parse(fs.readFileSync(new URL('../knowledge/sources/dasi-v80-verification.json',import.meta.url),'utf8'));
  const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
  for(const ref of refs.navigation){
    const data=JSON.parse(fs.readFileSync(new URL('../public/'+ref.file,import.meta.url),'utf8'));
    const nav=Object.fromEntries(ref.navigationKeys.map(k=>[k,data[k]??null]));
    assert.equal(createHash('sha256').update(JSON.stringify(canonical(nav))).digest('hex'),ref.navigationSha256,ref.file);
    assert.equal(ref.unchanged,true);
  }
});
test('distant crowns preserve the original tree placement instead of collapsing at the origin',()=>{
  const refs=JSON.parse(fs.readFileSync(new URL('../knowledge/sources/dasi-v80-verification.json',import.meta.url),'utf8'));
  const bounds=new THREE.Box3();let count=0;
  for(const n of gltf.nodes.filter(n=>n.extras?.vegetation_lod==='far')){
    const matrix=new THREE.Matrix4();
    if(n.matrix)matrix.fromArray(n.matrix);
    else matrix.compose(new THREE.Vector3(...(n.translation??[0,0,0])),new THREE.Quaternion(...(n.rotation??[0,0,0,1])),new THREE.Vector3(...(n.scale??[1,1,1])));
    for(const p of gltf.meshes[n.mesh].primitives){
      const a=gltf.accessors[p.attributes.POSITION];
      bounds.union(new THREE.Box3(new THREE.Vector3(...a.min),new THREE.Vector3(...a.max)).applyMatrix4(matrix));
    }
    count++;
  }
  assert.ok(count>=6,'Spatially separated woodland and campus crowns');
  for(let i=0;i<3;i++){
    assert.ok(Math.abs(bounds.min.getComponent(i)-refs.canopyBounds.min[i])<.005,'Original canopy minimum');
    assert.ok(Math.abs(bounds.max.getComponent(i)-refs.canopyBounds.max[i])<.005,'Original canopy maximum');
  }
});
