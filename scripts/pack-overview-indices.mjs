// Lossless triangle partitioning for 16-bit indices; authored coordinates stay unchanged.
import fs from 'node:fs';
const path=process.argv[2],raw=fs.readFileSync(path),n=raw.readUInt32LE(12),g=JSON.parse(raw.subarray(20,20+n)),binary=raw.subarray(28+n);
if(g.images?.length||g.skins?.length||g.animations?.length)throw Error('Untextured static overview only');
const accessors=[],views=[],buffers=[];let length=0,triangles=0;
const size={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4},components={SCALAR:1,VEC2:2,VEC3:3,VEC4:4};
function append(bytes,view){const id=views.length;views.push({...view,buffer:0,byteOffset:length,byteLength:bytes.length});buffers.push(bytes);length+=bytes.length;let pad=(4-length%4)%4;buffers.push(Buffer.alloc(pad));length+=pad;return id;}
function attribute(id,order){
 const a=g.accessors[id],v=g.bufferViews[a.bufferView],stride=v.byteStride??size[a.componentType]*components[a.type];
 if(a.sparse)throw Error('Sparse accessor unsupported');
 const output=Buffer.alloc(order.length*stride),start=(v.byteOffset??0)+(a.byteOffset??0);
 order.forEach((index,j)=>binary.copy(output,j*stride,start+index*stride,start+(index+1)*stride));
 const next={...a,count:order.length,bufferView:append(output,v)};delete next.byteOffset;
 // Original bounds conservatively contain each partition, so no geometry is culled.
 accessors.push(next);return accessors.length-1;
}
for(const mesh of g.meshes){
 const primitives=[];
 for(const p of mesh.primitives){
  if((p.mode??4)!==4||p.indices===undefined)throw Error('Indexed triangles only');
  const a=g.accessors[p.indices],v=g.bufferViews[a.bufferView],bytes=size[a.componentType],start=(v.byteOffset??0)+(a.byteOffset??0);
  const read=i=>bytes===4?binary.readUInt32LE(start+i*bytes):bytes===2?binary.readUInt16LE(start+i*bytes):binary.readUInt8(start+i);
  let map=new Map(),order=[],indices=[];
  function flush(){
   if(!indices.length)return;
   const attributes={};for(const [name,id] of Object.entries(p.attributes))attributes[name]=attribute(id,order);
   const data=Buffer.alloc(indices.length*2);indices.forEach((index,j)=>data.writeUInt16LE(index,j*2));
   const id=accessors.length;accessors.push({bufferView:append(data,{target:34963}),componentType:5123,count:indices.length,type:'SCALAR',min:[0],max:[order.length-1]});
   primitives.push({...p,attributes,indices:id});map=new Map();order=[];indices=[];
  }
  for(let i=0;i<a.count;i+=3){
   const face=[read(i),read(i+1),read(i+2)];if(map.size+face.filter(x=>!map.has(x)).length>65535)flush();
   for(const index of face){if(!map.has(index)){map.set(index,order.length);order.push(index);}indices.push(map.get(index));}
   triangles++;
  }
  flush();
 }
 mesh.primitives=primitives;
}
g.accessors=accessors;g.bufferViews=views;g.buffers=[{byteLength:length}];
const text=Buffer.from(JSON.stringify(g)),json=Buffer.concat([text,Buffer.alloc((4-text.length%4)%4,32)]),out=Buffer.alloc(28+json.length+length);
out.writeUInt32LE(0x46546c67);out.writeUInt32LE(2,4);out.writeUInt32LE(out.length,8);out.writeUInt32LE(json.length,12);out.writeUInt32LE(0x4e4f534a,16);json.copy(out,20);out.writeUInt32LE(length,20+json.length);out.writeUInt32LE(0x004e4942,24+json.length);Buffer.concat(buffers).copy(out,28+json.length);
fs.writeFileSync(path,out);console.log({before:raw.length,after:out.length,triangles});
