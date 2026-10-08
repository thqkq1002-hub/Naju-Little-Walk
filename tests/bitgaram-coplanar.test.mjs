import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {readModel} from './gltf-geometry.mjs';

// Decks and floors used to share exactly one height with the surface under them and flicker.
const zones={
  'below the slide':[[4,22,104,112],[-23,5,110,112],[5,16,107,112],[-25,-2,79,92]],
  'summit shelter':[[7,13,11,17],[-11,0,18.5,21],[4,6.5,19,23]],
};
const surfaces=/^(context_roof_garden_paving|walk-floor_lower_station|walk-floor_access101_(lower_gallery|lower_outdoor|turn_landings|upper_gallery|upper_outdoor)|walk-floor_outdoor_timber_stairs|ground_floor_summit|walk-floor_upper_station)$/;

test('overlapping decks and floors never share one height',()=>{
  const {scene,gltf}=readModel(new URL('../public/models/bitgaram-park.glb',import.meta.url));
  assert.ok(gltf.extras?.coplanarDeckFix?.ground_floor_summit,'Separation script applied');
  const targets=[];scene.traverse(o=>{if(surfaces.test(o.name))targets.push(o);});
  assert.equal(targets.length,10);
  const ray=new THREE.Raycaster();
  for(const [label,rects] of Object.entries(zones)){
    let overlaps=0,closest=Infinity;
    for(const [x0,x1,z0,z1] of rects)for(let x=x0;x<=x1;x+=.5)for(let z=z0;z<=z1;z+=.5){
      ray.set(new THREE.Vector3(x,75,z),new THREE.Vector3(0,-1,0));ray.far=70;
      const hits=ray.intersectObjects(targets,true);
      for(let i=0;i+1<hits.length;i++)if(hits[i].object.parent!==hits[i+1].object.parent){overlaps++;closest=Math.min(closest,Math.abs(hits[i].point.y-hits[i+1].point.y));}
    }
    assert.ok(overlaps>10,`${label}: overlapping zone is still sampled`);
    assert.ok(closest>=.0015,`${label}: surfaces ${closest.toFixed(4)} m apart flicker`);
  }
});
