import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
const world=JSON.parse(fs.readFileSync(new URL('../public/city-world.json',import.meta.url),'utf8'));
const metrics=JSON.parse(fs.readFileSync(new URL('../knowledge/sources/geumseonggwan-v77/metrics.json',import.meta.url),'utf8'));

test('architectural close views keep a finite target above ground and have unique controls',()=>{
  assert.deepEqual(world.architectureViews.map(v=>v.id),['hall-front','eaves','manghwaru','ceiling']);
  for(const v of world.architectureViews){
    assert.ok([...v.center,v.radius,v.angle,v.elevation].every(Number.isFinite));
    assert.ok(v.center[1]>0&&v.radius>=5&&v.radius<=60);
  }
  assert.ok(world.architectureViews.find(v=>v.id==='eaves').elevation<.1,'Eave view must see the brackets from below');
  const ceiling=world.architectureViews.find(v=>v.id==='ceiling');
  const eyeY=ceiling.center[1]+Math.sin(ceiling.elevation)*ceiling.radius;
  assert.ok(eyeY>1.5&&eyeY<4,'Ceiling view must look up from inside the hall');
  assert.equal(crypto.createHash('sha256').update(JSON.stringify(world.solids)).digest('hex'),metrics.collisionSHA256,'Detailing must preserve the verified wall, doorway and floor envelopes');
});

test('published model contains the curved brackets and fine fittings without exceeding hosting budget',()=>{
  const packed=fs.readFileSync(new URL('../public/models/geumseonggwan.glb.gz',import.meta.url));
  assert.ok(packed.length<25*1024*1024);
  const bytes=zlib.gunzipSync(packed);
  assert.deepEqual(bytes,fs.readFileSync(new URL('../public/models/geumseonggwan.glb',import.meta.url)));
  const gltf=JSON.parse(bytes.toString('utf8',20,20+bytes.readUInt32LE(12)));
  for(const name of ['v78_ikgong_leaf_arms','v78_ikgong_leaf_outlines','v78_painted_beam_faces','v77_door_iron_fittings','v77_hip_roof_barrel_courses']){
    const node=gltf.nodes.find(n=>n.name===name);assert.ok(node,name);
    const mesh=gltf.meshes[node.mesh];assert.ok(mesh.primitives.length>0);
    for(const p of mesh.primitives){
      const a=gltf.accessors[p.attributes.POSITION];assert.ok(a.count>10);
      assert.ok([...a.min,...a.max].every(Number.isFinite),name);
      assert.ok(a.max[1]>a.min[1],`${name} must have real height`);
    }
  }
  assert.ok(gltf.meshes.length<800,'Keep detail grouped for browser traversal');
  assert.equal(gltf.nodes.some(n=>/^(hall_ikgong_|manghwaru_ikgong_)/.test(n.name)),false,'Old block brackets must be replaced in the new copy');
  assert.ok(gltf.nodes.some(n=>n.name==='v78_painted_lotus_coffers'));
  assert.equal(gltf.nodes.some(n=>n.name==='ceiling_original_lotus'),false,'Superseded relief flowers must be removed from the new copy');
  assert.equal(gltf.nodes.some(n=>n.name==='hall_coffer_frame'),false,'The old rails through the flower centers must be replaced');
  assert.ok(gltf.nodes.some(n=>n.name==='v78_coffer_edge_frames'));
  for(const name of ['Geum_v78_painted_rafter_body','Geum_v78_painted_rafter_end','Geum_v78_lotus_coffer']){
    const material=gltf.materials.find(m=>m.name===name);assert.ok(material,name);
    assert.ok(material.pbrMetallicRoughness.baseColorTexture,`${name} must export its original painted map`);
    assert.deepEqual(material.pbrMetallicRoughness.baseColorFactor??[1,1,1,1],[1,1,1,1],'Painted maps must not get darkened by a second tint');
  }
});
