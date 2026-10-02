import { destinations } from './destinations.ts';
import type { Portal, World } from './world.ts';
import { canTravelTo } from './map-navigation.ts';

/** Only authored arrivals are accepted; URL coordinates never bypass collisions. */
export function sceneArrival(world: World, search: string) {
  const key=new URLSearchParams(search).get('at');
  const arrival=key && Object.hasOwn(world.arrivals??{},key) ? world.arrivals![key] : undefined;
  if(arrival && canTravelTo([arrival.x,arrival.z],world,arrival.height??0))return { ...arrival, entered:true };
  return {...world.spawn,height:world.spawn.height??0,entered:false};
}

export function portalAt(world: World,x: number,z: number,height=0): Portal | undefined {
  return world.portals?.find(p=>Math.abs((p.height??0)-height)<.6 && Math.hypot(p.position[0]-x,p.position[1]-z)<p.radius);
}

export function portalHref(portal: Portal): string | null {
  if(!Object.hasOwn(destinations,portal.target) || !/^[a-z0-9-]+$/.test(portal.arrival))return null;
  return `/?${new URLSearchParams({place:portal.target,at:portal.arrival})}`;
}
