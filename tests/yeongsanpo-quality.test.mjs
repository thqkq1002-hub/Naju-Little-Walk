import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {appDestinationFromSearch} from '../lib/app-destination.ts';
const read=name=>JSON.parse(fs.readFileSync(new URL('../'+name,import.meta.url),'utf8'));
const model=id=>{
  const raw=fs.readFileSync(new URL('../public/models/'+id+'.glb',import.meta.url));
  return {raw,gltf:JSON.parse(raw.toString('utf8',20,20+raw.readUInt32LE(12)))};
};
test('all refined scenes and moving boats have standalone compressed PBR models',()=>{
  const budgets={yeongsanpo:1700,'yeongsanpo-history':450,'yeongsanpo-literature':400,najuho:100,wanggeonho:100};
  for(const [id,budget] of Object.entries(budgets)){
    const {raw,gltf}=model(id),packed=fs.readFileSync(new URL('../public/models/'+id+'.glb.gz',import.meta.url));
    assert.deepEqual(gunzipSync(packed),raw,id+' compressed transport');
    assert.ok(packed.length<25*1024*1024,id+' download limit');
    assert.ok(gltf.meshes.length<budget,id+' material grouping');
    assert.ok(gltf.images.length>=10&&gltf.images.every(i=>i.bufferView!==undefined&&!i.uri));
    assert.ok(gltf.materials.filter(m=>m.normalTexture).length>=5,id+' authored surface normals');
    assert.equal(gltf.buffers.length,1);assert.ok(!gltf.buffers[0].uri);
  }
});
test('river has physically shaded ripples and leaves use clipped silhouettes',()=>{
  const {gltf}=model('yeongsanpo');
  const water=gltf.materials.find(m=>m.name.startsWith('Y79_water_'));
  assert.ok(water.normalTexture&&water.pbrMetallicRoughness.metallicRoughnessTexture);
  const leaf=gltf.materials.find(m=>m.name==='Y79_leaf_cutout');
  assert.equal(leaf.alphaMode,'MASK');assert.equal(leaf.doubleSided,true);
  assert.ok(gltf.nodes.some(n=>n.name==='yeongsanpo_lighthouse'));
});
test('scene refinements retain navigation baselines and record the deliberate northern crop',()=>{
  const refs=read('knowledge/sources/yeongsanpo-v79-verification.json');
  const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
  for(const id of ['yeongsanpo','yeongsanpo-history','yeongsanpo-literature']){
    const w=read('public/'+id+'-world.json');
    assert.equal(w.detailVersion,'yeongsanpo-v79-20261003');
    const reference=refs.navigation.find(n=>n.scene===id);
    assert.ok(reference?.unchanged);
    const nav=Object.fromEntries(reference.navigationKeys.map(k=>[k,w[k]??null]));
    const crop=id==='yeongsanpo'&&w.mapCrop?.revision==='north-crop-v90'?read('knowledge/sources/yeongsanpo-crop-v90.json'):id==='yeongsanpo-history'&&w.galleryRevision?.startsWith('history-complete-v91')?read('knowledge/sources/history-gallery-v91.json'):null;
    if(crop)assert.equal(crop.legacyNavigationSha256,reference.navigationSha256,'Crop starts from the preserved navigation baseline');
    assert.equal(createHash('sha256').update(JSON.stringify(canonical(nav))).digest('hex'),crop?.navigationSha256??reference.navigationSha256,id+' floor, wall and doorway envelopes');
    assert.equal(appDestinationFromSearch('?place='+id),id);
    for(const p of w.portals??[])assert.equal(appDestinationFromSearch('?place='+p.target),p.target);
  }
  const w=read('public/yeongsanpo-world.json');
  assert.equal(w.architectureViews.length,4);
  assert.equal(w.boats.length,2);
  for(const b of w.boats)assert.match(b.modelUrl,/quality-v79/);
});
