import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {readModel} from './gltf-geometry.mjs';

// Decks, paving and stair landings below the Bitgaram slide used to share exactly the same height and flicker.
const zones=[[4,22,104,112],[-23,5,110,112],[5,16,107,112],[-25,-2,79,92]];
const surfaces=/^(context_roof_garden_paving|walk-floor_lower_station|walk-floor_access101_lower_(gallery|outdoor)|walk-floor_access101_turn_landings|walk-floor_outdoor_timber_stairs)$/;

test('overlapping decks, paving and stair landings never share one height',()=>{
  const {scene,gltf}=readModel(new URL('../public/models/bitgaram-park.glb',import.meta.url));
  assert.ok(gltf.extras?.coplanarDeckFix,'Separation script applied');
  const targets=[];scene.traverse(o=>{if(surfaces.test(o.name))targets.push(o);});
  assert.equal(targets.length,6);
  const ray=new THREE.Raycaster();let overlaps=0,closest=Infinity;
  for(const [x0,x1,z0,z1] of zones)for(let x=x0;x<=x1;x+=.5)for(let z=z0;z<=z1;z+=.5){
    ray.set(new THREE.Vector3(x,32,z),new THREE.Vector3(0,-1,0));ray.far=22;
    const hits=ray.intersectObjects(targets,true);
    for(let i=0;i+1<hits.length;i++)if(hits[i].object.parent!==hits[i+1].object.parent){overlaps++;closest=Math.min(closest,Math.abs(hits[i].point.y-hits[i+1].point.y));}
  }
  assert.ok(overlaps>100,'The overlapping zones are still sampled');
  assert.ok(closest>=.0015,`Surfaces ${closest.toFixed(4)} m apart flicker`);
});
