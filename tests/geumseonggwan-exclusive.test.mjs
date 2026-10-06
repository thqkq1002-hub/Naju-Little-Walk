import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {appDestinationFromSearch} from '../lib/app-destination.ts';
import {destinations} from '../lib/destinations.ts';
import {mapArrival,canTravelTo} from '../lib/map-navigation.ts';
import {moveOnFloors,worldFloors,worldObstacles,floorHeight} from '../lib/world.ts';
const world=JSON.parse(fs.readFileSync(new URL('../public/city-world.json',import.meta.url),'utf8'));
test('all regional and indoor deep links remain reachable while the default precinct is preserved',()=>{
  for(const id of Object.keys(destinations))assert.equal(appDestinationFromSearch('?place='+id),id);
  for(const search of ['', '?place=unknown','?place=__proto__'])assert.equal(appDestinationFromSearch(search),'geumseonggwan');
  assert.deepEqual(world.sceneLinks,[]);assert.deepEqual(world.portals,[]);
  const page=fs.readFileSync(new URL('../app/page.tsx',import.meta.url),'utf8');
  assert.ok(page.includes("selected==='bitgaram'?<BitgaramHub/>:<Explorer/>"));
  assert.ok(!page.includes("searchParams.delete('place')"));
});

test('every precinct destination has a safe local arrival including the elevated hall',()=>{
  for(const place of world.places){
    const p=mapArrival(place,world);assert.ok(p,place.id);
    assert.ok(canTravelTo(p,world,place.arrivalHeight??0),place.id);
  }
  const interior=world.places.find(p=>p.id==='interior');
  assert.ok(floorHeight(...mapArrival(interior,world),worldFloors(world.solids))>.9);
});
test('actual floor navigation climbs the five hall steps and returns to the courtyard',()=>{
  const floors=worldFloors(world.solids),obstacles=worldObstacles(world.solids);
  let p={x:world.spawn.x,z:world.spawn.z,height:0};
  for(const [x,z] of [...world.walkRoute.slice(1),...world.walkRoute.slice(0,-1).reverse()]){
    p=moveOnFloors(p.x,p.z,p.height,x-p.x,z-p.z,obstacles,floors,world.bounds,world.requireFloor);
    assert.ok(Math.hypot(p.x-x,p.z-z)<.04,`Blocked real floor route at ${x},${z}: ${JSON.stringify(p)}`);
  }
  assert.equal(p.height,0);
});
test('web asset embeds colored physical maps, detailed roofs and grouped architecture',()=>{
  const bytes=fs.readFileSync(new URL('../public/models/geumseonggwan.glb',import.meta.url));
  const gltf=JSON.parse(bytes.toString('utf8',20,20+bytes.readUInt32LE(12)));
  for(const name of ['v76_main_overlapping_barrel_tiles','v76_west_wing_barrel_tiles','v76_east_wing_barrel_tiles','v76_manghwaru_barrel_tiles','v76_middle_gate_barrel_tiles','v76_layered_tree_leaf_canopies'])assert.ok(gltf.nodes.some(n=>n.name===name),name);
  assert.ok(gltf.meshes.length<800,'Grouped architecture must not regress to thousands of objects');
  assert.ok(gltf.images.length>0&&gltf.images.every(i=>!i.uri&&i.bufferView!==undefined));
  const timber=gltf.materials.filter(m=>m.name.startsWith('Geum_v76_wood'));
  assert.ok(timber.length>0&&timber.some(m=>{const c=m.pbrMetallicRoughness?.baseColorFactor;return c&&c[0]>c[1]*1.2;}),'Wood must retain its warm tint when exporting textured material');
  assert.equal(gltf.nodes.some(n=>/^(context_|parking_|parked_|street_|road_|osm-building_)/.test(n.name)),false);
});
