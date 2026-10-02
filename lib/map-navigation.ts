import { hitsPolygon, solidCollider, reachableFloor, blocksWalking, worldFloors, worldObstacles, type Point, type Place, type World } from './world.ts';

export const regionalBounds = [126.625, 126.87, 34.985, 35.044] as const;
export const regionalSize = [1000, 400] as const;

export function regionalPoint(lon: number, lat: number): Point {
  return [(lon-regionalBounds[0])/(regionalBounds[1]-regionalBounds[0])*regionalSize[0], (regionalBounds[3]-lat)/(regionalBounds[3]-regionalBounds[2])*regionalSize[1]];
}

/** A map jump is an explicit relocation. It may never finish in a solid or outside the world. */
export function canTravelTo(point: Point, world: World, height=0): boolean {
  const [x,z] = point, b=world.bounds;
  if(!Number.isFinite(x)||!Number.isFinite(z)||!Number.isFinite(height)||x<b[0]+.3||x>b[1]-.3||z<b[2]+.3||z>b[3]-.3)return false;
  if(world.verticalNavigation){
    const floor=reachableFloor(x,z,height,worldFloors(world.solids),world.requireFloor);
    return floor!==null&&!blocksWalking(x,z,floor,worldObstacles(world.solids));
  }
  return !world.solids.some(s=>s.collision && hitsPolygon(x,z,solidCollider(s)));
}

export function mapArrival(place: Place, world: World): Point | null {
  const origin=place.arrival ?? place.position;
  const valid=(p: Point)=>canTravelTo(p,world,place.arrivalHeight??0) && (!place.footprint || hitsPolygon(...p,place.footprint,0));
  if(valid(origin))return origin;
  for(let radius=.6;radius<=Math.min(place.radius,24);radius+=.6){
    for(let i=0;i<32;i++){
      const p: Point=[origin[0]+Math.cos(i*Math.PI/16)*radius,origin[1]+Math.sin(i*Math.PI/16)*radius];
      if(valid(p))return p;
    }
  }
  return null;
}

export function mapSolids(world: World) {
  return world.solids.filter(s=>/^(osm-building|photo-building|context_.*_wall|mapped_reservoir_water|mapped_river_water|ground_floor|road_|road-edge|hall-wall|rail-ballast|walk-floor_platform|walk-floor_approach|walk-floor_turnaround|mound_|path_|replica_outline|exhibit-case|museum-wall|walk-floor_bridge|walk-floor_cafe|walk-floor_dock|walk-floor_riverfront|campus_building_|campus_upper_envelope_|rc_residence_|library_annular_envelope|campus_parking_|sports_court_|athletics_track_red|football_pitch)/.test(s.name));
}

export function mapColor(name: string): string {
  return /^mapped_(reservoir|river)/.test(name) ? '#759b9a' : name.startsWith('context_') ? '#a9afa3' : name.startsWith('replica') ? '#c59665' : name.startsWith('walk-floor') ? '#d3bd94' : name.startsWith('mound_') ? '#6d9152' : name.includes('lawn') ? '#bfce9a' : name.includes('grove') ? '#829d63' : name.includes('parking') ? '#abb2a8' : name.includes('court') ? '#c98c73' : name.startsWith('rail') ? '#897f70' : /^(road|path)/.test(name) ? '#f8f5e9' : name.startsWith('hall') ? '#407064' : '#bdc7b9';
}
