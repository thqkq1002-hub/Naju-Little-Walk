import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gzipSync} from 'node:zlib';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {fetchModelData,unpackModel} from '../lib/model-transport.ts';

const model=fs.readFileSync(new URL('../public/models/bitgaram-kentech.glb',import.meta.url));
const packed=fs.readFileSync(new URL('../public/models/bitgaram-kentech.glb.gz',import.meta.url));
const buffer=bytes=>bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);
const response=()=>new Response(packed,{headers:{'content-length':String(packed.length)}});

test('KENTECH downloads, decompresses and parses through the browser GLTF loader',async()=>{
  const progress=[];
  const data=await fetchModelData('/models/bitgaram-kentech.glb.gz',{fetcher:async()=>response(),onProgress:p=>progress.push(p)});
  assert.deepEqual(Buffer.from(data),model);
  const gltf=await new GLTFLoader().parseAsync(data,'');
  let meshes=0;gltf.scene.traverse(o=>{if(o.isMesh){meshes++;assert.ok(o.geometry.attributes.position.count>0);}});
  assert.equal(meshes,112);
  assert.ok(progress.some(p=>p.phase==='download'&&p.received===packed.length&&p.total===packed.length));
  assert.equal(progress.at(-1).phase,'unpack');
});

test('a stalled request is aborted and retried once with a fresh cache policy',async()=>{
  const calls=[],progress=[];
  const data=await fetchModelData('/campus.glb.gz',{
    idleTimeoutMs:30,onProgress:p=>progress.push(p),
    fetcher:async(url,options)=>{
      calls.push(options);
      if(calls.length===1)return new Promise(()=>{});
      return response();
    },
  });
  assert.deepEqual(Buffer.from(data),model);
  assert.equal(calls.length,2);
  assert.equal(calls[0].signal.aborted,true);
  assert.deepEqual(calls.map(c=>c.cache),['default','reload']);
  assert.ok(progress.some(p=>p.phase==='retry'));
});

test('a response with a stalled body also cancels and retries',async()=>{
  let calls=0,cancelled=false;
  const data=await fetchModelData('/campus.glb.gz',{idleTimeoutMs:30,fetcher:async()=>{
    if(++calls===1)return new Response(new ReadableStream({cancel(){cancelled=true;}}));
    return response();
  }});
  assert.deepEqual(Buffer.from(data),model);
  assert.equal(cancelled,true);assert.equal(calls,2);
});

test('leaving or manually restarting the scene cancels without a second request',async()=>{
  const controller=new AbortController();let calls=0,cancelled=false;
  const loading=fetchModelData('/campus.glb.gz',{signal:controller.signal,fetcher:async()=>{
    calls++;
    return new Response(new ReadableStream({start(){setTimeout(()=>controller.abort(),10);},cancel(){cancelled=true;}}));
  }});
  await assert.rejects(loading,{name:'AbortError'});
  assert.equal(calls,1);assert.equal(cancelled,true);
});

test('a slow but advancing download resets the idle timeout',async()=>{
  // Tiny valid GLB keeps this timing test independent of model decoding cost.
  const bytes=new Uint8Array(12);const header=new DataView(bytes.buffer);
  header.setUint32(0,0x46546c67,true);header.setUint32(4,2,true);header.setUint32(8,12,true);
  let calls=0;
  const data=await fetchModelData('/slow.glb',{idleTimeoutMs:100,fetcher:async()=>{
    calls++;
    return new Response(new ReadableStream({async start(controller){
      for(let i=0;i<3;i++){await new Promise(resolve=>setTimeout(resolve,50));controller.enqueue(bytes.slice(i*4,i*4+4));}
      controller.close();
    }}));
  }});
  assert.deepEqual(new Uint8Array(data),bytes);assert.equal(calls,1);
});

test('truncated cached model bytes are rejected and reloaded',async()=>{
  let calls=0;
  const data=await fetchModelData('/campus.glb.gz',{fetcher:async()=>++calls===1?new Response(gzipSync(model.subarray(0,100))):response()});
  assert.deepEqual(Buffer.from(data),model);assert.equal(calls,2);
  await assert.rejects(unpackModel(buffer(model.subarray(0,100))),/불완전/);
});

test('a persistent failure exits the loading state instead of retrying forever',async()=>{
  let calls=0;
  await assert.rejects(fetchModelData('/campus.glb.gz',{fetcher:async()=>{calls++;return new Response('',{status:503});}}),/503/);
  assert.equal(calls,2);
});

test('HTTP-decompressed responses do not present an inaccurate Content-Length percentage',async()=>{
  const progress=[];
  const data=await fetchModelData('/campus.glb.gz',{fetcher:async()=>new Response(model,{headers:{'content-encoding':'gzip','content-length':String(packed.length)}}),onProgress:p=>progress.push(p)});
  assert.deepEqual(Buffer.from(data),model);
  assert.ok(progress.filter(p=>p.phase==='download').every(p=>p.total===undefined));
});
