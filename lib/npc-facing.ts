/**
 * Guides turn their whole body toward a nearby visitor and drift back to their authored pose when the
 * visitor walks away. The model's front is +Z, so a root yaw faces (sin yaw, cos yaw); feet never move.
 */
export const FACE_RANGE=20;
const SAME_LEVEL=2.5;
const TURN_RATE=4,RETURN_RATE=1.5;

export const yawToward=(fromX:number,fromZ:number,toX:number,toZ:number)=>Math.atan2(toX-fromX,toZ-fromZ);
const wrap=(angle:number)=>Math.atan2(Math.sin(angle),Math.cos(angle));

/** Ease along the shorter arc; never overshoots, whatever the frame time. */
export function turnYaw(current:number,target:number,dt:number,rate:number):number {
  return wrap(current+wrap(target-current)*(1-Math.exp(-rate*Math.max(dt,0))));
}

export type FacingGuide={position:[number,number,number];yaw:number};
/** The yaw a guide should take this frame; `instant` skips the easing for reduced motion. */
export function guideYaw(current:number,guide:FacingGuide,visitor:{x:number;z:number;height:number}|null,dt:number,instant=false):number {
  const [x,y,z]=guide.position;
  const distance=visitor?Math.hypot(visitor.x-x,visitor.z-z):Infinity;
  const tracking=!!visitor&&distance>.35&&distance<FACE_RANGE&&Math.abs(visitor.height-y)<SAME_LEVEL;
  const target=tracking?yawToward(x,z,visitor.x,visitor.z):guide.yaw;
  return instant?wrap(target):turnYaw(current,target,dt,tracking?TURN_RATE:RETURN_RATE);
}
