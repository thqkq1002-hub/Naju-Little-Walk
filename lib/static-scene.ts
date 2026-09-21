import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

/** Keep Blender's repeated plant geometry shared, with local bounds for culling. */
export function instanceAuthoredVegetation(root: THREE.Object3D): number {
  root.updateMatrixWorld(true);
  const inverseRoot=new THREE.Matrix4().copy(root.matrixWorld).invert();
  const groups=new Map<string,{mesh:THREE.Mesh;matrix:THREE.Matrix4;lod:string;cell:number;radius:number}[]>();
  root.traverse(object=>{
    if (!(object instanceof THREE.Mesh) || object instanceof THREE.InstancedMesh || object instanceof THREE.SkinnedMesh || Array.isArray(object.material) || object.material.transparent || object.morphTargetInfluences?.length) return;
    let tagged=false,lod='',radius=80;
    for(let p:THREE.Object3D|null=object;p;p=p.parent){
      if(!p.visible)return;
      tagged ||= p.userData.authored_vegetation===true;
      if(p.userData.vegetation_lod){lod=p.userData.vegetation_lod;radius=p.userData.vegetation_distance??80;}
      if(p===root)break;
    }
    if(!tagged)return;
    const matrix=new THREE.Matrix4().multiplyMatrices(inverseRoot,object.matrixWorld);
    if(matrix.determinant()<=0)return;
    const position=new THREE.Vector3().setFromMatrixPosition(matrix);
    const cell=lod?(radius>40?48:24):96;
    const key=`${object.geometry.uuid}:${object.material.uuid}:${object.castShadow}:${object.receiveShadow}:${lod}:${Math.floor(position.x/cell)}:${Math.floor(position.z/cell)}`;
    const group=groups.get(key)??[];group.push({mesh:object,matrix,lod,cell,radius});groups.set(key,group);
  });
  let removed=0;
  for(const group of groups.values()){
    if(group.length<2&&!group[0].lod)continue;
    const first=group[0].mesh;
    const batch=new THREE.InstancedMesh(first.geometry,first.material,group.length);
    batch.name='authored_vegetation_instances';batch.castShadow=first.castShadow;batch.receiveShadow=first.receiveShadow;
    if(group[0].lod){
      const {matrix,lod,cell,radius}=group[0],p=new THREE.Vector3().setFromMatrixPosition(matrix);
      batch.userData.vegetation_lod=lod;batch.userData.vegetation_distance=radius;
      batch.userData.vegetation_center=new THREE.Vector3((Math.floor(p.x/cell)+.5)*cell,0,(Math.floor(p.z/cell)+.5)*cell);
      batch.visible=lod==='far';
    }
    group.forEach(({mesh,matrix},index)=>{batch.setMatrixAt(index,matrix);mesh.removeFromParent();});
    batch.instanceMatrix.needsUpdate=true;batch.computeBoundingBox();batch.computeBoundingSphere();
    root.add(batch);removed+=group.length-1;
  }
  return removed;
}

/** Matching near/far cells switch together, including while changing to the aerial view. */
export function updateVegetationDetail(root:THREE.Object3D,cameraWorld:THREE.Vector3):boolean {
  const local=root.worldToLocal(cameraWorld.clone());let changed=false;
  root.traverse(o=>{
    if(!(o instanceof THREE.InstancedMesh)||!o.userData.vegetation_lod)return;
    const near=local.distanceTo(o.userData.vegetation_center)<o.userData.vegetation_distance;
    const visible=o.userData.vegetation_lod==='near'?near:!near;
    if(o.visible!==visible){o.visible=visible;changed=true;}
  });
  return changed;
}

/** Batch static opaque details for rendering; the editable Blender file stays separate. */
export function batchStaticScene(root: THREE.Object3D): { before: number; after: number } {
  const instancedRemoved=instanceAuthoredVegetation(root);
  root.updateMatrixWorld(true);
  const inverseRoot=new THREE.Matrix4().copy(root.matrixWorld).invert();
  const groups=new Map<string,THREE.Mesh[]>();
  let before=0;
  root.traverse(object=>{
    if (!(object instanceof THREE.Mesh)) return;
    before++;
    if (object instanceof THREE.SkinnedMesh || object instanceof THREE.InstancedMesh || Array.isArray(object.material) || object.material.transparent || object.morphTargetInfluences?.length) return;
    for(let p:THREE.Object3D|null=object;p;p=p.parent){
      if(p.userData.authored_vegetation===true)return;
      if(p===root)break;
    }
    const attributes=(Object.entries(object.geometry.attributes) as [string,THREE.BufferAttribute | THREE.InterleavedBufferAttribute][]).map(([name,a])=>`${name}:${a.itemSize}:${a.normalized}:${(a instanceof THREE.BufferAttribute ? a.array : a.data.array).constructor.name}`).sort().join('|');
    const key=`${object.material.uuid}:${object.castShadow}:${object.receiveShadow}:${!!object.geometry.index}:${!!object.userData.hide_in_overview}:${attributes}`;
    const group=groups.get(key) ?? [];
    group.push(object); groups.set(key,group);
  });
  const retired=new Set<THREE.BufferGeometry>();
  let after=before;
  for (const meshes of groups.values()) {
    if (meshes.length<12) continue;
    const transformed=meshes.map(mesh=>{
      const geometry=mesh.geometry.clone();
      // GLB quantization stores local coordinates in integer attributes. Applying
      // world transforms to those arrays wraps negative positions and truncates
      // fractional values; decode before baking the transform into a merged mesh.
      for(const name of ['position','normal','tangent']){
        const attribute=geometry.getAttribute(name);if(!attribute)continue;
        const values=new Float32Array(attribute.count*attribute.itemSize);
        for(let i=0;i<attribute.count;i++)for(let c=0;c<attribute.itemSize;c++)values[i*attribute.itemSize+c]=attribute.getComponent(i,c);
        geometry.setAttribute(name,new THREE.BufferAttribute(values,attribute.itemSize));
      }
      return geometry.applyMatrix4(new THREE.Matrix4().multiplyMatrices(inverseRoot,mesh.matrixWorld));
    });
    const merged=mergeGeometries(transformed,false);
    transformed.forEach(geometry=>geometry.dispose());
    if (!merged) continue;
    merged.computeBoundingSphere();
    const batch=new THREE.Mesh(merged,meshes[0].material);
    batch.name='static_detail_batch';
    batch.userData.hide_in_overview=!!meshes[0].userData.hide_in_overview;
    batch.castShadow=meshes[0].castShadow; batch.receiveShadow=meshes[0].receiveShadow;
    for(const mesh of meshes) { mesh.removeFromParent(); retired.add(mesh.geometry); }
    root.add(batch); after-=meshes.length-1;
  }
  root.traverse(object=>{ if(object instanceof THREE.Mesh) retired.delete(object.geometry); });
  retired.forEach(geometry=>geometry.dispose());
  return {before:before+instancedRemoved,after};
}
