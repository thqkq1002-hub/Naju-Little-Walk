import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=fs.readFileSync(new URL('../public/models/neureoji.glb',import.meta.url));
const doc=JSON.parse(raw.toString('utf8',20,20+raw.readUInt32LE(12)));
test('leaf cutouts and painted distant crowns retain their export material contracts',()=>{
 const leaves=doc.materials.filter(m=>/^(Neureoji93_(crown_|near_leaves)|Neureoji94_(leaf_cutout|bloom_cutout)|Neureoji95_leaf_|Neureoji97_leaf_)/.test(m.name));
 assert.ok(leaves.length>=9);
 for(const m of leaves){assert.equal(m.alphaMode,'MASK',m.name);assert.equal(m.alphaCutoff,.38,m.name);assert.equal(m.doubleSided,true,m.name);}
 for(const m of doc.materials.filter(m=>m.name.startsWith('Neureoji93_crown_')))assert.ok(m.extensions?.KHR_materials_unlit,m.name);
});
test('near woodland contains solid branching crowns instead of only crossed cards',()=>{
 const meshes=doc.meshes.filter(m=>m.name.startsWith('Neureoji97_volume_crowns_'));
 assert.equal(meshes.length,4);
 for(const mesh of meshes)for(const p of mesh.primitives){const a=doc.accessors[p.attributes.POSITION];assert.ok(a.count>100);assert.ok(a.max.every((v,i)=>v>a.min[i]));}
 assert.ok(doc.nodes.some(n=>n.name==='Neureoji97_grounded_trunks'));
});
