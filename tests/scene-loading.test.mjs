import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {batchStaticScene,batchStaticSceneInSlices} from '../lib/static-scene.ts';

function fixture(){
 const root=new THREE.Group();root.position.set(-300,7,42);root.rotation.y=.43;
 const material=new THREE.MeshStandardMaterial();
 for(let i=0;i<48;i++){
  const geometry=new THREE.BoxGeometry(1,.7,2);
  const mesh=new THREE.Mesh(geometry,material);mesh.position.set(i*2.13,.25+i%3,-i*1.27);mesh.rotation.y=i*.07;mesh.scale.set(.73,1.2,.9);
  mesh.userData.hide_in_overview=true;root.add(mesh);
 }
 return root;
}
function bounds(root){root.updateMatrixWorld(true);return new THREE.Box3().setFromObject(root,true);}
function worldPoints(root){
 root.updateMatrixWorld(true);const result=[];
 root.traverse(o=>{if(!o.isMesh)return;const a=o.geometry.getAttribute('position');for(let i=0;i<a.count;i++){const p=new THREE.Vector3().fromBufferAttribute(a,i).applyMatrix4(o.matrixWorld);result.push(p.toArray().map(v=>v.toFixed(3)).join(','));}});
 return result.sort();
}

test('sliced loading keeps authored vertices, materials and cutaway flags and lets a timer run',async()=>{
 const sync=fixture(),sliced=fixture(),expected=worldPoints(sync),before=bounds(sync);
 const syncStats=batchStaticScene(sync);let ticks=0,progress=[];
 const stats=await batchStaticSceneInSlices(sliced,{budgetMs:0,onProgress:(n,total)=>progress.push([n,total]),yieldControl:()=>new Promise(resolve=>setTimeout(()=>{ticks++;resolve();},0))});
 assert.ok(ticks>20,'Other browser work must receive time while geometry is processed');
 assert.deepEqual(stats,syncStats);assert.deepEqual(worldPoints(sliced),worldPoints(sync));
 const after=bounds(sliced);assert.ok(before.min.distanceTo(after.min)<.001&&before.max.distanceTo(after.max)<.001);
 assert.equal(sliced.children.length,1);assert.equal(sliced.children[0].userData.hide_in_overview,true);
 assert.equal(expected.length,worldPoints(sliced).length);assert.deepEqual(progress.at(-1),[1,1]);
});

test('cancelled sliced loading releases temporary geometry and preserves remaining source geometry',async()=>{
 const root=fixture(),expected=worldPoints(root),abort=new AbortController();let ticks=0,disposed=0;
 const clone=THREE.BufferGeometry.prototype.clone;
 THREE.BufferGeometry.prototype.clone=function(){const g=clone.call(this);g.addEventListener('dispose',()=>disposed++);return g;};
 try {
  await assert.rejects(batchStaticSceneInSlices(root,{signal:abort.signal,budgetMs:0,yieldControl:async()=>{if(++ticks===8)abort.abort();}}),{name:'AbortError'});
  assert.ok(disposed>=5,'All cloned geometry created before cancellation must be disposed');
  assert.deepEqual(worldPoints(root),expected);assert.equal(root.children.length,48);
 } finally {THREE.BufferGeometry.prototype.clone=clone;}
});
