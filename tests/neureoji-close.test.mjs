import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import {readModel} from './gltf-geometry.mjs';
const path=new URL('../public/models/neureoji.glb',import.meta.url);
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const raw=fs.readFileSync(path),doc=JSON.parse(raw.toString('utf8',20,20+raw.readUInt32LE(12)));

test('hydrangea volumes stay opaque while the surrounding leaves retain cutout rendering',()=>{
 const cores=doc.meshes.filter(m=>m.name.startsWith('Neureoji95_bloom_core_'));
 assert.equal(cores.length,6);
 for(const mesh of cores)for(const p of mesh.primitives){
  const m=doc.materials[p.material];assert.equal(m.alphaMode??'OPAQUE','OPAQUE',mesh.name);
  assert.equal(m.pbrMetallicRoughness.baseColorFactor?.[3]??1,1);assert.ok(m.pbrMetallicRoughness.baseColorTexture);
 }
 for(const m of doc.materials.filter(m=>m.name.startsWith('Neureoji95_leaf_')))assert.equal(m.alphaMode,'MASK');
});

test('new edge tufts do not enter either walking corridor after GLB quantization',()=>{
 const {scene}=readModel(path);const grass=scene.getObjectByName('Neureoji100_path_edge_tufts');assert.ok(grass);
 const w=read('public/neureoji-world.json'),widths={'flower-road':3,'woodland-hydrangea':1.85};
 const routes=Object.entries(w.hydrangeaRoutes);
 function clearance(x,z){
  let min=Infinity;
  for(const [name,route] of routes)for(let i=1;i<route.length;i++){
   const a=route[i-1],b=route[i],dx=b[0]-a[0],dz=b[1]-a[1],length=dx*dx+dz*dz;
   const t=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/length));
   min=Math.min(min,Math.hypot(x-a[0]-t*dx,z-a[1]-t*dz)-widths[name]/2);
  }
  return min;
 }
 const p=new THREE.Vector3();let count=0;
 grass.traverse(o=>{
  if(!o.geometry)return;const pos=o.geometry.getAttribute('position');
  for(let i=0;i<pos.count;i++){
   p.fromBufferAttribute(pos,i).applyMatrix4(o.matrixWorld);
   assert.ok(clearance(p.x,p.z)>.08,`Grass intrudes at ${p.x},${p.z}`);count++;
  }
 });
 assert.ok(count>1000);scene.traverse(o=>o.geometry?.dispose());
});
