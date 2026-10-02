import fs from 'node:fs';
import {gzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
const beforePath=process.argv[4]??'public/models/naju-arboretum.glb',old=fs.readFileSync(beforePath),oldGz=fs.readFileSync(beforePath+'.gz');
const path=process.argv[2]??'outputs/quality-v61/naju-arboretum-v61-soft.glb',raw=fs.readFileSync(path),gz=gzipSync(raw,{level:9});
fs.writeFileSync(path+'.gz',gz);
const metrics=b=>{const g=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)));return {nodes:g.nodes.length,meshes:g.meshes.length,shared_mesh_triangles:g.meshes.reduce((n,m)=>n+m.primitives.reduce((n,p)=>n+(p.indices===undefined?g.accessors[p.attributes.POSITION].count:g.accessors[p.indices].count)/3,0),0),embedded_images:g.images.length};};
const report={before:{bytes:old.length,gzip_bytes:oldGz.length,...metrics(old)},after:{bytes:raw.length,gzip_bytes:gz.length,...metrics(raw)},sha256:createHash('sha256').update(raw).digest('hex'),transport:'Only normals use normalized int8; positions and UV stay exact'};
fs.writeFileSync(process.argv[3]??'knowledge/sources/arboretum/garden-quality-v61-transport.json',JSON.stringify(report,null,2)+'\n');console.log(report);
