import * as THREE from 'three';

export type Fixture = {position: [number,number,number]; color: string; intensity: number; distance: number};

/** Keep the shader light count bounded; authored fixtures remain in the GLB. */
export function createLocalLights(scene: THREE.Scene, fixtures: Fixture[], limit=8) {
  const pool=Array.from({length:Math.min(limit,fixtures.length)},()=>{
    const light=new THREE.PointLight(0xffffff,0,1,2);
    scene.add(light);return light;
  });
  const update=(position: THREE.Vector3)=>{
    const nearby=fixtures.map(f=>({f,d:position.distanceToSquared(new THREE.Vector3(...f.position))}))
      .filter(({f,d})=>d<(f.distance+25)**2)
      .sort((a,b)=>b.f.intensity/(1+b.d)-a.f.intensity/(1+a.d)).slice(0,pool.length);
    pool.forEach((light,i)=>{
      const fixture=nearby[i]?.f;
      light.intensity=fixture?.intensity??0;
      if(fixture){light.position.set(...fixture.position);light.color.set(fixture.color);light.distance=fixture.distance;}
    });
  };
  return {pool,update};
}
