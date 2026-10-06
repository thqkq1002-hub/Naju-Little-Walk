// Install only the independently checked, reviewed Blender export.
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { createHash } from 'node:crypto';
const root=path.resolve(import.meta.dirname,'..');
const file=path.join(root,'outputs/quality-v87/naju-arboretum-v87-r4.glb');
const verification=JSON.parse(fs.readFileSync(path.join(root,'knowledge/sources/arboretum/canopy-v87-verification.json')));
if(!verification.world_unchanged||!verification.wood_preserved||!verification.transforms_preserved||!verification.matched_lod_volume||!verification.groundcover_path_clearance)throw Error('Preservation gate failed');
if(!verification.blend_revision?.endsWith('canopy-v87-r4.blend')||createHash('sha256').update(fs.readFileSync(path.join(root,verification.blend_revision))).digest('hex')!==verification.blend_sha256)throw Error('Saved Blender revision differs from verified file');
let raw=fs.readFileSync(file),n=raw.readUInt32LE(12),g=JSON.parse(raw.subarray(20,20+n)),tail=raw.subarray(20+n);
for(const kind of ['meta','plane','mixed']){
 const material=g.materials.find(m=>m.name===`Canopy_${kind}_MASK_v87`);if(!material)throw Error('Missing authored foliage');
 material.alphaMode='MASK';material.alphaCutoff=.4;material.doubleSided=true;
}
const text=Buffer.from(JSON.stringify(g)),json=Buffer.concat([text,Buffer.alloc((4-text.length%4)%4,32)]);
raw=Buffer.alloc(20+json.length+tail.length);raw.writeUInt32LE(0x46546c67);raw.writeUInt32LE(2,4);raw.writeUInt32LE(raw.length,8);raw.writeUInt32LE(json.length,12);raw.writeUInt32LE(0x4e4f534a,16);json.copy(raw,20);tail.copy(raw,20+json.length);
const publicFile=path.join(root,'public/models/naju-arboretum.glb'),backup=path.join(root,'work/arboretum-before-v87-r4');
if(fs.existsSync(backup))throw Error('Backup already exists; inspect instead of reinstalling');
fs.mkdirSync(backup);for(const suffix of ['', '.gz'])fs.copyFileSync(publicFile+suffix,path.join(backup,'naju-arboretum.glb'+suffix));
const originalBackup=path.join(root,'work/arboretum-before-v87/naju-arboretum.glb');
const baseline=fs.existsSync(originalBackup)?originalBackup:publicFile;
const beforeRaw=fs.readFileSync(baseline),old=JSON.parse(beforeRaw.subarray(20,20+beforeRaw.readUInt32LE(12)));
const triangles=d=>d.meshes.reduce((s,m)=>s+m.primitives.reduce((v,p)=>v+d.accessors[p.indices??p.attributes.POSITION].count/3,0),0);
const treeBudget=(d,lod)=>d.nodes.filter(n=>n.extras?.vegetation_lod===lod&&['meta','broad','broad2'].includes(n.extras?.reference_habit)).reduce((sum,n)=>sum+d.meshes[n.mesh].primitives.reduce((v,p)=>v+d.accessors[p.indices??p.attributes.POSITION].count/3,0),0);
const packed=zlib.gzipSync(raw,{level:9});
const metrics={before:{glb_bytes:beforeRaw.length,gzip_bytes:fs.statSync(baseline+'.gz').size,shared_geometry_triangles:triangles(old)},after:{glb_bytes:raw.length,gzip_bytes:packed.length,shared_geometry_triangles:triangles(g),mesh_count:g.meshes.length,image_count:g.images.length},tree_pairs:verification.tree_pairs,groundcover_pairs:verification.groundcover_pairs,shared_tree_prototypes:verification.shared_prototypes,world_unchanged:true};
for(const [label,d] of [['before',old],['after',g]])metrics[label].trees_if_all_near_or_far={near:treeBudget(d,'near'),far:treeBudget(d,'far')};
fs.writeFileSync(file,raw);fs.writeFileSync(publicFile,raw);fs.writeFileSync(publicFile+'.gz',packed);
fs.writeFileSync(path.join(root,'knowledge/sources/arboretum/canopy-v87-metrics.json'),JSON.stringify(metrics,null,2));console.log(metrics);
