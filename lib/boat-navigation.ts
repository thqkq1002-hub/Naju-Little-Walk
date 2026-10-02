import { hitsPolygon, type Point, type Solid } from './world.ts';

export type BoatDefinition = {
  id: string; name: string; modelUrl: string; length: number; beam: number;
  dimensionsNote: string; home: { x: number; z: number; yaw: number };
  waterY: number; deckHeight: number; boarding: Point; helm: Point;
  shore: Point; shoreHeight: number; hull: Point[]; solids: Solid[];
};
export type BoatState = { id: string; x: number; z: number; yaw: number; speed: number; blocked: boolean };
export type NavigationWater = { polygons: Point[][]; obstacles: Point[][] };

export const mooredBoat = (boat: BoatDefinition): BoatState => ({ id: boat.id, ...boat.home, speed: 0, blocked: false });
export function boatToWorld([x,z]: Point, boat: Pick<BoatState,'x'|'z'|'yaw'>): Point {
  const c=Math.cos(boat.yaw),s=Math.sin(boat.yaw);
  return [boat.x+x*c+z*s,boat.z-x*s+z*c];
}
export function worldToBoat([x,z]: Point, boat: Pick<BoatState,'x'|'z'|'yaw'>): Point {
  const dx=x-boat.x,dz=z-boat.z,c=Math.cos(boat.yaw),s=Math.sin(boat.yaw);
  return [dx*c-dz*s,dx*s+dz*c];
}
export function atBerth(state: BoatState, definition: BoatDefinition) {
  return Math.hypot(state.x-definition.home.x,state.z-definition.home.z)<.5 && Math.abs(Math.atan2(Math.sin(state.yaw-definition.home.yaw),Math.cos(state.yaw-definition.home.yaw)))<.035 && Math.abs(state.speed)<.08;
}
export function canBoard(position: Point, elevation: number, state: BoatState, definition: BoatDefinition) {
  return atBerth(state,definition) && Math.abs(elevation-definition.shoreHeight)<.45 && Math.hypot(position[0]-definition.shore[0],position[1]-definition.shore[1])<3;
}
const cross=(a: Point,b: Point,c: Point)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
function segmentsCross(a: Point,b: Point,c: Point,d: Point) {
  const x=cross(a,b,c),y=cross(a,b,d),u=cross(c,d,a),v=cross(c,d,b);
  if(x*y<0&&u*v<0)return true;
  const on=(p:Point,q:Point,r:Point)=>Math.abs(cross(p,q,r))<1e-8&&r[0]>=Math.min(p[0],q[0])-1e-8&&r[0]<=Math.max(p[0],q[0])+1e-8&&r[1]>=Math.min(p[1],q[1])-1e-8&&r[1]<=Math.max(p[1],q[1])+1e-8;
  return on(a,b,c)||on(a,b,d)||on(c,d,a)||on(c,d,b);
}
export function polygonsOverlap(a: Point[], b: Point[]) {
  return a.some(p=>hitsPolygon(...p,b,0)) || b.some(p=>hitsPolygon(...p,a,0)) || a.some((p,i)=>b.some((q,j)=>segmentsCross(p,a[(i+1)%a.length],q,b[(j+1)%b.length])));
}
export function boatFitsWater(state: BoatState, definition: BoatDefinition, water: NavigationWater, others: {state:BoatState;definition:BoatDefinition}[]) {
  const hull=definition.hull.map(p=>boatToWorld(p,state));
  // Sample the perimeter, not only the centre, including concave shoreline bends.
  for(let i=0;i<hull.length;i++){
    const a=hull[i],b=hull[(i+1)%hull.length],n=Math.max(1,Math.ceil(Math.hypot(b[0]-a[0],b[1]-a[1])/.35));
    for(let j=0;j<=n;j++){
      const p:Point=[a[0]+(b[0]-a[0])*j/n,a[1]+(b[1]-a[1])*j/n];
      if(!water.polygons.some(poly=>hitsPolygon(...p,poly,0)))return false;
    }
  }
  return !water.obstacles.some(poly=>polygonsOverlap(hull,poly)) && !others.some(other=>other.state.id!==state.id&&polygonsOverlap(hull,other.definition.hull.map(p=>boatToWorld(p,other.state))));
}

/** Cast off sideways from the photographed +X boarding side before turning a long hull. */
export function stepDeparture(state:BoatState,definition:BoatDefinition,distance:number,water:NavigationWater,others:{state:BoatState;definition:BoatDefinition}[]):BoatState {
  let next={...state,speed:0,blocked:false};
  const length=Math.max(0,Math.min(distance,.2));
  const [x,z]=boatToWorld([-length,0],next),candidate={...next,x,z};
  return boatFitsWater(candidate,definition,water,others)?candidate:{...next,blocked:true};
}

/** Slow motor-tour controls. Substeps include swept hull rotation to prevent tunnelling. */
export function stepBoat(state: BoatState, definition: BoatDefinition, input: {throttle:number;steer:number;brake:boolean}, seconds: number, water: NavigationWater, others: {state:BoatState;definition:BoatDefinition}[]): BoatState {
  let next={...state,blocked:false};
  const duration=Math.max(0,Math.min(Number.isFinite(seconds)?seconds:0,.25));
  const steps=Math.max(1,Math.ceil(duration/.0125)),dt=duration/steps;
  for(let i=0;i<steps;i++){
    const throttle=Math.max(-1,Math.min(1,input.throttle));
    let speed=next.speed+throttle*.65*dt;
    speed*=Math.exp(-(input.brake?5:throttle===0?.65:.06)*dt);
    speed=Math.max(-1.4,Math.min(4.1,speed));
    if(Math.abs(speed)<.006)speed=0;
    const yaw=next.yaw-Math.max(-1,Math.min(1,input.steer))*.22*(speed/4.1)*dt;
    const candidate={...next,speed,yaw,x:next.x-Math.sin(yaw)*speed*dt,z:next.z-Math.cos(yaw)*speed*dt};
    if(!boatFitsWater(candidate,definition,water,others)){next.speed=0;next.blocked=true;break;}
    next=candidate;
  }
  return next;
}
