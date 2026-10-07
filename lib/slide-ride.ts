import type {DestinationId} from './destinations.ts';
import type {Point,Solid,World} from './world.ts';

/** A seated ride down an authored chute, ending standing on a landing mat that joins the walking floors. */
export type SlideRideData={
  id:string;name:string;
  /** Trough floor from the top lip to the stop point on the mat, [x, y, z] in walk metres. */
  route:[number,number,number][];
  entry:{x:number;z:number;height:number;radius:number};
  mat:{modelUrl:string;position:[number,number,number];yaw:number;floor:Point[];height:number};
  estimated:string;
};
export type SlidePose={x:number;y:number;z:number;eye:number;yaw:number;pitch:number;roll:number;fov:number;speed:number;progress:number;landed:boolean;done:boolean};

const rides:Partial<Record<DestinationId,string>>={'bitgaram-park':'/bitgaram-slide-ride.json?v=1'};
export const slideRideUrl=(id:DestinationId)=>rides[id];

/** The mat is walkable: the ride ends there and visitors step onto the stair landing beside it. */
export function withSlideLanding(world:World,ride:SlideRideData):World {
  const floor:Solid={name:'walk-floor_slide_landing_mat',kind:'building',position:[0,ride.mat.height-.05,0],size:[0,.05,0],footprint:ride.mat.floor,color:'#1f4f9e',collision:false};
  return {...world,solids:[...world.solids,floor]};
}

const G=9.81,DRAG=.045,ROLLING=.25,RUNOUT=12,RUNOUT_BRAKE=5,MAT_BRAKE=2.6,MIN_SPEED=1.1,SEATED=.85,STANDING=1.72,STAND_UP=.9;
const wrap=(a:number)=>Math.atan2(Math.sin(a),Math.cos(a));

export class SlideRide {
  readonly length:number;
  /** Distance along the route where the granite trough ends and the mat begins. */
  readonly troughEnd:number;
  private readonly cumulative:number[];
  private readonly data:SlideRideData;
  s=0;v=1.4;private time=0;private standing=0;
  done=false;

  constructor(data:SlideRideData) {
    this.data=data;
    const r=data.route;
    this.cumulative=r.map((_,i)=>0);
    for(let i=1;i<r.length;i++)this.cumulative[i]=this.cumulative[i-1]+Math.hypot(r[i][0]-r[i-1][0],r[i][1]-r[i-1][1],r[i][2]-r[i-1][2]);
    this.length=this.cumulative.at(-1)!;
    this.troughEnd=this.cumulative[r.length-3];
  }

  at(s:number):[number,number,number] {
    const r=this.data.route,c=this.cumulative,d=Math.min(Math.max(s,0),this.length);
    let lo=0,hi=c.length-1;
    while(hi-lo>1){const mid=(lo+hi)>>1;if(c[mid]<=d)lo=mid;else hi=mid;}
    const t=(d-c[lo])/((c[hi]-c[lo])||1);
    return [r[lo][0]+(r[hi][0]-r[lo][0])*t,r[lo][1]+(r[hi][1]-r[lo][1])*t,r[lo][2]+(r[hi][2]-r[lo][2])*t];
  }
  /** Camera yaw looking down the chute (forward is -sin, -cos of yaw). */
  heading(s:number){const a=this.at(s-.5),b=this.at(s+2.5);return Math.atan2(-(b[0]-a[0]),-(b[2]-a[2]));}

  update(dt:number,reducedMotion=false):SlidePose {
    dt=Math.min(Math.max(dt,0),.06);this.time+=dt;
    const landed=this.s>=this.troughEnd;
    if(this.standing===0){
      for(let i=0;i<3;i++){
        const h=dt/3;
        if(this.s<this.troughEnd){
          const drop=this.at(this.s-.5)[1]-this.at(this.s+.5)[1];
          // The last metres of granite act as a run-out, so riders reach the mat at a jogging pace.
          const runout=Math.max(0,1-(this.troughEnd-this.s)/RUNOUT);
          const accel=G*drop*(reducedMotion?.7:1)-DRAG*this.v*this.v-ROLLING-RUNOUT_BRAKE*runout;
          this.v=Math.max(MIN_SPEED,this.v+accel*h);
        }else this.v=Math.max(0,this.v-MAT_BRAKE*h);
        this.s+=this.v*h;
        if(this.s>=this.length||(this.s>this.troughEnd&&this.v<.05)){this.s=Math.min(this.s,this.length);this.v=0;this.standing=1e-6;break;}
      }
    }else this.standing+=dt;
    const rise=Math.min(1,this.standing/STAND_UP),ease=rise*rise*(3-2*rise);
    if(rise>=1)this.done=true;
    const [x,y,z]=this.at(this.s);
    const yaw=this.heading(this.s);
    const turn=wrap(this.heading(this.s+1)-this.heading(this.s-1))/2;
    const calm=reducedMotion?0:1-ease;
    const fast=Math.min(this.v/9,1);
    const ahead=this.at(this.s+4)[1];
    return {
      x,y,z,
      eye:SEATED+(STANDING-SEATED)*ease+(reducedMotion?0:Math.sin(this.time*23)*.012*fast+Math.sin(this.time*7.3)*.006*fast)*calm,
      yaw,
      pitch:-Math.atan2(y-ahead,4)*.9*(1-ease),
      roll:Math.max(-.22,Math.min(.22,turn*this.v*this.v/G*.9))*calm,
      fov:60+(reducedMotion?0:14*fast)*calm,
      speed:Math.round(this.v*3.6),
      progress:Math.min(1,this.s/this.length),
      landed,done:this.done,
    };
  }

  /** Jump straight to the mat, already standing. */
  skip():SlidePose{this.s=this.length;this.v=0;this.standing=STAND_UP;return this.update(0);}
}
