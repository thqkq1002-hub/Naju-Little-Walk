import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {NpcAnimation} from '../lib/npc-animation.ts';

// Decode shipped skin/animation buffers without browser-only texture decoding.
const manifest=JSON.parse(fs.readFileSync(new URL('../public/npc-placements.json',import.meta.url),'utf8'));
async function geometryOnly(character){
  const raw=fs.readFileSync(new URL('../public'+manifest.assets[character].modelUrl,import.meta.url));
  const length=raw.readUInt32LE(12),gltf=JSON.parse(raw.subarray(20,20+length).toString());
  const binStart=20+length,bin=raw.subarray(binStart+8,binStart+8+raw.readUInt32LE(binStart));
  delete gltf.images;delete gltf.textures;delete gltf.materials;delete gltf.samplers;
  gltf.extensionsRequired=(gltf.extensionsRequired??[]).filter(x=>x!=='EXT_texture_webp');
  gltf.extensionsUsed=(gltf.extensionsUsed??[]).filter(x=>x!=='EXT_texture_webp');
  for(const mesh of gltf.meshes)for(const primitive of mesh.primitives)delete primitive.material;
  const json=Buffer.from(JSON.stringify(gltf)),size=Math.ceil(json.length/4)*4;
  const output=Buffer.alloc(28+size+bin.length);output.write('glTF');output.writeUInt32LE(2,4);output.writeUInt32LE(output.length,8);
  output.writeUInt32LE(size,12);output.writeUInt32LE(0x4e4f534a,16);output.fill(32,20,20+size);json.copy(output,20);
  output.writeUInt32LE(bin.length,20+size);output.writeUInt32LE(0x004e4942,24+size);bin.copy(output,28+size);
  return new GLTFLoader().parseAsync(output.buffer.slice(output.byteOffset,output.byteOffset+output.byteLength),'');
}
for(const character of ['baedoli','beodeuri','hongdoli','teacher']){
  test(`${character}: greeting and nod do not tear adjacent surface vertices`,async()=>{
    const gltf=await geometryOnly(character),controller=new NpcAnimation(gltf.scene,gltf.animations);
    let skin;gltf.scene.traverse(o=>{if(o.isSkinnedMesh)skin=o;});
    const position=skin.geometry.attributes.position,index=skin.geometry.index;
    const edges=[];
    for(let i=0;i<index.count;i+=3){
      const a=index.getX(i),b=index.getX(i+1),c=index.getX(i+2);
      for(const [u,v] of [[a,b],[b,c],[c,a]]){
        const length=new THREE.Vector3().fromBufferAttribute(position,u).distanceTo(new THREE.Vector3().fromBufferAttribute(position,v));
        if(length>.0001&&length<.025)edges.push([u,v,length]);
      }
    }
    for(const name of ['Greeting','Explain','Nod']){
      controller.setGesture(name);
      for(let sample=0;sample<4;sample++){
        for(let frame=0;frame<12;frame++)controller.update(.06);
        gltf.scene.updateMatrixWorld(true);skin.skeleton.update();
        const posed=Array.from({length:position.count},(_,i)=>skin.getVertexPosition(i,new THREE.Vector3()));
        let worst=0,offending=[];
        for(const [u,v,length] of edges){const growth=posed[u].distanceTo(posed[v])-length;if(growth>worst){worst=growth;offending=[u,v];}}
        assert.ok(worst<.03,`${name} stretches a short surface edge by ${(worst*100).toFixed(1)}cm at ${offending.map(i=>new THREE.Vector3().fromBufferAttribute(position,i).toArray().map(n=>n.toFixed(3)).join(',')).join(' → ')}`);
      }
    }
    controller.dispose();skin.geometry.dispose();
  });
}
for(const character of ['baedoli','beodeuri','hongdoli','teacher']){
  test(`${character}: shipped skin moves gestures while feet remain grounded`,async()=>{
    const gltf=await geometryOnly(character),controller=new NpcAnimation(gltf.scene,gltf.animations);
    let skin;gltf.scene.traverse(o=>{if(o.isSkinnedMesh)skin=o;});assert.ok(skin);
    const p=skin.geometry.attributes.position,feet=[];
    for(let i=0;i<p.count;i++)if(p.getY(i)<.065)feet.push(i);
    assert.ok(feet.length>10,'Foot geometry exists');
    const samples=feet.filter((_,i)=>i%Math.max(1,Math.floor(feet.length/50))===0);
    const update=()=>{gltf.scene.updateMatrixWorld(true);skin.skeleton.update();};
    update();const baseline=samples.map(i=>skin.getVertexPosition(i,new THREE.Vector3()).clone());
    controller.setGesture('Greeting');for(let i=0;i<25;i++)controller.update(.06);update();
    for(let i=0;i<samples.length;i++){
      const vertex=skin.getVertexPosition(samples[i],new THREE.Vector3());
      assert.ok(vertex.distanceTo(baseline[i])<.003,'No sliding feet');
      assert.ok(vertex.y>=-.001,'No sinking below floor');
    }
    assert.ok(skin.skeleton.bones.some(b=>Math.abs(b.quaternion.x)+Math.abs(b.quaternion.y)+Math.abs(b.quaternion.z)>.02),'Skeleton actually changes pose');
    for(let i=0;i<p.count;i+=Math.max(1,Math.floor(p.count/100))){const v=skin.getVertexPosition(i,new THREE.Vector3());assert.ok([v.x,v.y,v.z].every(Number.isFinite));}
    controller.dispose();skin.geometry.dispose();
  });
}
