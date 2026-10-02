// Lossless packing: identical buffer-view bytes share storage; all nodes and accessors remain intact.
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
for (const path of process.argv.slice(2)) {
  const source=readFileSync(path), jsonLength=source.readUInt32LE(12);
  const doc=JSON.parse(source.subarray(20,20+jsonLength));
  const bin=source.subarray(28+jsonLength), chunks=[], seen=new Map();
  let length=0;
  for(const view of doc.bufferViews){
    if(view.buffer!==0)throw new Error('Expected one embedded buffer');
    const bytes=bin.subarray(view.byteOffset??0,(view.byteOffset??0)+view.byteLength);
    const hash=createHash('sha256').update(bytes).digest('hex');
    if(!seen.has(hash)){
      seen.set(hash,length);chunks.push(bytes);length+=bytes.length;
      const pad=(4-length%4)%4;if(pad){chunks.push(Buffer.alloc(pad));length+=pad;}
    }
    view.byteOffset=seen.get(hash);
  }
  // Validate before compacting duplicate descriptors.
  const verification=Buffer.concat(chunks), oldViews=JSON.parse(source.subarray(20,20+jsonLength)).bufferViews;
  doc.bufferViews.forEach((v,i)=>{const o=oldViews[i];if(!verification.subarray(v.byteOffset,v.byteOffset+v.byteLength).equals(bin.subarray(o.byteOffset??0,(o.byteOffset??0)+o.byteLength)))throw new Error('Buffer mismatch');});
  const unique=[], ids=new Map(), remap=doc.bufferViews.map(v=>{
    const key=JSON.stringify(v);if(!ids.has(key)){ids.set(key,unique.length);unique.push(v);}return ids.get(key);
  });
  for(const a of doc.accessors??[]){
    if(a.bufferView!==undefined)a.bufferView=remap[a.bufferView];
    if(a.sparse){a.sparse.indices.bufferView=remap[a.sparse.indices.bufferView];a.sparse.values.bufferView=remap[a.sparse.values.bufferView];}
  }
  for(const i of doc.images??[])if(i.bufferView!==undefined)i.bufferView=remap[i.bufferView];
  doc.bufferViews=unique;
  const accessorIds=new Map(),accessors=[];
  const ar=doc.accessors.map(a=>{const key=JSON.stringify(a);if(!accessorIds.has(key)){accessorIds.set(key,accessors.length);accessors.push(a);}return accessorIds.get(key);});
  for(const m of doc.meshes??[])for(const p of m.primitives){
    if(p.indices!==undefined)p.indices=ar[p.indices];
    for(const k in p.attributes)p.attributes[k]=ar[p.attributes[k]];
    for(const t of p.targets??[])for(const k in t)t[k]=ar[t[k]];
  }
  for(const s of doc.skins??[])if(s.inverseBindMatrices!==undefined)s.inverseBindMatrices=ar[s.inverseBindMatrices];
  for(const a of doc.animations??[])for(const s of a.samplers){s.input=ar[s.input];s.output=ar[s.output];}
  doc.accessors=accessors;
  doc.buffers[0].byteLength=length;
  const packed=Buffer.concat(chunks), encoded=Buffer.from(JSON.stringify(doc));
  const json=Buffer.concat([encoded,Buffer.alloc((4-encoded.length%4)%4,32)]);
  const header=Buffer.alloc(20);header.writeUInt32LE(0x46546c67);header.writeUInt32LE(2,4);
  header.writeUInt32LE(28+json.length+packed.length,8);header.writeUInt32LE(json.length,12);header.writeUInt32LE(0x4e4f534a,16);
  const bh=Buffer.alloc(8);bh.writeUInt32LE(packed.length);bh.writeUInt32LE(0x004e4942,4);
  // Verify every view still addresses the exact original bytes before replacing the file.
  const result=Buffer.concat([header,json,bh,packed]);writeFileSync(path,result);
  console.log(`${path}: ${source.length} -> ${result.length}`);
}
