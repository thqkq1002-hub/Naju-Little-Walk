import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {readModel} from './gltf-geometry.mjs';

test('the forest end retains timber while both hydrangea approaches retain concrete',()=>{
 const {scene,gltf}=readModel(new URL('../public/models/neureoji.glb',import.meta.url));
 let timber=0,concrete=0;
 for(const name of ['walk-floor_hydrangea_flower-road','walk-floor_hydrangea_woodland-hydrangea']){
  const group=scene.getObjectByName(name),mesh=gltf.meshes.find(m=>m.name===name);
  assert.ok(group&&mesh);
  for(const [i,object] of group.children.entries()){
   const material=gltf.materials[mesh.primitives[i].material];
   const p=object.geometry.getAttribute('position'),index=object.geometry.index;
   const points=[new THREE.Vector3(),new THREE.Vector3(),new THREE.Vector3()];
   for(let j=0;j<(index?.count??p.count);j+=3){
    points.forEach((v,k)=>v.fromBufferAttribute(p,index?index.getX(j+k):j+k).applyMatrix4(object.matrixWorld));
    const z=points.reduce((s,v)=>s+v.z,0)/3;
    // Side faces straddling the original boundary are allowed either surface.
    if(Math.abs(z+190)<.5)continue;
    const expected=name.endsWith('woodland-hydrangea')&&z<-190;
    assert.equal(material.name,expected?'Neureoji102_boardwalk_timber':'Neureoji99_path_aggregate',`${name} z=${z}`);
    assert.ok(material.pbrMetallicRoughness.baseColorTexture);
    if(expected)timber++;else concrete++;
   }
  }
 }
 assert.ok(timber>50&&concrete>100);
 scene.traverse(o=>o.geometry?.dispose());
});
