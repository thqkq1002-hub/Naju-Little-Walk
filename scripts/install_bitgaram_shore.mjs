// Install only after independent saved-model verification and visual review.
import fs from 'node:fs';import path from 'node:path';import zlib from 'node:zlib';
const root=path.resolve(import.meta.dirname,'..');
const verification=JSON.parse(fs.readFileSync(path.join(root,'knowledge/sources/bitgaram/shore-v75-verification.json')));
if(!verification.world_unchanged||!verification.unchanged_geometry_and_transforms||!verification.saved_surface_matches_prepared_geometry)throw Error('Preservation gate failed');
const file=path.join(root,'outputs/quality-v75/bitgaram-park-v75.glb'),raw=fs.readFileSync(file),j=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
const bank=j.nodes.find(n=>n.name==='mapped_park_lawn_shore_v75');if(!bank||!bank.extras.visual_context_only)throw Error('New background lawn missing');
const normals=j.meshes.flatMap(m=>m.primitives.map(p=>p.attributes.NORMAL)).filter(n=>n!==undefined);if(normals.some(n=>j.accessors[n].componentType!==5120))throw Error('Normals have not been packed');
const pub=path.join(root,'public/models/bitgaram-park.glb'),backup=path.join(root,'work/park-before-v75');
if(fs.existsSync(backup))throw Error('Existing backup preserved; inspect instead of reinstalling');
fs.mkdirSync(backup);for(const s of ['','.gz'])fs.copyFileSync(pub+s,path.join(backup,'bitgaram-park.glb'+s));
const oldRaw=fs.readFileSync(pub),old=JSON.parse(oldRaw.subarray(20,20+oldRaw.readUInt32LE(12))),gz=zlib.gzipSync(raw,{level:9});
if(!zlib.gunzipSync(gz).equals(raw))throw Error('Gzip mismatch');
const triangles=d=>d.meshes.reduce((sum,m)=>sum+m.primitives.reduce((s,p)=>s+d.accessors[p.indices??p.attributes.POSITION].count/3,0),0);
const metrics={before:{glb_bytes:oldRaw.length,gzip_bytes:fs.statSync(pub+'.gz').size,shared_geometry_triangles:triangles(old),mesh_count:old.meshes.length},after:{glb_bytes:raw.length,gzip_bytes:gz.length,shared_geometry_triangles:triangles(j),mesh_count:j.meshes.length,image_count:j.images.length},protected_meshes:verification.protected_meshes,water_meshes_unchanged:verification.protected_water_meshes,world_unchanged:true,visual_context_only:true,gzip_exact:true};
fs.writeFileSync(pub,raw);fs.writeFileSync(pub+'.gz',gz);fs.writeFileSync(path.join(root,'knowledge/sources/bitgaram/shore-v75-metrics.json'),JSON.stringify(metrics,null,2));console.log(metrics);
