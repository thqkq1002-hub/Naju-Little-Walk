import type { Vec3, Point, WalkObstacle } from './world.ts';
export type RailStation={id:string;name:string;distance:number;arrival:Point;height:number};
export type MonorailDefinition={modelUrl:string;route:Vec3[];stations:RailStation[];speed:number;acceleration:number;floorOffset:number;initialStation:string};
export type RailState={distance:number;speed:number;target:string|null;station:string|null;door:number;aboard:boolean};
export function railLength(d:MonorailDefinition){return d.route.slice(1).reduce((n,p,i)=>n+Math.hypot(...p.map((v,k)=>v-d.route[i][k])),0);}
export function railPose(d:MonorailDefinition,distance:number){
 let left=Math.max(0,Math.min(railLength(d),distance));
 for(let i=1;i<d.route.length;i++){
  const a=d.route[i-1],b=d.route[i],length=Math.hypot(...b.map((v,k)=>v-a[k]));
  if(left<=length||i===d.route.length-1){const t=length?left/length:0;return {x:a[0]+(b[0]-a[0])*t,y:a[1]+(b[1]-a[1])*t,z:a[2]+(b[2]-a[2])*t,yaw:Math.atan2(a[0]-b[0],a[2]-b[2])};}
  left-=length;
 }
 throw new Error('A monorail needs a valid route');
}
export function initialRailState(d:MonorailDefinition):RailState{const s=d.stations.find(s=>s.id===d.initialStation)??d.stations[0];return {distance:s.distance,speed:0,target:null,station:s.id,door:1,aboard:false};}
export function nearRailStation(d:MonorailDefinition,p:Point,h:number){return d.stations.find(s=>Math.hypot(p[0]-s.arrival[0],p[1]-s.arrival[1])<6&&Math.abs(h-s.height)<.6);}
export function railObstacle(d:MonorailDefinition,distance:number):WalkObstacle{
 const p=railPose(d,distance),c=Math.cos(p.yaw),s=Math.sin(p.yaw);
 const polygon:Point[]=[[-1.07,-2.05],[1.07,-2.05],[1.07,2.05],[-1.07,2.05]].map(([x,z])=>[p.x+x*c+z*s,p.z-x*s+z*c]);
 return {polygon,minY:p.y-.16,maxY:p.y+2.7,minX:Math.min(...polygon.map(p=>p[0])),maxX:Math.max(...polygon.map(p=>p[0])),minZ:Math.min(...polygon.map(p=>p[1])),maxZ:Math.max(...polygon.map(p=>p[1]))};
}
export function requestRail(d:MonorailDefinition,s:RailState,id:string):RailState{
 if(s.target||!d.stations.some(p=>p.id===id)||s.station===id)return s;
 return {...s,target:id,station:null,speed:0};
}
export function boardRail(d:MonorailDefinition,s:RailState,p:Point,h:number):RailState{
 const near=nearRailStation(d,p,h);
 return !s.aboard&&near?.id===s.station&&!s.target&&s.door>.98?{...s,aboard:true}:s;
}
export function leaveRail(d:MonorailDefinition,s:RailState){
 const station=d.stations.find(p=>p.id===s.station);
 return s.aboard&&station&&!s.target&&s.door>.98?{state:{...s,aboard:false},station}:null;
}
export function stepRail(d:MonorailDefinition,s:RailState,dt:number):RailState{
 if(!Number.isFinite(dt)||dt<=0)return s;
 let next={...s};let remaining=Math.min(dt,.25);
 while(remaining>1e-8){const t=Math.min(.02,remaining);remaining-=t;
  if(!next.target){next.door=Math.min(1,next.door+t*1.25);next.speed=0;continue;}
  next.door=Math.max(0,next.door-t*1.25);
  if(next.door>0)continue;
  const target=d.stations.find(p=>p.id===next.target)!;const delta=target.distance-next.distance;
  const wanted=Math.min(d.speed,Math.sqrt(2*d.acceleration*Math.abs(delta)));
  next.speed=Math.max(0,Math.min(wanted,next.speed+d.acceleration*t));
  const travel=Math.min(Math.abs(delta),next.speed*t);
  next.distance+=Math.sign(delta)*travel;
  if(Math.abs(target.distance-next.distance)<.004){next.distance=target.distance;next.station=target.id;next.target=null;next.speed=0;}
 }
 return next;
}
