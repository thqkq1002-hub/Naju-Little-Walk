import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {unpackModel} from './model-transport.ts';
import {initialRailState,railPose,railObstacle,nearRailStation,requestRail,boardRail,leaveRail,stepRail,type MonorailDefinition} from './monorail.ts';
import type {Point} from './world.ts';
export type RailHud={aboard:boolean;near:string|null;station:string|null;target:string|null;door:number;speed:number;progress:number;stations:{id:string;name:string}[]};
export class MonorailScene{
 state;root:THREE.Group|null=null;doors:{object:THREE.Object3D;z:number;direction:number}[]=[];
 constructor(public definition:MonorailDefinition){this.state=initialRailState(definition);}
 async load(scene:THREE.Scene,signal:AbortSignal){
  const response=await fetch(this.definition.modelUrl,{signal});if(!response.ok)throw new Error('모노레일 차량을 불러오지 못했습니다.');
  const gltf=await new GLTFLoader().parseAsync(await unpackModel(await response.arrayBuffer()),'');
  this.root=gltf.scene;
  // The park uses cached shadows; a moving cab must not leave a frozen shadow.
  this.root.traverse(o=>{if(o instanceof THREE.Mesh){o.castShadow=false;o.receiveShadow=true;}if(o.name==='monorail_door_left'||o.name==='monorail_door_right')this.doors.push({object:o,z:o.position.z,direction:o.name.endsWith('left')?-1:1});});
  scene.add(this.root);this.sync();
 }
 sync(){if(!this.root)return;const p=railPose(this.definition,this.state.distance);this.root.position.set(p.x,p.y,p.z);this.root.rotation.y=p.yaw;for(const d of this.doors)d.object.position.z=d.z+d.direction*this.state.door*.70;}
 update(dt:number){this.state=stepRail(this.definition,this.state,dt);this.sync();return this.eye();}
 eye(){if(!this.state.aboard)return null;const p=railPose(this.definition,this.state.distance);return {x:p.x,z:p.z,height:p.y+this.definition.floorOffset};}
 obstacle(){return railObstacle(this.definition,this.state.distance);}
 board(p:Point,h:number){const next=boardRail(this.definition,this.state,p,h);const boarded=next!==this.state;this.state=next;return boarded;}
 request(id:string){this.state=requestRail(this.definition,this.state,id);}
 leave(){const result=leaveRail(this.definition,this.state);if(!result)return null;this.state=result.state;return result.station;}
 reset(){this.state=initialRailState(this.definition);this.sync();}
 hud(p:Point,h:number):RailHud{return {aboard:this.state.aboard,near:nearRailStation(this.definition,p,h)?.id??null,station:this.state.station,target:this.state.target,door:this.state.door,speed:this.state.speed*3.6,progress:this.state.distance/this.definition.stations.at(-1)!.distance,stations:this.definition.stations.map(s=>({id:s.id,name:s.name}))};}
}
