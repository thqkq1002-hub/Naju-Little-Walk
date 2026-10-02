// Overview-only uniform position quantization (less than 10 cm over this map).
// Never run on a walkable collision model. Blender source keeps full precision.
import {readFileSync,writeFileSync} from 'node:fs';
import {Matrix4} from 'three';
const path=process.argv[2],b=readFileSync(path),n=b.readUInt32LE(12),j=JSON.parse(b.subarray(20,20+n)),bin=b.subarray(28+n);
if(j.skins?.length||j.animations?.length)throw Error('Static models only');
// Each mesh receives its own position descriptor before per-mesh transforms are applied.
for(const m of j.meshes){const copied=new Map();for(const p of m.primitives){const id=p.attributes.POSITION;if(!copied.has(id)){const a={...j.accessors[id]};const v={...j.bufferViews[a.bufferView]};a.bufferView=j.bufferViews.length;j.bufferViews.push(v);copied.set(id,j.accessors.length);j.accessors.push(a);}p.attributes.POSITION=copied.get(id);}}
const replacements=new Map();let maxError=0;
for(let mi=0;mi<j.meshes.length;mi++){
 const m=j.meshes[mi],ids=[...new Set(m.primitives.map(p=>p.attributes.POSITION))];
 const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
 for(const id of ids){const a=j.accessors[id];if(a.componentType!==5126)throw Error('Expected float positions');for(let k=0;k<3;k++){lo[k]=Math.min(lo[k],a.min[k]);hi[k]=Math.max(hi[k],a.max[k]);}}
 const step=Math.max(...hi.map((x,k)=>x-lo[k]),.001)/65535;maxError=Math.max(maxError,step/2);
 if(step>.2)throw Error('Overview quantization exceeds 10cm per-axis error');
 for(const id of ids){const a=j.accessors[id],v=j.bufferViews[a.bufferView];if(a.byteOffset||v.byteStride||replacements.has(a.bufferView))throw Error('Unsupported shared/interleaved positions');
  const q=Buffer.alloc(a.count*8),min=[65535,65535,65535],max=[0,0,0];
  for(let i=0;i<a.count;i++)for(let k=0;k<3;k++){const value=Math.max(0,Math.min(65535,Math.round((bin.readFloatLE(v.byteOffset+i*12+k*4)-lo[k])/step)));q.writeUInt16LE(value,i*8+k*2);min[k]=Math.min(min[k],value);max[k]=Math.max(max[k],value);}
  a.componentType=5123;a.min=min;a.max=max;replacements.set(a.bufferView,q);v.byteStride=8;
 }
 const adjust=new Matrix4().makeTranslation(...lo).multiply(new Matrix4().makeScale(step,step,step));
 for(const node of j.nodes.filter(node=>node.mesh===mi)){
  if(node.children?.length)throw Error('Mesh parents need separate transforms');
  const mat=new Matrix4();if(node.matrix)mat.fromArray(node.matrix);else{
   const t=node.translation??[0,0,0],r=node.rotation??[0,0,0,1],s=node.scale??[1,1,1];
   // Matrix4.compose accepts vector/quaternion-like objects.
   mat.compose({x:t[0],y:t[1],z:t[2]},{_x:r[0],_y:r[1],_z:r[2],_w:r[3]},{x:s[0],y:s[1],z:s[2]});
  }
  node.matrix=mat.multiply(adjust).toArray();delete node.translation;delete node.rotation;delete node.scale;
 }
}
if(!j.textures?.length)for(const m of j.meshes)for(const p of m.primitives)for(const k of Object.keys(p.attributes))if(k.startsWith('TEXCOORD_'))delete p.attributes[k];
const used=new Set(j.meshes.flatMap(m=>m.primitives.flatMap(p=>[p.indices,...Object.values(p.attributes)].filter(i=>i!==undefined))));
const accessors=[],am=new Map();for(const id of used){am.set(id,accessors.length);accessors.push(j.accessors[id]);}
for(const m of j.meshes)for(const p of m.primitives){if(p.indices!==undefined)p.indices=am.get(p.indices);for(const k in p.attributes)p.attributes[k]=am.get(p.attributes[k]);}j.accessors=accessors;
const vids=new Set(accessors.map(a=>a.bufferView)),views=[],vm=new Map(),chunks=[];let length=0;
for(const id of vids){const v=j.bufferViews[id],data=replacements.get(id)??bin.subarray(v.byteOffset,v.byteOffset+v.byteLength);vm.set(id,views.length);views.push({...v,byteOffset:length,byteLength:data.length});chunks.push(data);length+=data.length;const pad=(4-length%4)%4;chunks.push(Buffer.alloc(pad));length+=pad;}
for(const a of accessors)a.bufferView=vm.get(a.bufferView);j.bufferViews=views;j.buffers[0].byteLength=length;
for(const k of ['extensionsUsed','extensionsRequired'])j[k]=[...new Set([...(j[k]??[]),'KHR_mesh_quantization'])];
const text=Buffer.from(JSON.stringify(j)),json=Buffer.concat([text,Buffer.alloc((4-text.length%4)%4,32)]),out=Buffer.alloc(28+json.length+length);
out.writeUInt32LE(0x46546c67);out.writeUInt32LE(2,4);out.writeUInt32LE(out.length,8);out.writeUInt32LE(json.length,12);out.writeUInt32LE(0x4e4f534a,16);json.copy(out,20);out.writeUInt32LE(length,20+json.length);out.writeUInt32LE(0x004e4942,24+json.length);Buffer.concat(chunks).copy(out,28+json.length);writeFileSync(path,out);console.log({before:b.length,after:out.length,maxPositionErrorMeters:maxError});
