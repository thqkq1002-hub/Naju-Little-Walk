import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { batchStaticScene } from './static-scene.ts';
import { unpackModel } from './model-transport.ts';
import { moveOnFloors, worldFloors, worldObstacles, type Point, type World } from './world.ts';
import { atBerth, boatToWorld, canBoard, mooredBoat, stepBoat, stepDeparture, type BoatDefinition, type BoatState } from './boat-navigation.ts';

export type BoatHud = {
  aboard: string | null; mode: 'shore'|'deck'|'helm'; speed: number; blocked: boolean; canLeave: boolean;
  near: string | null; boats: {id:string;name:string;x:number;z:number;yaw:number;note:string;berthed:boolean}[];
  departing: boolean;
};
type Vessel = { definition: BoatDefinition; state: BoatState; object: THREE.Group; floors: ReturnType<typeof worldFloors>; obstacles: ReturnType<typeof worldObstacles> };
export class BoatFleet {
  vessels: Vessel[]=[];
  passenger: { vessel: Vessel; position: Point; height: number; helm: boolean; departure:number } | null=null;
  private world: World;
  constructor(world: World) {this.world=world;}
  async load(scene: THREE.Scene) {
    const loader=new GLTFLoader();
    for(const definition of this.world.boats??[]){
      const response=await fetch(definition.modelUrl);
      if(!response.ok)throw new Error(`${definition.name} 모델을 불러오지 못했습니다.`);
      const gltf=await loader.parseAsync(await unpackModel(await response.arrayBuffer()),'');
      gltf.scene.traverse(o=>{if(o instanceof THREE.Mesh){o.castShadow=true;o.receiveShadow=true;}});
      batchStaticScene(gltf.scene);
      const vessel={definition,state:mooredBoat(definition),object:gltf.scene,floors:worldFloors(definition.solids),obstacles:worldObstacles(definition.solids)};
      this.vessels.push(vessel);scene.add(gltf.scene);this.sync(vessel);
    }
  }
  sync(v: Vessel){ v.object.position.set(v.state.x,v.definition.waterY,v.state.z);v.object.rotation.y=v.state.yaw; }
  stop(){for(const v of this.vessels)v.state.speed=0;if(this.passenger)this.passenger.departure=0;}
  reset(){this.passenger=null;for(const v of this.vessels){v.state=mooredBoat(v.definition);this.sync(v);}}
  leaveForTravel(){if(this.passenger){const v=this.passenger.vessel;v.state=mooredBoat(v.definition);this.sync(v);}this.passenger=null;}
  board(id:string,position:Point,elevation:number){
    const v=this.vessels.find(v=>v.definition.id===id);
    if(!v||this.passenger||!canBoard(position,elevation,v.state,v.definition))return false;
    this.passenger={vessel:v,position:[...v.definition.boarding],height:v.definition.deckHeight,helm:false,departure:0};return true;
  }
  drive(){if(!this.passenger)return;this.stop();this.passenger.helm=true;this.passenger.position=[...this.passenger.vessel.definition.helm];this.passenger.height=this.passenger.vessel.definition.deckHeight;if(atBerth(this.passenger.vessel.state,this.passenger.vessel.definition))this.passenger.departure=this.passenger.vessel.definition.length*.25;}
  deck(){if(!this.passenger)return;this.stop();this.passenger.helm=false;}
  returnToBerth(){
    if(!this.passenger)return;
    const v=this.passenger.vessel;v.state=mooredBoat(v.definition);this.sync(v);
    this.passenger.helm=false;this.passenger.departure=0;this.passenger.position=[...v.definition.boarding];this.passenger.height=v.definition.deckHeight;
  }
  leave(): {position:Point;height:number}|null {
    if(!this.passenger)return null;
    const v=this.passenger.vessel;
    if(!atBerth(v.state,v.definition))return null;
    const result={position:v.definition.shore,height:v.definition.shoreHeight};this.passenger=null;return result;
  }
  update(dt:number,keys:Set<string>,yaw:number){
    const p=this.passenger;if(!p)return null;
    const v=p.vessel,oldYaw=v.state.yaw;
    const forward=Number(keys.has('KeyW')||keys.has('ArrowUp'))-Number(keys.has('KeyS')||keys.has('ArrowDown'));
    const side=Number(keys.has('KeyD'))-Number(keys.has('KeyA'));
    if(p.helm&&this.world.navigationWater){
      if(keys.has('Space'))p.departure=0;
      if(p.departure>0){
        const distance=Math.min(p.departure,dt*1.3);
        v.state=stepDeparture(v.state,v.definition,distance,this.world.navigationWater,this.vessels);
        p.departure=v.state.blocked?0:Math.max(0,p.departure-distance);
      }else{
        const steer=side||Number(keys.has('ArrowRight'))-Number(keys.has('ArrowLeft'));
        v.state=stepBoat(v.state,v.definition,{throttle:forward,steer,brake:keys.has('Space')},dt,this.world.navigationWater,this.vessels);
      }
      this.sync(v);
    }else{
      const relative=yaw-v.state.yaw,speed=2.3*dt/(Math.hypot(forward,side)||1);
      const next=moveOnFloors(p.position[0],p.position[1],p.height,(-Math.sin(relative)*forward+Math.cos(relative)*side)*speed,(-Math.cos(relative)*forward-Math.sin(relative)*side)*speed,v.obstacles,v.floors,[-v.definition.beam/2,v.definition.beam/2,-v.definition.length/2,v.definition.length/2],true);
      p.position=[next.x,next.z];p.height=next.height;
    }
    return {...this.eye()!,yawDelta:v.state.yaw-oldYaw};
  }
  eye(){const p=this.passenger;if(!p)return null;const [x,z]=boatToWorld(p.position,p.vessel.state);return {x,z,height:p.height+p.vessel.definition.waterY};}
  hud(position:Point,height:number):BoatHud {
    const p=this.passenger;
    return {aboard:p?.vessel.definition.id??null,mode:p?(p.helm?'helm':'deck'):'shore',departing:!!p&&p.departure>0,speed:Math.abs(p?.vessel.state.speed??0)*3.6,blocked:p?.vessel.state.blocked??false,canLeave:!!p&&atBerth(p.vessel.state,p.vessel.definition),near:this.vessels.find(v=>canBoard(position,height,v.state,v.definition))?.definition.id??null,boats:this.vessels.map(v=>({id:v.definition.id,name:v.definition.name,x:v.state.x,z:v.state.z,yaw:v.state.yaw,note:`${v.definition.length} × ${v.definition.beam}m · ${v.definition.id==='najuho'?'사진 비례 추정':'공개 제원, 선실 치수 추정'}`,berthed:atBerth(v.state,v.definition)}))};
  }
}
