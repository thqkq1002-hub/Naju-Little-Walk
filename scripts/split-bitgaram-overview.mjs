// Split an untextured static GLB into two concurrent transport parts without moving geometry.
import fs from 'node:fs';import {gzipSync} from 'node:zlib';
const path=process.argv[2]??'public/models/bitgaram-overview.glb',raw=fs.readFileSync(path),n=raw.readUInt32LE(12),original=JSON.parse(raw.subarray(20,20+n)),bin=raw.subarray(28+n);
if(original.images?.length||original.skins?.length||original.animations?.length)throw Error('Static overview only');
const sets=[new Set(),new Set()],sizes=[0,0];
original.meshes.map((m,i)=>({i,size:m.primitives.reduce((sum,p)=>sum+Object.values(p.attributes).reduce((s,id)=>s+original.bufferViews[original.accessors[id].bufferView].byteLength,0)+original.bufferViews[original.accessors[p.indices].bufferView].byteLength,0)})).sort((a,b)=>b.size-a.size).forEach(({i,size})=>{const part=sizes[0]<=sizes[1]?0:1;sets[part].add(i);sizes[part]+=size;});
for(let part=0;part<2;part++){
 const g=structuredClone(original),meshMap=new Map();g.meshes=g.meshes.filter((m,i)=>{if(!sets[part].has(i))return false;meshMap.set(i,meshMap.size);return true;});
 for(const node of g.nodes)if(node.mesh!==undefined){if(meshMap.has(node.mesh))node.mesh=meshMap.get(node.mesh);else delete node.mesh;}
 const ids=new Set(g.meshes.flatMap(m=>m.primitives.flatMap(p=>[p.indices,...Object.values(p.attributes)]))),accessors=[],am=new Map(),views=[],vm=new Map(),chunks=[];let length=0;
 for(const id of ids){const a=g.accessors[id];am.set(id,accessors.length);accessors.push(a);if(!vm.has(a.bufferView)){const v=g.bufferViews[a.bufferView];vm.set(a.bufferView,views.length);const bytes=bin.subarray(v.byteOffset,v.byteOffset+v.byteLength);views.push({...v,byteOffset:length});chunks.push(bytes);length+=bytes.length;const pad=(4-length%4)%4;chunks.push(Buffer.alloc(pad));length+=pad;}}
 for(const a of accessors)a.bufferView=vm.get(a.bufferView);
 for(const m of g.meshes)for(const p of m.primitives){p.indices=am.get(p.indices);for(const name in p.attributes)p.attributes[name]=am.get(p.attributes[name]);}
 g.accessors=accessors;g.bufferViews=views;g.buffers=[{byteLength:length}];
 const text=Buffer.from(JSON.stringify(g)),json=Buffer.concat([text,Buffer.alloc((4-text.length%4)%4,32)]),out=Buffer.alloc(28+json.length+length);
 out.writeUInt32LE(0x46546c67);out.writeUInt32LE(2,4);out.writeUInt32LE(out.length,8);out.writeUInt32LE(json.length,12);out.writeUInt32LE(0x4e4f534a,16);json.copy(out,20);out.writeUInt32LE(length,20+json.length);out.writeUInt32LE(0x004e4942,24+json.length);Buffer.concat(chunks).copy(out,28+json.length);
 const name=part===0?path:path.replace('.glb','-part2.glb');fs.writeFileSync(name,out);fs.writeFileSync(name+'.gz',gzipSync(out,{level:9}));console.log(name,out.length);
}
