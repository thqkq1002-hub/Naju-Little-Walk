export type Vec3 = [number, number, number];
export type Point = [number, number];
export type Solid = {
  name: string;
  kind: 'box' | 'cylinder' | 'sphere' | 'roof' | 'building';
  position: Vec3;
  size: Vec3;
  color: string;
  rotation?: number;
  footprint?: Point[];
  collision?: boolean;
  /** Authored sloping surface: y = a*x + b*z + c, in world metres. */
  floorPlane?: [number, number, number];
};
export type Sign = { text: string; position: Vec3; width: number; rotation?: number; color?: string };
export type Arrival = { x: number; z: number; yaw: number; pitch?: number; height?: number };
export type Portal = { id: string; position: Point; radius: number; target: string; arrival: string; label: string; height?: number };
export type Place = { id: string; name: string; description: string; position: Point; radius: number; indoor?: boolean; footprint?: Point[]; arrival?: Point; arrivalHeight?: number; arrivalYaw?: number; arrivalPitch?: number; mapLabel?: string };
export type World = {
  title: string;
  subtitle: string;
  source: string;
  bounds: [number, number, number, number];
  spawn: { x: number; z: number; yaw: number; height?: number };
  solids: Solid[];
  signs: Sign[];
  places: Place[];
  lights?: { position: Vec3; color: string; intensity: number; distance: number }[];
  verticalNavigation?: boolean;
  requireFloor?: boolean;
  arrivals?: Record<string, Arrival>;
  portals?: Portal[];
  sceneLinks?: {label:string;target:string}[];
  viewMode?: 'panorama';
  boats?: import('./boat-navigation.ts').BoatDefinition[];
  monorail?: import('./monorail.ts').MonorailDefinition;
  navigationWater?: import('./boat-navigation.ts').NavigationWater;
  lighting?: { exposure: number; ambient: number; sun: number };
  architectureViews?: { id: string; label: string; center: Vec3; radius: number; elevation: number; angle: number; fov?: number }[];
};

export function currentPlace(x: number, z: number, places: Place[], height?:number): Place | undefined {
  return places.find(p => (height===undefined || p.arrivalHeight===undefined || Math.abs(p.arrivalHeight-height)<.7) && (p.footprint ? hitsPolygon(x,z,p.footprint,0) : Math.hypot(p.position[0]-x,p.position[1]-z)<p.radius));
}

export type Collider = Point[];
export type Floor = { polygon: Collider; height: number; plane?: [number, number, number] };

export function heightOnFloor(floor: Floor, x: number, z: number): number {
  return floor.plane ? floor.plane[0]*x + floor.plane[1]*z + floor.plane[2] : floor.height;
}

export type WalkObstacle = { polygon: Collider; minY: number; maxY: number; minX: number; maxX: number; minZ: number; maxZ: number };

export function worldObstacles(solids: Solid[]): WalkObstacle[] {
  return solids.filter(s=>s.collision).map(s=>{
    const polygon=solidCollider(s), base=s.position[1]-(s.kind==='building'?0:s.size[1]/2);
    return {polygon,minY:base,maxY:base+s.size[1],minX:Math.min(...polygon.map(p=>p[0])),maxX:Math.max(...polygon.map(p=>p[0])),minZ:Math.min(...polygon.map(p=>p[1])),maxZ:Math.max(...polygon.map(p=>p[1]))};
  });
}

export function blocksWalking(x: number,z: number,height: number,obstacles: WalkObstacle[]) {
  return obstacles.some(o=>o.maxY>height+.08 && o.minY<height+1.65 && x>=o.minX-.28 && x<=o.maxX+.28 && z>=o.minZ-.28 && z<=o.maxZ+.28 && hitsPolygon(x,z,o.polygon));
}

/** Choose a reachable floor, so a balcony above the lobby never lifts a visitor through its ceiling. */
export function reachableFloor(x: number,z: number,height: number,floors: Floor[],requireFloor=false): number | null {
  let best: number|null = !requireFloor && Math.abs(height)<=.36?0:null;
  for(const floor of floors){
    if(!hitsPolygon(x,z,floor.polygon,0))continue;
    const surfaceHeight=heightOnFloor(floor,x,z);
    if(Math.abs(surfaceHeight-height)>.36)continue;
    if(best===null || surfaceHeight>best)best=surfaceHeight;
  }
  return best;
}

export function moveOnFloors(x: number,z: number,height: number,dx: number,dz: number,obstacles: WalkObstacle[],floors: Floor[],bounds: World['bounds'],requireFloor=false) {
  const count=Math.max(1,Math.ceil(Math.hypot(dx,dz)/.12));
  const tryStep=(nx:number,nz:number)=>{
    if(nx<bounds[0]+.3||nx>bounds[1]-.3||nz<bounds[2]+.3||nz>bounds[3]-.3)return;
    const nextHeight=reachableFloor(nx,nz,height,floors,requireFloor);
    if(nextHeight!==null&&!blocksWalking(nx,nz,nextHeight,obstacles)){x=nx;z=nz;height=nextHeight;}
  };
  for(let i=0;i<count;i++){tryStep(x+dx/count,z);tryStep(x,z+dz/count);}
  return {x,z,height};
}

export function worldFloors(solids: Solid[]): Floor[] {
  return solids.filter(s => s.name.startsWith('ground_floor') || s.name.startsWith('walk-floor')).map(s => ({ polygon: solidCollider(s), height: s.position[1] + s.size[1] * (s.kind === 'building' ? 1 : .5), ...(s.floorPlane ? {plane:s.floorPlane} : {}) }));
}

export function floorHeight(x: number, z: number, floors: Floor[]) {
  return floors.reduce((height, floor) => hitsPolygon(x, z, floor.polygon, 0) ? Math.max(height, heightOnFloor(floor,x,z)) : height, 0);
}

export function solidCollider(s: Solid): Collider {
  const footprint = s.footprint ?? [
    [-s.size[0] / 2, -s.size[2] / 2], [s.size[0] / 2, -s.size[2] / 2],
    [s.size[0] / 2, s.size[2] / 2], [-s.size[0] / 2, s.size[2] / 2],
  ];
  const c = Math.cos(s.rotation ?? 0), sin = Math.sin(s.rotation ?? 0);
  return footprint.map(([x, z]) => [s.position[0] + x * c + z * sin, s.position[2] - x * sin + z * c]);
}

export function hitsPolygon(x: number, z: number, polygon: Collider, radius = 0.28) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [ax, az] = polygon[i], [bx, bz] = polygon[j];
    if ((az > z) !== (bz > z) && x < (bx - ax) * (z - az) / (bz - az) + ax) inside = !inside;
    const dx = bx - ax, dz = bz - az;
    const t = Math.max(0, Math.min(1, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz || 1)));
    if ((x - ax - t * dx) ** 2 + (z - az - t * dz) ** 2 < radius ** 2) return true;
  }
  return inside;
}

export function movePlayer(x: number, z: number, dx: number, dz: number, colliders: Collider[], bounds: World['bounds']) {
  const steps = Math.max(1, Math.ceil(Math.hypot(dx, dz) / 0.12));
  const blocked = (px: number, pz: number) => px < bounds[0] + 0.3 || px > bounds[1] - 0.3 || pz < bounds[2] + 0.3 || pz > bounds[3] - 0.3 || colliders.some(p => hitsPolygon(px, pz, p));
  for (let i = 0; i < steps; i++) {
    if (!blocked(x + dx / steps, z)) x += dx / steps;
    if (!blocked(x, z + dz / steps)) z += dz / steps;
  }
  return { x, z };
}
