import type {DestinationId} from './destinations.ts';
import type {Solid,World} from './world.ts';

export type NpcCharacter='baedoli'|'beodeuri'|'hongdoli'|'teacher';
export type NpcPlacement={character:NpcCharacter;position:[number,number,number];yaw:number;collisionRadius:number;height:number};
export type NpcManifest={version:number;assets:Record<NpcCharacter,{name:string;modelUrl:string}>;placements:Partial<Record<DestinationId,NpcPlacement>>};

/** One guide beside the start, shared by rendering, walking and map travel. */
export function withNpcObstacle(world:World,placement:NpcPlacement):World {
  const [x,y,z]=placement.position;
  const obstacle:Solid={name:`npc-guide-${placement.character}`,kind:'cylinder',position:[x,y+placement.height/2,z],size:[placement.collisionRadius*2,placement.height,placement.collisionRadius*2],color:'#778878',collision:true};
  return {...world,solids:[...world.solids,obstacle]};
}
