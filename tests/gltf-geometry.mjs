import fs from 'node:fs';
import * as THREE from 'three';

/** Geometry-only GLB reader for authored surfaces, without browser image/DOM APIs. */
export function readModel(path) {
  const file=fs.readFileSync(path),jsonLength=file.readUInt32LE(12);
  const gltf=JSON.parse(file.toString('utf8',20,20+jsonLength));
  const binary=file.subarray(28+jsonLength);
  const read=(index)=>{
    const a=gltf.accessors[index],v=gltf.bufferViews[a.bufferView];
    const size={SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[a.type];
    const bytes={5121:1,5123:2,5125:4,5126:4}[a.componentType];
    const method={5121:'readUInt8',5123:'readUInt16LE',5125:'readUInt32LE',5126:'readFloatLE'}[a.componentType];
    const out=[];
    for(let i=0;i<a.count;i++)for(let j=0;j<size;j++)out.push(binary[method]((v.byteOffset??0)+(a.byteOffset??0)+i*(v.byteStride??size*bytes)+j*bytes));
    return {array:out,size};
  };
  const material=new THREE.MeshBasicMaterial({side:THREE.FrontSide});
  const nodes=gltf.nodes.map(n=>{
    const group=new THREE.Group();group.name=n.name??'';group.userData={...(n.extras??{})};
    if(n.matrix){group.matrix.fromArray(n.matrix);group.matrix.decompose(group.position,group.quaternion,group.scale);}
    else{if(n.translation)group.position.fromArray(n.translation);if(n.rotation)group.quaternion.fromArray(n.rotation);if(n.scale)group.scale.fromArray(n.scale);}
    if(n.mesh!==undefined)for(const p of gltf.meshes[n.mesh].primitives){
      const pos=read(p.attributes.POSITION),geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(pos.array,pos.size));
      if(p.indices!==undefined)geometry.setIndex(read(p.indices).array);
      group.add(new THREE.Mesh(geometry,material));
    }
    return group;
  });
  gltf.nodes.forEach((n,i)=>(n.children??[]).forEach(j=>nodes[i].add(nodes[j])));
  const scene=new THREE.Group();for(const i of gltf.scenes[gltf.scene??0].nodes)scene.add(nodes[i]);scene.updateMatrixWorld(true);
  return {scene,gltf};
}
