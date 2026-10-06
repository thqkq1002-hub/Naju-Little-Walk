import type {DestinationId} from './destinations.ts';
import type {Solid,World} from './world.ts';

export type NpcCharacter='baedoli'|'beodeuri'|'hongdoli'|'teacher';
export type NpcPlacement={character:NpcCharacter;position:[number,number,number];yaw:number;collisionRadius:number;height:number};
/** A further guide elsewhere on the same map, e.g. down at a pier; `id` names its script. */
export type ExtraNpcPlacement=NpcPlacement&{id:string};
export type NpcManifest={version:number;assets:Record<NpcCharacter,{name:string;modelUrl:string}>;placements:Partial<Record<DestinationId,NpcPlacement>>;extraPlacements?:Partial<Record<DestinationId,ExtraNpcPlacement[]>>};
export type PlacedGuide=NpcPlacement&{script:string};

/** The start guide first, then any extras; each carries the key of its intro script. */
export function guidePlacements(manifest:NpcManifest,destinationId:DestinationId):PlacedGuide[] {
  const start=manifest.placements[destinationId];
  return [...(start?[{...start,script:destinationId}]:[]),...(manifest.extraPlacements?.[destinationId]??[]).map(p=>({...p,script:p.id}))];
}

/** One guide beside the start, shared by rendering, walking and map travel. */
export function withNpcObstacle(world:World,placement:NpcPlacement):World {
  const [x,y,z]=placement.position;
  const obstacle:Solid={name:`npc-guide-${placement.character}`,kind:'cylinder',position:[x,y+placement.height/2,z],size:[placement.collisionRadius*2,placement.height,placement.collisionRadius*2],color:'#778878',collision:true};
  return {...world,solids:[...world.solids,obstacle]};
}
