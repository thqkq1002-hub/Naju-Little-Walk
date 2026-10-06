// Install the checked Blender revision with existing world navigation preserved.
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import {createHash} from 'node:crypto';
const root=path.resolve(import.meta.dirname,'..'),out=path.join(root,'outputs/quality-v88');
const verification=JSON.parse(fs.readFileSync(path.join(root,'knowledge/sources/arboretum/central-platanus-v88-verification.json')));
for(const key of ['lower_trunk_preserved','transforms_preserved','matched_lod_volume','navigation_unchanged','world_metadata_only','font_labels_verified'])if(!verification[key])throw Error('Preservation gate failed: '+key);
const hash=b=>createHash('sha256').update(b).digest('hex');
if(hash(fs.readFileSync(path.join(root,verification.blend_revision)))!==verification.blend_sha256)throw Error('Saved revision differs from checked source');
let raw=fs.readFileSync(path.join(out,'naju-arboretum-v88.glb')),n=raw.readUInt32LE(12),g=JSON.parse(raw.subarray(20,20+n)),tail=raw.subarray(20+n);
for(const kind of ['plane','mixed']){
 const mat=g.materials.find(m=>m.name===`Canopy_${kind}_MASK_v87`);if(!mat)throw Error('Missing foliage');
 mat.alphaMode='MASK';mat.alphaCutoff=.4;mat.doubleSided=true;
}
const central=g.nodes.filter(a=>a.extras?.canopy_form==='plane-central');if(central.length!==240)throw Error('Central tree pair count differs');
const text=Buffer.from(JSON.stringify(g)),json=Buffer.concat([text,Buffer.alloc((4-text.length%4)%4,32)]);
raw=Buffer.alloc(20+json.length+tail.length);raw.writeUInt32LE(0x46546c67);raw.writeUInt32LE(2,4);raw.writeUInt32LE(raw.length,8);raw.writeUInt32LE(json.length,12);raw.writeUInt32LE(0x4e4f534a,16);json.copy(raw,20);tail.copy(raw,20+json.length);
const model=path.join(root,'public/models/naju-arboretum.glb'),world=path.join(root,'public/naju-arboretum-world.json'),backup=path.join(root,'work/arboretum-before-v88');
if(fs.existsSync(backup))throw Error('Backup exists; inspect before reinstalling');
if(!fs.readFileSync(world).equals(fs.readFileSync(path.join(out,'world-before.json'))))throw Error('World changed since authoring');
fs.mkdirSync(backup);for(const suffix of ['', '.gz'])fs.copyFileSync(model+suffix,path.join(backup,'naju-arboretum.glb'+suffix));fs.copyFileSync(world,path.join(backup,'naju-arboretum-world.json'));
const packed=zlib.gzipSync(raw,{level:9});fs.writeFileSync(model,raw);fs.writeFileSync(model+'.gz',packed);fs.copyFileSync(path.join(out,'world-after.json'),world);
const metrics={central_tree_pairs:120,shared_central_prototypes:6,glb_bytes:raw.length,gzip_bytes:packed.length,model_sha256:hash(raw),gzip_sha256:hash(packed),world_sha256:hash(fs.readFileSync(world)),navigation_unchanged:true};
fs.writeFileSync(path.join(root,'knowledge/sources/arboretum/central-platanus-v88-metrics.json'),JSON.stringify(metrics,null,2));console.log(metrics);
