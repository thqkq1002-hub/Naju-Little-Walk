import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {batchStaticScene,updateVegetationDetail} from '../lib/static-scene.ts';

test('near and distant variants switch together without gaps, including aerial view',()=>{
 const root=new THREE.Group();root.position.set(200,0,-50);root.rotation.y=.3;
 for(const lod of ['near','far'])for(const x of [3,10]){
  const m=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());
  m.position.set(x,0,5);m.userData={authored_vegetation:true,vegetation_lod:lod,vegetation_distance:80};root.add(m);
 }
 batchStaticScene(root);root.updateMatrixWorld(true);
 const batches=root.children.filter(o=>o.isInstancedMesh);
 for(const [camera,expected] of [[new THREE.Vector3(12,2,12),'near'],[new THREE.Vector3(12,200,12),'far'],[new THREE.Vector3(12,2,12),'near']]){
  updateVegetationDetail(root,root.localToWorld(camera));
  assert.equal(batches.filter(b=>b.visible).length,2);
  assert.ok(batches.filter(b=>b.visible).every(b=>b.userData.vegetation_lod===expected));
 }
});

test('Blender vegetation shares geometry while preserving world placement and local bounds',()=>{
 const root=new THREE.Group();root.position.set(10,2,-7);root.rotation.y=.35;
 const geometry=new THREE.SphereGeometry(.8,8,6),material=new THREE.MeshStandardMaterial();
 const source=[];
 for(const offset of [0,210])for(let j=0;j<5;j++){
  const group=new THREE.Group();group.userData.authored_vegetation=true;group.position.set(offset+j*3,0,2);group.rotation.y=j*.25;root.add(group);
  const mesh=new THREE.Mesh(geometry,material);mesh.position.y=3;mesh.scale.set(.8,1.5,1);mesh.castShadow=true;group.add(mesh);source.push(mesh);
 }
 root.updateMatrixWorld(true);const matrices=source.map(m=>m.matrixWorld.clone());const before=new THREE.Box3().setFromObject(root);
 const stats=batchStaticScene(root);assert.equal(stats.before,10);assert.equal(stats.after,2);
 const batches=[];root.traverse(o=>{if(o instanceof THREE.InstancedMesh)batches.push(o);});assert.equal(batches.length,2);
 root.updateMatrixWorld(true);const after=new THREE.Box3().setFromObject(root);
 assert.ok(after.clone().expandByScalar(1e-4).containsBox(before),'Conservative instance bounds must enclose every plant');
 const actual=[];
 for(const b of batches){
  assert.equal(b.geometry,geometry,'Repeated vertices must stay shared');assert.ok(b.castShadow);assert.ok(b.boundingSphere.radius<15,'Distant groves must not share one global bound');
  for(let i=0;i<b.count;i++){const m=new THREE.Matrix4();b.getMatrixAt(i,m);actual.push(m.premultiply(b.matrixWorld));}
 }
 for(const expected of matrices)assert.ok(actual.some(m=>m.elements.every((v,i)=>Math.abs(v-expected.elements[i])<1e-4)));
});

test('hidden, mirrored, and transparent plants keep their original rendering semantics',()=>{
 const root=new THREE.Group(),geometry=new THREE.BoxGeometry(),solid=new THREE.MeshStandardMaterial();
 const parents=[];
 for(let i=0;i<14;i++){
  const p=new THREE.Group();p.userData.authored_vegetation=true;p.visible=false;root.add(p);const m=new THREE.Mesh(geometry,solid);p.add(m);parents.push([m,p]);
 }
 for(let i=0;i<4;i++){
  const m=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({transparent:true,opacity:.3}));m.userData.authored_vegetation=true;root.add(m);parents.push([m,root]);
 }
 for(let i=0;i<14;i++){
  const m=new THREE.Mesh(geometry,solid);m.userData.authored_vegetation=true;m.scale.x=-1;root.add(m);parents.push([m,root]);
 }
 batchStaticScene(root);
 for(const [m,p] of parents)assert.equal(m.parent,p);
});
