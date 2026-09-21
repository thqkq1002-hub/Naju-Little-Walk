import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {createLocalLights} from '../lib/local-lights.ts';

test('campus keeps eight lights while following visitors between distant rooms',()=>{
  const scene=new THREE.Scene();
  const fixtures=Array.from({length:130},(_,i)=>({position:[i*4,3,0],color:'#ffffff',intensity:10,distance:12}));
  const {pool,update}=createLocalLights(scene,fixtures);
  assert.equal(pool.length,8);
  update(new THREE.Vector3(0,1.7,0));
  assert.ok(pool.some(l=>l.intensity>0&&l.position.x===0));
  update(new THREE.Vector3(500,1.7,0));
  assert.ok(pool.every(l=>l.intensity===0||l.position.x>460));
  update(new THREE.Vector3(1000,1.7,0));
  assert.ok(pool.every(l=>l.intensity===0));
  assert.equal(scene.children.length,8,'No light allocations as the camera moves');
});
