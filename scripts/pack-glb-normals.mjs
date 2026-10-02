// Quantize only surface normals for transport. Positions and scene transforms stay exact.
import {readFileSync,writeFileSync} from 'node:fs';
for(const path of process.argv.slice(2)){
 const b=readFileSync(path),n=b.readUInt32LE(12),j=JSON.parse(b.subarray(20,20+n)),bin=b.subarray(28+n);
 const normalIds=new Set(j.meshes.flatMap(m=>m.primitives.map(p=>p.attributes.NORMAL)).filter(x=>x!==undefined));
 const replacements=new Map();
 for(const id of normalIds){const a=j.accessors[id],v=j.bufferViews[a.bufferView];if(a.componentType!==5126)continue;
  if(a.byteOffset||v.byteStride||a.type!=='VEC3')throw Error('Unexpected normal layout');
  const q=Buffer.alloc(a.count*4);for(let i=0;i<a.count;i++)for(let k=0;k<3;k++)q.writeInt8(Math.max(-127,Math.min(127,Math.round(bin.readFloatLE(v.byteOffset+i*12+k*4)*127))),i*4+k);
  replacements.set(a.bufferView,q);a.componentType=5120;a.normalized=true;delete a.min;delete a.max;
 }
 let length=0;const chunks=[];
 for(let i=0;i<j.bufferViews.length;i++){const v=j.bufferViews[i],q=replacements.get(i)??bin.subarray(v.byteOffset,v.byteOffset+v.byteLength);v.byteOffset=length;v.byteLength=q.length;if(replacements.has(i))v.byteStride=4;chunks.push(q);length+=q.length;const pad=(4-length%4)%4;chunks.push(Buffer.alloc(pad));length+=pad;}
 j.buffers[0].byteLength=length;
 for(const key of ['extensionsUsed','extensionsRequired'])j[key]=[...new Set([...(j[key]??[]),'KHR_mesh_quantization'])];
 const text=Buffer.from(JSON.stringify(j)),json=Buffer.concat([text,Buffer.alloc((4-text.length%4)%4,32)]),out=Buffer.alloc(28+json.length+length);
 out.writeUInt32LE(0x46546c67);out.writeUInt32LE(2,4);out.writeUInt32LE(out.length,8);out.writeUInt32LE(json.length,12);out.writeUInt32LE(0x4e4f534a,16);json.copy(out,20);out.writeUInt32LE(length,20+json.length);out.writeUInt32LE(0x004e4942,24+json.length);Buffer.concat(chunks).copy(out,28+json.length);writeFileSync(path,out);console.log(`${b.length} -> ${out.length}`);
}
