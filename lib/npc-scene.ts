import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import type {NpcManifest,NpcPlacement} from './npc-placement.ts';
import {NpcAnimation} from './npc-animation.ts';

/** Load only this region's Blender asset; never include guides in city batching. */
export async function loadNpcGuide(placement:NpcPlacement,manifest:NpcManifest,signal:AbortSignal):Promise<NpcAnimation> {
  const asset=manifest.assets[placement.character];
  const response=await fetch(asset.modelUrl,{signal});
  if(!response.ok)throw new Error(`${asset.name} 안내 캐릭터를 불러오지 못했습니다.`);
  const gltf=await new GLTFLoader().parseAsync(await response.arrayBuffer(),'');
  const root=gltf.scene;
  if(signal.aborted){
    root.traverse(o=>{if(o instanceof THREE.Mesh){o.geometry.dispose();for(const m of Array.isArray(o.material)?o.material:[o.material]){for(const v of Object.values(m))if(v instanceof THREE.Texture)v.dispose();m.dispose();}}});
    signal.throwIfAborted();
  }
  root.name=`npc-guide-${placement.character}`;
  root.userData.npcCharacter=placement.character;root.userData.npcName=asset.name;
  root.position.fromArray(placement.position);root.rotation.y=placement.yaw;
  // The moving guide is separate from the city batch and cached static shadow map.
  root.traverse(o=>{if(o instanceof THREE.Mesh){o.castShadow=false;o.receiveShadow=true;o.frustumCulled=false;}});
  const shadow=new THREE.Mesh(new THREE.CircleGeometry(placement.collisionRadius*1.6,24),new THREE.MeshBasicMaterial({color:0x263826,transparent:true,opacity:.12,depthWrite:false}));
  shadow.name='Guide_contact_shadow';shadow.rotation.x=-Math.PI/2;shadow.position.y=.012;root.add(shadow);
  root.updateMatrixWorld(true);
  return new NpcAnimation(root,gltf.animations);
}
