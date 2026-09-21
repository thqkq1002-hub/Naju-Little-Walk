import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {batchStaticScene} from '../lib/static-scene.ts';

function extents(root){root.updateMatrixWorld(true);return new THREE.Box3().setFromObject(root,true);}
function sameBounds(before,after,tolerance=.003){
 for(const edge of ['min','max'])for(const axis of ['x','y','z'])assert.ok(Math.abs(before[edge][axis]-after[edge][axis])<tolerance,`${edge}.${axis}: ${before[edge][axis]} -> ${after[edge][axis]}`);
}
test('batching quantized interleaved positions preserves negative coordinates and fractional heights',()=>{
 const root=new THREE.Group(),material=new THREE.MeshStandardMaterial();
 for(let i=0;i<14;i++){
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.InterleavedBufferAttribute(new THREE.InterleavedBuffer(new Uint16Array([0,0,0,0,100,0,0,0,0,100,0,0]),4),3,0));
  g.setAttribute('normal',new THREE.BufferAttribute(new Int8Array([0,0,127,0,0,127,0,0,127]),3,true));
  g.setIndex([0,1,2]);const m=new THREE.Mesh(g,material);m.position.set(-400+i*13.25,2.35,-170);m.scale.setScalar(.025);root.add(m);
 }
 const before=extents(root);const stats=batchStaticScene(root);assert.equal(stats.after,1);sameBounds(before,extents(root));
 const mesh=root.children.find(o=>o.isMesh);assert.ok(mesh.geometry.attributes.position.array instanceof Float32Array);assert.ok(mesh.geometry.attributes.normal.array instanceof Float32Array);
});
test('published Bitgaram GLBs retain every building envelope after viewer batching',async()=>{
 const root=new THREE.Group(),loader=new GLTFLoader();
 for(const name of ['bitgaram-overview','bitgaram-overview-part2']){
  const b=fs.readFileSync(new URL(`../public/models/${name}.glb`,import.meta.url));
  const gltf=await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'');root.add(gltf.scene);
 }
 const before=extents(root);
 const materialBounds=()=>{const map=new Map();root.updateMatrixWorld(true);root.traverse(o=>{if(!o.isMesh)return;const key=o.material.name;const box=map.get(key)??new THREE.Box3();const p=o.geometry.attributes.position,v=new THREE.Vector3();for(let i=0;i<p.count;i++)box.expandByPoint(v.fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld));map.set(key,box);});return map;};
 const original=materialBounds();batchStaticScene(root);sameBounds(before,extents(root));const after=materialBounds();
 for(const [name,box] of original){assert.ok(after.has(name),`Missing ${name}`);sameBounds(box,after.get(name));}
});
