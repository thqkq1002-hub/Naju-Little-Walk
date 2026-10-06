/** Inspect existing Blender exports; preserve models and write only guide placements. */
import fs from 'node:fs';
import * as THREE from 'three';
import {readModel} from '../tests/gltf-geometry.mjs';
import {destinations} from '../lib/destinations.ts';
import {canTravelTo} from '../lib/map-navigation.ts';
import {floorHeight,reachableFloor,worldFloors} from '../lib/world.ts';

const assignments={geumseonggwan:'beodeuri',bogam:'beodeuri','bitgaram-park':'baedoli','bitgaram-kepco':'baedoli','bitgaram-kentech':'baedoli',yeongsanpo:'hongdoli',dasi:'teacher'};
const names={baedoli:'배돌이',beodeuri:'버들낭자',hongdoli:'홍돌이',teacher:'선생님'};
const assets={};
fs.mkdirSync('public/models/npc',{recursive:true});
for(const key of Object.keys(names)){
  const folder=`assets/npc/meshy-first-pass-20261002/${key}`;
  const path=`${folder}/${key}-colored-v4.glb`;
  const {scene}=readModel(path),box=new THREE.Box3().setFromObject(scene),size=box.getSize(new THREE.Vector3());
  fs.copyFileSync(path,`public/models/npc/${key}-v4.glb`);
  assets[key]={name:names[key],modelUrl:`/models/npc/${key}-v4.glb`,height:size.y,width:size.x,depth:size.z,front:'+Z',bottom:box.min.y};
  scene.traverse(o=>o.geometry?.dispose());
}
const placements={};
for(const [id,character] of Object.entries(assignments)){
  const destination=destinations[id],world=JSON.parse(fs.readFileSync('public'+destination.worldUrl.split('?')[0],'utf8'));
  const {scene}=readModel('public'+destination.modelUrl.split('?')[0].replace(/\.gz$/,''));
  const spawn=world.spawn,floors=worldFloors(world.solids),s=Math.sin(spawn.yaw),c=Math.cos(spawn.yaw),asset=assets[character];
  const base=world.verticalNavigation?(reachableFloor(spawn.x,spawn.z,spawn.height??0,floors)??0):floorHeight(spawn.x,spawn.z,floors);
  const radius=Math.min(.7,Math.max(.3,asset.width*.22));
  let chosen;
  for(const distance of [4.5,5,4,5.5,6,3.5]){
    // The park's right side has the elevated stair handrail; welcome from the left.
    for(const side of id==='bitgaram-park'?[-1.4,1.4,-1.8,1.8,-1,1,-2.2,2.2]:[1.4,-1.4,1.8,-1.8,1,-1,2.2,-2.2]){
      const x=spawn.x-s*distance+c*side,z=spawn.z-c*distance-s*side;
      const height=world.verticalNavigation?reachableFloor(x,z,base,floors,world.requireFloor):floorHeight(x,z,floors);
      if(height===null || Math.abs(height-base)>.25)continue;
      if(![0,...Array.from({length:12},(_,i)=>(i+1)*Math.PI/6)].every((angle,i)=>canTravelTo([x+(i?Math.cos(angle)*radius:0),z+(i?Math.sin(angle)*radius:0)],world,height)))continue;
      if(world.portals?.some(p=>Math.hypot(x-p.position[0],z-p.position[1])<p.radius+radius+.5))continue;
      const origin=new THREE.Vector3(spawn.x,base+1.72,spawn.z),target=new THREE.Vector3(x,height+asset.height*.6,z),delta=target.clone().sub(origin);
      const hit=new THREE.Raycaster(origin,delta.clone().normalize(),.05,delta.length()-.15).intersectObject(scene,true)[0];
      if(hit)continue;
      chosen={character,position:[x,height-asset.bottom,z],yaw:Math.atan2(spawn.x-x,spawn.z-z),collisionRadius:radius,height:asset.height,spawn:{...spawn},distanceFromStart:Math.hypot(x-spawn.x,z-spawn.z)};break;
    }
    if(chosen)break;
  }
  if(!chosen)throw new Error(`No unobstructed start placement: ${id}`);
  placements[id]=chosen;
  console.log(id,JSON.stringify(chosen));
  scene.traverse(o=>o.geometry?.dispose());
}
fs.writeFileSync('public/npc-placements.json',JSON.stringify({version:1,source:'사용자 지정 지역의 창작 안내 캐릭터. 실제 현장 시설이 아님. Blender 채색 초안 v4, 고정 자세.',assets,placements},null,2)+'\n');
