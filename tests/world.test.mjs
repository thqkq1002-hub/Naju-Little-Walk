import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { hitsPolygon, movePlayer, moveOnFloors, reachableFloor, blocksWalking, worldObstacles, solidCollider, worldFloors, floorHeight, currentPlace } from '../lib/world.ts';
import { destinationFromSearch, destinations } from '../lib/destinations.ts';
import * as THREE from 'three';
import { batchStaticScene } from '../lib/static-scene.ts';
import { unpackModel } from '../lib/model-transport.ts';
import { sceneArrival,portalAt,portalHref } from '../lib/scene-travel.ts';
import { canTravelTo, mapArrival, mapSolids, regionalPoint, regionalSize } from '../lib/map-navigation.ts';
import { readModel } from './gltf-geometry.mjs';
import { mooredBoat, boatToWorld, worldToBoat, atBerth, canBoard, boatFitsWater, stepBoat, stepDeparture, polygonsOverlap } from '../lib/boat-navigation.ts';
import { BoatFleet } from '../lib/boat-fleet.ts';

const bogam=JSON.parse(fs.readFileSync(new URL('../public/bogam-world.json',import.meta.url),'utf8'));
const bogamColliders=bogam.solids.filter(s=>s.collision).map(solidCollider);
const museum=JSON.parse(fs.readFileSync(new URL('../public/bogam-museum-world.json',import.meta.url),'utf8'));
const museumFloors=worldFloors(museum.solids), museumObstacles=worldObstacles(museum.solids);

test('Bitgaram compressed downloads restore the exact authored Blender models',async()=>{
  for(const id of ['park','overview','observatory']){
    const raw=fs.readFileSync(new URL(`../public/models/bitgaram-${id}.glb`,import.meta.url));
    const packed=fs.readFileSync(new URL(`../public/models/bitgaram-${id}.glb.gz`,import.meta.url));
    const restored=await unpackModel(packed.buffer.slice(packed.byteOffset,packed.byteOffset+packed.byteLength));
    assert.ok(Buffer.from(restored).equals(raw));
    assert.ok(packed.length<raw.length,'Transport is smaller than the original');
  }
});

test('observatory uses an embedded panorama instead of the old exterior blocks',()=>{
  const raw=fs.readFileSync(new URL('../public/models/bitgaram-observatory.glb',import.meta.url));
  const gltf=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)).toString());
  const node=gltf.nodes.find(n=>n.extras?.photo_panorama);
  assert.ok(node,'Panorama is part of the 3D model');
  const material=gltf.materials[gltf.meshes[node.mesh].primitives[0].material];
  assert.ok(material.extensions?.KHR_materials_unlit || (material.emissiveTexture && material.emissiveFactor?.every(v=>v===1) && material.pbrMetallicRoughness?.baseColorFactor?.slice(0,3).every(v=>v===0)),'Photo exports as unlit or emission-only with a black surface');
  assert.ok(gltf.images.some(i=>i.bufferView!==undefined),'Panorama texture travels inside the GLB');
  assert.ok(!gltf.nodes.some(n=>/^(context_|lake_osm_|photo_wrap_)/.test(n.name??'')),'Old background geometry must not hide the panorama');
});

test('park aerial roof has an open oculus and physical supports block walking',()=>{
  const {scene}=readModel(new URL('../public/models/bitgaram-park.glb',import.meta.url));
  const roof=scene.getObjectByName('aerial_roof_open_oval');
  assert.ok(roof,'Detailed exterior roof is exported');
  assert.ok(!roof.userData.hide_in_overview,'Exterior roof stays visible in the aerial view');
  const downward=(x,z)=>new THREE.Raycaster(new THREE.Vector3(x,40,z),new THREE.Vector3(0,-1,0),0,8).intersectObject(roof,true);
  assert.equal(downward(-2,0).length,0,'Central oval opening remains open');
  assert.ok(downward(10,0).length,'Outer roof annulus covers the viewing room');
  const w=JSON.parse(fs.readFileSync(new URL('../public/bitgaram-park-world.json',import.meta.url),'utf8'));
  const columns=w.solids.filter(s=>s.name==='aerial_column_body');
  assert.equal(columns.length,6);
  for(const c of columns){
    const pts=solidCollider(c),x=pts.reduce((s,p)=>s+p[0],0)/pts.length,z=pts.reduce((s,p)=>s+p[1],0)/pts.length;
    assert.equal(canTravelTo([x,z],w,16),false,'Support must block visitors');
  }
  assert.equal(canTravelTo([0,5.8],w,16),false,'The glazed entrance drum is not a pass-through prop');
  walkRoute(w,[[0,21],[0,8]],16);
  const shell=w.solids.find(s=>s.name==='photo_exhibition_shell');
  assert.ok(shell&&shell.collision,'Exhibition shell retains a physical boundary');
});

test('Bitgaram slide gallery and monorail boundaries are physical and the roof garden stays open',()=>{
  const w=JSON.parse(fs.readFileSync(new URL('../public/bitgaram-park-world.json',import.meta.url),'utf8'));
  const names=['slide_gallery_outer_guard','stone_slide_safety_boundary','monorail_guideway_boundary'];
  const guards=w.solids.filter(s=>names.includes(s.name));
  assert.ok(guards.length>140);
  const obstacles=worldObstacles(w.solids);
  for(const guard of guards){
    const p=solidCollider(guard),x=p.reduce((s,a)=>s+a[0],0)/p.length,z=p.reduce((s,a)=>s+a[1],0)/p.length;
    assert.ok(blocksWalking(x,z,guard.position[1]+.05,obstacles));
  }
  const {scene}=readModel(new URL('../public/models/bitgaram-park.glb',import.meta.url));
  for(const name of names)assert.equal(scene.getObjectByName(name),undefined,'Collision proxies are not visible solid walls');
  const ray=new THREE.Raycaster(new THREE.Vector3(0,20,130),new THREE.Vector3(0,-1,0),0,15);
  assert.equal(ray.intersectObject(scene.getObjectByName('photo_exhibition_sloped_shell'),true).length,0,'Old closed roof removed');
  assert.ok(ray.intersectObject(scene.getObjectByName('context_roof_garden_paving'),true).length,'Roof terrace floor remains');
  const building=solidCollider(w.solids.find(s=>s.name==='photo_exhibition_shell'));
  scene.traverse(o=>{
    if(o.name.startsWith('aerial_woodland_canopy')){
      const p=o.getWorldPosition(new THREE.Vector3());
      assert.equal(hitsPolygon(p.x,p.z,building,0),false,'Woodland trunks must not emerge through the roof garden');
    }
  });
});

test('Bitgaram signs load valid scenes and preserve elevated park spawn',()=>{
  for(const id of ['bitgaram-park','bitgaram-observatory','bitgaram-kepco','bitgaram-kentech']){
    const w=JSON.parse(fs.readFileSync(new URL(`../public/${id}-world.json`,import.meta.url),'utf8'));
    const a=sceneArrival(w,'');
    assert.ok(canTravelTo([a.x,a.z],w,a.height),id);
    for(const link of w.sceneLinks) assert.ok(destinations[link.target],link.target);
    if(id==='bitgaram-park'){
      assert.equal(a.height,16);
      const access=JSON.parse(fs.readFileSync(new URL('../knowledge/sources/bitgaram/access-v69.json',import.meta.url)));
      const path=access.stairs_route.map(p=>[p[0],p[2]]);
      const end=walkRoute(w,[[a.x,a.z],[0,12],[path[0][0],12],...path],16);
      assert.ok(Math.abs(end.height-6.22)<.08,'Stairs reach the mapped lower exhibition terrace');
    } else if(id==='bitgaram-observatory'){
      // Empty room: former furniture and central core positions are now walkable.
      walkRoute(w,[[0,7],[6,7],[6,2],[10,0],[7,-8],[-5,-8],[-5,-4],[-10,0],[-6,0],[-6,7],[0,7]]);
      assert.equal(canTravelTo([8,4],w),true,'Removed bench must not leave an invisible collider');
      walkRoute(w,[[0,7],[0,0],[0,-7],[8,4]]);
      assert.equal(canTravelTo([12.85,0],w),false,'Inner guard contains visitors');
      assert.equal(canTravelTo([13.8,0],w),false,'Glazing must contain visitors');
    } else {
      const lobby=w.places.find(p=>p.id==='lobby').arrival;
      walkRoute(w,[[a.x,a.z],lobby,[a.x,a.z]]);
    }
  }
  const overview=JSON.parse(fs.readFileSync(new URL('../public/bitgaram-overview.json',import.meta.url),'utf8'));
  assert.equal(overview.pins.length,3);
  for(const p of overview.pins)assert.ok(p.x>0&&p.x<100&&p.y>0&&p.y<100,'Pin inside rendered map');
});

test('KEPCO overview retains the tower and the extended front courtyard connects to the lobby',()=>{
  const {scene}=readModel(new URL('../public/models/bitgaram-kepco.glb',import.meta.url));
  const tower=scene.getObjectByName('central_tower');
  assert.ok(tower&&!tower.userData.hide_in_overview,'Tower must remain visible in the outdoor overview');
  const w=JSON.parse(fs.readFileSync(new URL('../public/bitgaram-kepco-world.json',import.meta.url),'utf8'));
  const p=[w.spawn.x,w.spawn.z],lobby=w.places.find(p=>p.id==='lobby').arrival;
  walkRoute(w,[p,[p[0],p[1]+20],p,lobby,p]);
});

const yeongsanWorlds=Object.fromEntries(['yeongsanpo','yeongsanpo-history','yeongsanpo-literature'].map(id=>[id,JSON.parse(fs.readFileSync(new URL(`../public/${id}-world.json`,import.meta.url),'utf8'))]));
test('literature ceilings enclose the reported sky gaps and the stair landing',()=>{
  const {scene}=readModel(new URL('../public/models/yeongsanpo-literature.glb',import.meta.url));
  for(const [x,y,z] of [[-8.6,1.72,0],[-1.8,1.72,1.5],[-.4,1.72,-5],[-4,1.72,4.4],[-8.5,1.72,-8.93],[-2,5.08,-8.45],[-2,3.8,-5]]){
    const ray=new THREE.Raycaster(new THREE.Vector3(x,y,z),new THREE.Vector3(0,1,0),.01,8);
    assert.ok(ray.intersectObject(scene,true).length,`Sky leak above ${x},${y},${z}`);
  }
});
test('attic wall tops, corners and the floor beside the high windows are enclosed',()=>{
  const {scene}=readModel(new URL('../public/models/yeongsanpo-literature.glb',import.meta.url));
  for(const [origin,direction] of [
    [[-5.6,5.58,-3],[-1,0,0]],[[-5.6,5.58,-3],[1,0,0]],
    [[-5.6,5.58,-3],[0,0,-1]],[[-5.6,5.58,-3],[0,0,1]],
    [[-8.58,5.08,-8.53],[0,1,0]],[[-8.58,5.08,2.7],[0,1,0]],
  ])assert.ok(new THREE.Raycaster(new THREE.Vector3(...origin),new THREE.Vector3(...direction),.01,7).intersectObject(scene,true).length,`Open attic envelope ${origin} ${direction}`);
  for(const z of [-7,-3,1]){
    const hit=new THREE.Raycaster(new THREE.Vector3(-8.60,3.8,z),new THREE.Vector3(0,-1,0),.01,1).intersectObject(scene,true)[0];
    assert.ok(hit&&hit.point.y>=3.35,`Missing upper floor by window at ${z}`);
  }
});
test('detailed reading furniture leaves both side aisles and the stair route accessible',()=>{
  const w=yeongsanWorlds['yeongsanpo-literature'],a=sceneArrival(w,'?at=reading');
  assert.equal(a.entered,true);assert.equal(a.height,3.36);assert.ok(canTravelTo([a.x,a.z],w,a.height));
  walkRoute(w,[[-7.5,1.95],[-7.5,-7.9],[-4,-7.9],[-2,-8.45],[-4,-8.45],[-7.5,-8.45],[-7.5,1.95]],3.36);
  const chairs=w.solids.filter(s=>s.name==='attic_chair_collision');assert.equal(chairs.length,12);
  const p=chairs[0].footprint.reduce((sum,p)=>[sum[0]+p[0]/4,sum[1]+p[1]/4],[0,0]);
  assert.equal(blocksWalking(...p,3.36,worldObstacles(w.solids)),true);
});
test('gallery has seven staggered lightboxes, black mesh ceiling and enclosed food vitrines',()=>{
  const {gltf}=readModel(new URL('../public/models/yeongsanpo-history.glb',import.meta.url));
  assert.equal(gltf.nodes.filter(n=>/^timeline_lightbox_\d+$/.test(n.name)).length,7);
  for(const prefix of ['cutaway_ceiling_mesh','vitrine_glass_lid','onggi_straw_bundle','ceiling_projector'])assert.ok(gltf.nodes.some(n=>n.name.startsWith(prefix)),prefix);
});
test('ground-floor veranda closes the wall bands and frames a finite garden view',()=>{
  const {scene}=readModel(new URL('../public/models/yeongsanpo-literature.glb',import.meta.url));
  const surfaces=[];
  scene.traverse(o=>{if(/^(veranda_window_head_wall|veranda_transom_infill|window_garden_boundary_wall)/.test(o.name))surfaces.push(o);});
  for(const [origin,far] of [[[-6,2.95,7.2],1.9],[[6,2.82,4.8],1.2],[[-5.7,1.72,7.2],18.5]]){
    assert.ok(new THREE.Raycaster(new THREE.Vector3(...origin),new THREE.Vector3(0,0,1),.01,far).intersectObjects(surfaces,true).length,`Unfinished veranda view at ${origin}`);
  }
});
test('ground-floor display cases and sliding leaves block bodies but preserve three passages',()=>{
  const w=yeongsanWorlds['yeongsanpo-literature'],obstacles=worldObstacles(w.solids),floors=worldFloors(w.solids);
  for(const x of [-6,0,6])walkRoute(w,[[x,7.2],[x,5],[x,7.2]]);
  for(const x of [-7.5,-3,3,7.5]){
    const hit=moveOnFloors(x,7.2,0,0,-3,obstacles,floors,w.bounds,true);
    assert.ok(hit.z>6,`Walking through a sliding leaf at ${x}`);
  }
  for(const x of [2.7,4.8,6.9]){
    assert.ok(blocksWalking(x,-8.27,0,obstacles),'Book case must block the visitor');
    assert.equal(canTravelTo([x,-8.27],w),false,'Map must not place a visitor inside a case');
  }
  const hit=moveOnFloors(-5.7,7.2,0,0,5,obstacles,floors,w.bounds,true);
  assert.ok(hit.z<8.8,'Garden-facing glazing must stop a visitor');
  assert.equal(canTravelTo([0,12],w),false,'Window garden is outside this interior map');
});
test('ground exhibition and veranda arrivals connect to the original exit',()=>{
  const w=yeongsanWorlds['yeongsanpo-literature'];
  for(const id of ['exhibit','veranda']){
    const a=sceneArrival(w,'?at='+id);assert.ok(a.entered&&a.height===0&&canTravelTo([a.x,a.z],w));
  }
  const a=w.arrivals.exhibit;
  const route=[[a.x,a.z],[6,7.2],[-5.7,7.2],[-6,5],[-6,7.2],[0,7.2],[0,9.65]];
  const end=walkRoute(w,route);assert.equal(portalAt(w,end.x,end.z,end.height)?.target,'yeongsanpo');
});
const testBoat={id:'test',name:'Test',home:{x:0,z:0,yaw:0},length:12,beam:4,hull:[[-2,-6],[2,-6],[2,6],[-2,6]],shore:[3,0],shoreHeight:0};
const openWater={polygons:[[[-50,-80],[50,-80],[50,80],[-50,80]]],obstacles:[]};
test('boat local coordinates and boarding remain correct after rotation and translation',()=>{
  const state={...mooredBoat(testBoat),x:19,z:-27,yaw:1.23};
  for(const point of [[0,0],[2,-6],[-1.3,4.2]]){
    const p=worldToBoat(boatToWorld(point,state),state);assert.ok(Math.hypot(p[0]-point[0],p[1]-point[1])<1e-10);
  }
  assert.equal(canBoard([3,0],0,mooredBoat(testBoat),testBoat),true);
  assert.equal(canBoard([3,0],6,mooredBoat(testBoat),testBoat),false);
  assert.equal(atBerth({...mooredBoat(testBoat),speed:1},testBoat),false);
  assert.equal(atBerth({...mooredBoat(testBoat),x:2},testBoat),false);
});
test('boat accelerates, turns, brakes and reverses while its hull remains in the river',()=>{
  let state=mooredBoat(testBoat);
  for(let i=0;i<100;i++)state=stepBoat(state,testBoat,{throttle:1,steer:.5,brake:false},.05,openWater,[]);
  assert.ok(state.speed>2&&state.z< -5&&state.yaw<-.1);
  const speed=state.speed;
  for(let i=0;i<20;i++)state=stepBoat(state,testBoat,{throttle:0,steer:0,brake:true},.05,openWater,[]);
  assert.ok(state.speed<speed*.02);
  for(let i=0;i<70;i++)state=stepBoat(state,testBoat,{throttle:-1,steer:0,brake:false},.05,openWater,[]);
  assert.ok(state.speed< -1);
});
test('swept hull movement stops before a thin obstacle and other boats, including edge crossings',()=>{
  const obstacle=[[-40,-12.05],[40,-12.05],[40,-12],[-40,-12]];
  let state={...mooredBoat(testBoat),speed:4.1};
  for(let i=0;i<30;i++)state=stepBoat(state,testBoat,{throttle:1,steer:0,brake:false},.25,{...openWater,obstacles:[obstacle]},[]);
  assert.equal(state.blocked,true);assert.ok(state.z>=-6);assert.equal(state.speed,0);
  assert.equal(polygonsOverlap([[-5,-1],[5,-1],[5,1],[-5,1]],[[-1,-5],[1,-5],[1,5],[-1,5]]),true);
  const other={definition:testBoat,state:{...mooredBoat(testBoat),id:'other',z:-11}};
  assert.equal(boatFitsWater(mooredBoat(testBoat),testBoat,openWater,[other]),false);
  assert.equal(boatFitsWater({...mooredBoat(testBoat),x:49},testBoat,openWater,[]),false);
  const huge=stepBoat(mooredBoat(testBoat),testBoat,{throttle:1,steer:0,brake:false},100,openWater,[]);
  assert.ok(Math.abs(huge.z)<.1,'A resumed tab must not simulate an unbounded time jump');
});
test('both authored boats board from safe dock arrivals and have walkable cabins and stern decks',()=>{
  const outdoor=yeongsanWorlds.yeongsanpo;assert.equal(outdoor.boats.length,2);
  const wang=outdoor.boats.find(b=>b.id==='wanggeonho');assert.equal(wang.length,29.9);assert.equal(wang.beam,9.9);
  for(const b of outdoor.boats){
    const state=mooredBoat(b);assert.ok(canTravelTo(b.shore,outdoor,b.shoreHeight),b.id+' shore arrival');
    assert.ok(canBoard(b.shore,b.shoreHeight,state,b));
    assert.equal(sceneArrival(outdoor,'?at=board-'+b.id).entered,true);
    assert.ok(boatFitsWater(state,b,outdoor.navigationWater,outdoor.boats.map(definition=>({definition,state:mooredBoat(definition)}))),b.id+' initial hull');
    const local={title:b.name,bounds:[-b.beam/2,b.beam/2,-b.length/2,b.length/2],solids:b.solids,requireFloor:true};
    for(const route of [b.walkRoute,b.exploreRoute])walkRoute(local,[...route,...route.slice(0,-1).reverse()],b.deckHeight);
    const p=moveOnFloors(...b.boarding,b.deckHeight,100,0,worldObstacles(b.solids),worldFloors(b.solids),local.bounds,true);
    assert.ok(p.x<b.beam/2,'A passenger cannot walk off the deck into water');
  }
});
test('boat cabin GLBs enclose overhead surfaces and embed complete compressed assets',async()=>{
  for(const b of yeongsanWorlds.yeongsanpo.boats){
    const path=new URL('../public/models/'+b.id+'.glb',import.meta.url),raw=fs.readFileSync(path);
    const compressed=fs.readFileSync(new URL('../public/models/'+b.id+'.glb.gz',import.meta.url));
    assert.deepEqual(Buffer.from(await unpackModel(compressed.buffer.slice(compressed.byteOffset,compressed.byteOffset+compressed.byteLength))),raw);
    const {scene,gltf}=readModel(path);assert.match(gltf.asset.generator,/Blender/);
    const hit=new THREE.Raycaster(new THREE.Vector3(b.helm[0],b.deckHeight+1.72,b.helm[1]),new THREE.Vector3(0,1,0),.01,4).intersectObject(scene,true)[0];
    assert.ok(hit&&hit.point.y-b.deckHeight>=2.29,b.id+' helm headroom');
    assert.ok(gltf.images.every(i=>i.bufferView!==undefined&&!i.uri));
  }
});
test('both full-size hulls cast off and can steer away from the wharf',()=>{
  const w=yeongsanWorlds.yeongsanpo;
  for(const b of w.boats){
    let state=mooredBoat(b);const others=w.boats.map(definition=>({definition,state:mooredBoat(definition)}));
    for(let i=0;i<100;i++)state=stepDeparture(state,b,b.length*.25/100,w.navigationWater,others);
    assert.equal(state.blocked,false,b.id+' cast off');
    for(let i=0;i<220;i++)state=stepBoat(state,b,{throttle:1,steer:i<130?-1:0,brake:false},.05,w.navigationWater,others);
    assert.equal(state.blocked,false,b.id+' departure turn');
    assert.ok(Math.hypot(state.x-b.home.x,state.z-b.home.z)>25,b.id+' leaves berth');
  }
});
test('fleet modes stop motion on pause, retain passengers on deck and disembark only at berth',()=>{
  const w=yeongsanWorlds.yeongsanpo,fleet=new BoatFleet(w);
  fleet.vessels=w.boats.map(definition=>({definition,state:mooredBoat(definition),object:new THREE.Group(),floors:worldFloors(definition.solids),obstacles:worldObstacles(definition.solids)}));
  const b=w.boats[0];assert.equal(fleet.board(b.id,b.shore,b.shoreHeight),true);
  fleet.drive();assert.ok(fleet.passenger.departure>0);
  for(let i=0;i<100;i++)fleet.update(.05,new Set(),b.home.yaw);
  for(let i=0;i<40;i++)fleet.update(.05,new Set(['KeyW']),b.home.yaw);
  assert.equal(fleet.leave(),null,'No disembarkation in open water');
  assert.ok(fleet.eye().height<0&&fleet.eye().height> -7.47);
  fleet.stop();assert.equal(fleet.passenger.vessel.state.speed,0);assert.equal(fleet.passenger.departure,0);
  const anchor={...fleet.passenger.vessel.state};fleet.deck();fleet.update(.05,new Set(['KeyW']),b.home.yaw);
  assert.equal(fleet.passenger.helm,false);assert.deepEqual(fleet.passenger.vessel.state,anchor);
  fleet.returnToBerth();assert.equal(fleet.hud(b.shore,b.shoreHeight).canLeave,true);
  assert.deepEqual(fleet.leave().position,b.shore);assert.equal(fleet.passenger,null);
  const other=w.boats[1];assert.equal(fleet.board(other.id,other.shore,other.shoreHeight),true);
  fleet.drive();fleet.update(.05,new Set(),other.home.yaw);fleet.leaveForTravel();
  assert.equal(fleet.passenger,null);assert.equal(atBerth(fleet.vessels[1].state,other),true);
});
function walkRoute(world,route,height=0){
  const floors=worldFloors(world.solids),obstacles=worldObstacles(world.solids);
  let p={x:route[0][0],z:route[0][1],height};
  for(const [x,z] of route.slice(1)){
    p=moveOnFloors(p.x,p.z,p.height,x-p.x,z-p.z,obstacles,floors,world.bounds,world.requireFloor);
    assert.ok(Math.hypot(p.x-x,p.z-z)<.06,`Blocked ${world.subtitle} waypoint ${x},${z}: ${JSON.stringify(p)}`);
  }
  return p;
}

test('museum doors enter separate scenes and return to safe street arrivals without loops',()=>{
  const outdoor=yeongsanWorlds.yeongsanpo;
  for(const portal of outdoor.portals){
    const inside=yeongsanWorlds[portal.target],href=portalHref(portal);
    assert.equal(destinationFromSearch(href.split('?')[1]),portal.target);
    const arrival=sceneArrival(inside,href.split('?')[1]);assert.equal(arrival.entered,true);
    assert.equal(portalAt(inside,arrival.x,arrival.z),undefined);
    const exit=inside.portals[0];const back=sceneArrival(outdoor,portalHref(exit).split('?')[1]);
    assert.equal(back.entered,true);assert.equal(portalAt(outdoor,back.x,back.z),undefined);
    walkRoute(outdoor,[[back.x,back.z],portal.position]);
    assert.equal(portalAt(outdoor,...portal.position)?.target,portal.target);
    assert.equal(portalAt(outdoor,...portal.position,5),undefined);
  }
  assert.equal(portalHref({...outdoor.portals[0],target:'https://example.com'}),null);
  assert.equal(sceneArrival(outdoor,'?at=__proto__').entered,false);
});

test('history gallery visitors can circle the exhibits and leave through the original door',()=>{
  const world=yeongsanWorlds['yeongsanpo-history'];const end=walkRoute(world,world.walkRoute);
  assert.equal(portalAt(world,end.x,end.z,end.height)?.target,'yeongsanpo');
});

test('literature museum stairs reach the attic and return without walking inside the steps',()=>{
  const world=yeongsanWorlds['yeongsanpo-literature'];
  const route=[[0,7.3],[6,7.3],[6,4],[4,0],[4,-3.5],[0,-3.5],[-.6,-3.5],[-.6,-1.8],[-2,-1.8],[-2,-8.45],[-4,-8.45],[-7.5,-8.45],[-7.5,-4]];
  const top=walkRoute(world,route);assert.ok(Math.abs(top.height-3.36)<.03);
  const back=walkRoute(world,[...route].reverse(),top.height);assert.ok(Math.abs(back.height)<.04);
  const side=moveOnFloors(-3.3,-6,0,1.3,0,worldObstacles(world.solids),worldFloors(world.solids),world.bounds);
  assert.ok(side.x<-3.08,'The side of a tall step must stop a ground-level visitor');
});

test('Yeongsanpo river blocks walking while street and lower wharf stairs stay connected',()=>{
  const world=yeongsanWorlds.yeongsanpo;
  assert.equal(canTravelTo([-170,-50],world),false,'Open water is not a ground floor');
  const route=world.dockStairRoute;const lower=walkRoute(world,route);assert.ok(Math.abs(lower.height-world.dockHeight)<.03);
  const back=walkRoute(world,[...route].reverse(),lower.height);assert.ok(Math.abs(back.height)<.03);
  const road=world.roads.find(r=>r.id==='way/729505193');
  const section=road.points.filter(p=>p[0]>-205&&p[0]<0);
  walkRoute(world,section);
  for(const place of world.places)assert.ok(mapArrival(place,world),`No map arrival for ${place.name}`);
});

test('three new Blender scenes have standalone buffers and exact compressed transport',async()=>{
  for(const id of Object.keys(yeongsanWorlds)){
    const raw=fs.readFileSync(new URL(`../public/models/${id}.glb`,import.meta.url));
    const zipped=fs.readFileSync(new URL(`../public/models/${id}.glb.gz`,import.meta.url));
    const restored=await unpackModel(zipped.buffer.slice(zipped.byteOffset,zipped.byteOffset+zipped.byteLength));
    assert.deepEqual(Buffer.from(restored),raw);assert.ok(zipped.length<26214400);
    const json=JSON.parse(raw.toString('utf8',20,20+raw.readUInt32LE(12)));
    assert.match(json.asset.generator,/Blender/);assert.ok(json.buffers.every(b=>!b.uri));
    assert.ok(json.nodes.some(n=>n.name?.startsWith(id==='yeongsanpo'?'yeongsanpo_lighthouse':id.endsWith('history')?'boat_white_sail_screen':'attic_white_bookshelf')));
    if(id==='yeongsanpo')assert.equal(json.nodes.some(n=>n.extras?.hide_in_overview),false,'Exterior roofs remain visible in the regional overview');
  }
});

test('one outdoor walk connects the riverfront, Hong-eo street and both museum doorways',()=>{
  const w=yeongsanWorlds.yeongsanpo,h=w.arrivals['history-exit'],l=w.arrivals['literature-exit'];
  const hp=w.portals.find(p=>p.id==='history-entry').position,lp=w.portals.find(p=>p.id==='literature-entry').position;
  walkRoute(w,[[w.spawn.x,w.spawn.z],[-50.189387567,105.687208],[-39.13,99.49],[-33.02,117.14],[83.828313937,35.076932],[h.x,h.z],hp,[h.x,h.z],[83.828313937,35.076932],[-33.02,117.14],[-26.57,135.69],[52.16,117.63],...w.literatureGarden.approach,...w.literatureGarden.walkRoute.slice(1),[l.x,l.z],lp]);
});

test('courtyard entry follows the west lane and returns past the planted beds',()=>{
  const w=yeongsanWorlds.yeongsanpo,route=[...w.literatureGarden.approach,...w.literatureGarden.walkRoute.slice(1)];
  walkRoute(w,[...route,...route.slice(0,-1).reverse()]);
  const arrival=sceneArrival(w,'?at=literature-garden');
  assert.equal(arrival.entered,true);assert.ok(canTravelTo([arrival.x,arrival.z],w));
  assert.equal(portalAt(w,arrival.x,arrival.z),undefined);
  const obstacles=worldObstacles(w.solids);
  for(const rock of w.solids.filter(s=>s.name==='garden_boulder_collision')){
    const p=rock.footprint.reduce((a,p)=>[a[0]+p[0]/4,a[1]+p[1]/4],[0,0]);
    assert.ok(blocksWalking(...p,0,obstacles),'Garden rocks must not be walk-through decorations');
  }
});

test('museum boundary blocks crossing and map placement while the open entrance connects both ways',()=>{
  const w=yeongsanWorlds.yeongsanpo,e=w.literatureGarden.enclosure;
  const barriers=w.solids.filter(s=>s.name==='hall-wall_literature_boundary');
  assert.equal(barriers.length,e.segments.length);
  assert.equal(mapSolids(w).filter(s=>s.name==='hall-wall_literature_boundary').length,barriers.length);
  for(const s of barriers){
    const poly=solidCollider(s),p=poly.reduce((a,p)=>[a[0]+p[0]/poly.length,a[1]+p[1]/poly.length],[0,0]);
    assert.equal(canTravelTo(p,w),false,'The map cannot jump into a fence');
  }
  const route=[...w.literatureGarden.approach,...w.literatureGarden.walkRoute.slice(1)];
  walkRoute(w,[...route,...route.slice(0,-1).reverse()]);
  const {center,angle}=w.literatureGarden;
  const pt=(x,z)=>[center[0]+x*Math.cos(angle)-z*Math.sin(angle),center[1]+x*Math.sin(angle)+z*Math.cos(angle)];
  const a=pt(-14,29),b=pt(-20,29);
  const hit=moveOnFloors(...a,0,b[0]-a[0],b[1]-a[1],worldObstacles(w.solids),worldFloors(w.solids),w.bounds,true);
  assert.ok(Math.hypot(hit.x-b[0],hit.z-b[1])>2,'Walking must stop at the timber boundary');
});

test('side return remains reachable without crossing the new annex or a column',()=>{
  const w=yeongsanWorlds.yeongsanpo,route=w.literatureGarden.enclosure.sideRoute;
  walkRoute(w,[...route,...route.slice(0,-1).reverse()]);
  const arrival=sceneArrival(w,'?at=literature-side');assert.ok(arrival.entered&&canTravelTo([arrival.x,arrival.z],w));
  const annex=w.solids.find(s=>s.name==='photo-building_literature_service_annex');
  const p=solidCollider(annex).reduce((a,p)=>[a[0]+p[0]/4,a[1]+p[1]/4],[0,0]);
  assert.equal(canTravelTo(p,w),false);
  const deck=w.solids.find(s=>s.name==='exhibit-case_literature_wing_deck');
  const deckCenter=solidCollider(deck).reduce((a,p)=>[a[0]+p[0]/4,a[1]+p[1]/4],[0,0]);
  assert.ok(blocksWalking(...deckCenter,0,worldObstacles(w.solids)),'The solid low deck must not be walk-through');
  assert.equal(canTravelTo(deckCenter,w),false);
});

test('exported museum gable and clerestory close the previously floating roof sides',()=>{
  const w=yeongsanWorlds.yeongsanpo,{scene}=readModel(new URL('../public/models/yeongsanpo.glb',import.meta.url));
  const {center,angle}=w.literatureGarden;
  const point=([x,y,z])=>new THREE.Vector3(center[0]+x*Math.cos(angle)-z*Math.sin(angle),y,center[1]+x*Math.sin(angle)+z*Math.cos(angle));
  const direction=([x,y,z])=>new THREE.Vector3(x*Math.cos(angle)-z*Math.sin(angle),y,x*Math.sin(angle)+z*Math.cos(angle));
  const envelope=[];scene.traverse(o=>{if(/^literature_(sealed_upper_gable|closed_side_clerestory|clerestory_closed_wall)/.test(o.name))envelope.push(o);});
  for(const [origin,dir] of [[[8,6,-.8],[1,0,0]],[[8,4.45,0],[1,0,0]],[[1,4.45,-5.8],[0,0,-1]]]){
    assert.ok(new THREE.Raycaster(point(origin),direction(dir),.01,4).intersectObjects(envelope,true).length,`Unclosed roof side ${origin}`);
  }
});

test('traced context walls preserve the observed footprints and are included on the map',()=>{
  const w=yeongsanWorlds.yeongsanpo;
  const refs=['literature-context-traces','literature-close-neighbours'].flatMap(id=>JSON.parse(fs.readFileSync(new URL('../knowledge/sources/'+id+'.json',import.meta.url),'utf8')).roofs).filter(r=>!r.reviewFlags?.length);
  assert.equal(w.southContextRoofs,refs.length);
  for(const roof of refs){
    const wall=w.solids.find(s=>s.name==='photo-building_south_'+roof.id);
    assert.ok(wall?.collision&&mapSolids(w).includes(wall));
    for(const p of wall.footprint)assert.ok(hitsPolygon(...p,roof.worldFootprint,0),roof.id+' wall inside eaves');
  }
});

test('riverfront frontage keeps satellite footprints and exposes glazing toward the river',()=>{
  const w=yeongsanWorlds.yeongsanpo,{scene}=readModel(new URL('../public/models/yeongsanpo.glb',import.meta.url));
  const refs=JSON.parse(fs.readFileSync(new URL('../knowledge/sources/yeongsanpo-traced-roofs.json',import.meta.url),'utf8')).roofs;
  const xy=([lon,lat])=>[(lon-w.origin.lon)*111320*Math.cos(w.origin.lat*Math.PI/180),(w.origin.lat-lat)*111320];
  assert.equal(w.riverfrontDetails.revision,'riverfront-1');
  assert.equal(w.riverfrontDetails.buildings.length,20);
  for(const b of w.riverfrontDetails.buildings){
    const wall=w.solids.find(s=>s.name==='photo-building_riverfront_'+b.id);
    assert.ok(wall?.collision&&mapSolids(w).includes(wall),b.id);
    const original=refs.find(r=>r.id===b.id).footprint.map(xy);
    assert.deepEqual(wall.footprint,original,'Detailed walls must not move the observed footprint');
    if(b.facade!=='shop')continue;
    const normal=new THREE.Vector3(b.normal[0]-b.front[0],0,b.normal[1]-b.front[1]);
    assert.ok(normal.z<-.5,'Frontage must face the river, not its rear alley');
    const windows=[];scene.traverse(o=>{if(o.name.startsWith('riverfront_'+b.id+'_shop_pane'))windows.push(o);});
    assert.ok(windows.length,b.id+' has no visible window');
    const center=new THREE.Box3().setFromObject(windows[0],true).getCenter(new THREE.Vector3());
    const hit=new THREE.Raycaster(center.clone().addScaledVector(normal,2),normal.clone().negate(),.01,2.1).intersectObjects(windows,true)[0];
    assert.ok(hit,b.id+' glazing faces inward or is absent from the GLB');
  }
});

test('the restored frontage paving connects the river walk and rear lane in both directions',()=>{
  const w=yeongsanWorlds.yeongsanpo;
  const path=w.riverfrontDetails.paving.accessRoute;
  walkRoute(w,[...path,...path.slice(0,-1).reverse()]);
  const arrival=sceneArrival(w,'?at=riverfront-shops');
  assert.ok(arrival.entered&&canTravelTo([arrival.x,arrival.z],w));
  walkRoute(w,[[w.spawn.x,w.spawn.z],[arrival.x,arrival.z],path[3]]);
  const surface=w.solids.find(s=>s.name==='walk-floor_riverfront_parking_apron');
  assert.ok(surface&&mapSolids(w).includes(surface));
  const {scene}=readModel(new URL('../public/models/yeongsanpo.glb',import.meta.url));
  const mesh=scene.getObjectByName('walk-floor_riverfront_parking_apron');
  for(const [x,z] of path){
    assert.ok(hitsPolygon(x,z,solidCollider(surface),.001));
    const hit=new THREE.Raycaster(new THREE.Vector3(x,1,z),new THREE.Vector3(0,-1,0),.01,2).intersectObject(mesh,true)[0];
    assert.ok(hit&&Math.abs(hit.point.y-surface.position[1]-surface.size[1])<.002,'Frontage floor/GLB height differs');
  }
});

test('riverfront roofs gain real pitch while domestic walls and parked cars block walking',()=>{
  const w=yeongsanWorlds.yeongsanpo,{scene}=readModel(new URL('../public/models/yeongsanpo.glb',import.meta.url));
  for(const b of w.riverfrontDetails.buildings.filter(b=>b.roofType!=='flat')){
    const mesh=scene.getObjectByName('riverfront_pitched_roof_'+b.id);
    assert.ok(mesh,b.id+' roof missing');
    const box=new THREE.Box3().setFromObject(mesh,true);
    assert.ok(box.min.y>=b.height+.14&&box.max.y>b.height+.7,b.id+' must have closed pitched geometry above the walls');
  }
  const obstacles=worldObstacles(w.solids);
  for(const s of w.solids.filter(s=>s.name==='hall-wall_riverfront_house_front'||s.name==='riverfront_parked_car_body'||s.name.startsWith('exhibit-case_riverfront_external_stair'))){
    const p=solidCollider(s).reduce((a,p)=>[a[0]+p[0]/4,a[1]+p[1]/4],[0,0]);
    assert.ok(blocksWalking(...p,0,obstacles)&&!canTravelTo(p,w),'Wall or car is walk-through');
  }
  for(const s of w.solids.filter(s=>s.name.startsWith('osm-building_way_1120464648'))){
    assert.ok(s.position[1]+s.size[1]<=4.5,'The duplicate OSM shell must not protrude through the low roof');
  }
});

test('additional satellite roofs remain inside observed eaves and block walking',()=>{
  const w=yeongsanWorlds.yeongsanpo;
  const refs=JSON.parse(fs.readFileSync(new URL('../knowledge/sources/yeongsanpo-round2-roofs.json',import.meta.url),'utf8')).roofs.filter(r=>!r.reviewFlags?.length);
  assert.equal(w.additionalSatelliteRoofs,refs.length);
  const obstacles=worldObstacles(w.solids);
  for(const roof of refs){
    const wall=w.solids.find(s=>s.name==='photo-building_round2_'+roof.id);
    assert.ok(wall?.collision&&mapSolids(w).includes(wall));
    for(const p of wall.footprint)assert.ok(hitsPolygon(...p,roof.worldFootprint,0),roof.id+' wall outside traced eaves');
    const p=wall.footprint[0],q=wall.footprint[1],mid=[(p[0]+q[0])/2,(p[1]+q[1])/2];
    assert.ok(blocksWalking(...mid,0,obstacles),roof.id+' walk-through facade');
  }
});

test('street paving exports visible surfaces at the collision floor elevation',()=>{
  const w=yeongsanWorlds.yeongsanpo,{scene}=readModel(new URL('../public/models/yeongsanpo.glb',import.meta.url));
  const paving=w.solids.filter(s=>s.name==='walk-floor_street_pavers');assert.ok(paving.length>100);
  const meshes=[];scene.traverse(o=>{if(o.name.startsWith('walk-floor_street_pavers'))meshes.push(o);});
  for(const s of paving.filter((_,i)=>i%29===0)){
    const p=s.footprint.reduce((sum,p)=>[sum[0]+p[0]/4,sum[1]+p[1]/4],[0,0]);
    const top=s.position[1]+s.size[1];
    const hit=new THREE.Raycaster(new THREE.Vector3(p[0],1,p[1]),new THREE.Vector3(0,-1,0),.01,2).intersectObjects(meshes,true)[0];
    assert.ok(hit&&Math.abs(hit.point.y-top)<.003,'Visual and navigable paving disagree');
  }
});

test('satellite alley connections remain walkable past the added building walls',()=>{
  const w=yeongsanWorlds.yeongsanpo;
  assert.equal(w.additionalLanes.length,4);
  for(const lane of w.additionalLanes)walkRoute(w,[...lane.points,...lane.points.slice(0,-1).reverse()]);
  for(const name of ['west-lanes','jukjeon-alley']){
    const a=sceneArrival(w,'?at='+name);assert.equal(a.entered,true);
    assert.ok(canTravelTo([a.x,a.z],w),name+' arrival inside an obstacle');
  }
});

test('the bend in the garden paving has a continuous visible outer corner',()=>{
  const w=yeongsanWorlds.yeongsanpo,{scene}=readModel(new URL('../public/models/yeongsanpo.glb',import.meta.url));
  const paths=[];scene.traverse(o=>{if(o.name.startsWith('path_literature_garden'))paths.push(o);});
  const {center,angle}=w.literatureGarden;
  for(const [x,z] of [[0,30],[.96,30.23],[.88,30.36],[-.8,29.4]]){
    const px=center[0]+x*Math.cos(angle)-z*Math.sin(angle),pz=center[1]+x*Math.sin(angle)+z*Math.cos(angle);
    assert.ok(new THREE.Raycaster(new THREE.Vector3(px,1,pz),new THREE.Vector3(0,-1,0),.01,2).intersectObjects(paths,true).length,`Paving gap at ${x},${z}`);
  }
});

test('museum bridge bends have walkable outer corners and continuous edge guards',()=>{
  const frame=JSON.parse(fs.readFileSync(new URL('../knowledge/sources/bogam-museum-hall-frame.json',import.meta.url),'utf8')).hallFrame;
  const local=(x,z)=>[frame.center[0]+frame.u[0]*x+frame.v[0]*z,frame.center[1]+frame.u[1]*x+frame.v[1]*z];
  for(const point of [[-22.05,-19.55],[-6.15,-19.55],[-7.25,-3.25],[21.25,-4.35]]){
    const [x,z]=local(...point);
    assert.ok(Math.abs(reachableFloor(x,z,museum.bridgeHeight,museumFloors)-museum.bridgeHeight)<.001,`Missing corner floor ${point}`);
    assert.equal(blocksWalking(x,z,museum.bridgeHeight,museumObstacles),false,`Corner passage blocked ${point}`);
  }
  const route=[[-21.5,-18.3],[-22.05,-19.55],[-20.8,-19]].map(p=>local(...p));
  let p={x:route[0][0],z:route[0][1],height:museum.bridgeHeight};
  for(const [x,z] of [...route.slice(1),...route.slice(0,-1).reverse()]){
    p=moveOnFloors(p.x,p.z,p.height,x-p.x,z-p.z,museumObstacles,museumFloors,museum.bounds);
    assert.ok(Math.hypot(p.x-x,p.z-z)<.05,`Cannot walk around finished corner: ${JSON.stringify(p)}`);
  }
  for(const point of [[-22.54,-19.55],[-22.05,-20.04],[-6.15,-20.04],[-5.66,-19.55],[-7.74,-3.25],[-7.25,-2.76],[21.74,-4.35],[21.25,-4.84],[20.7,17.74]]){
    assert.equal(blocksWalking(...local(...point),museum.bridgeHeight,museumObstacles),true,`Missing edge guard ${point}`);
  }
});

test('museum lower lobby does not snap to the cafe above, and the stairs reach the full bridge circuit',()=>{
  let p={x:museum.spawn.x,z:museum.spawn.z,height:.12};
  assert.equal(reachableFloor(p.x,p.z,0,museumFloors),.12);
  assert.ok(floorHeight(p.x,p.z,museumFloors)>3,'This spot actually has an upper cafe floor');
  for(const [x,z] of museum.walkRoute.slice(1)){
    p=moveOnFloors(p.x,p.z,p.height,x-p.x,z-p.z,museumObstacles,museumFloors,museum.bounds);
    assert.ok(Math.hypot(p.x-x,p.z-z)<.05,`Blocked museum route ${x},${z}: ${JSON.stringify(p)}`);
  }
  assert.ok(Math.abs(p.height-museum.bridgeHeight)<.001,'Stairs must physically raise the visitor to the bridge');
  for(const [x,z] of museum.walkRoute.slice(0,-1).reverse()){
    p=moveOnFloors(p.x,p.z,p.height,x-p.x,z-p.z,museumObstacles,museumFloors,museum.bounds);
    assert.ok(Math.hypot(p.x-x,p.z-z)<.05,`Blocked return from museum bridge ${x},${z}: ${JSON.stringify(p)}`);
  }
  assert.ok(Math.abs(p.height-.12)<.001);
});

test('upper floors reject large drops and museum map jumps use the selected viewing level',()=>{
  const bridge=museum.places.find(p=>p.id==='bridge');
  const p=mapArrival(bridge,museum);
  assert.ok(canTravelTo(p,museum,bridge.arrivalHeight));
  assert.equal(canTravelTo(p,museum,0),false,'Ground inside the replica cannot be used as a shortcut');
  assert.equal(blocksWalking(...p,bridge.arrivalHeight,museumObstacles),false);
  const platform={polygon:[[-2,-2],[2,-2],[2,2],[-2,2]],height:3.5};
  const stopped=moveOnFloors(0,0,3.5,8,0,[],[platform],[-20,20,-20,20]);
  assert.ok(stopped.x<=2,'Upper-floor edge cannot cause an instant fall');
});

test('cafe staircase connects the lower lobby to the reading area and returns beneath the same floor',()=>{
  const frame=JSON.parse(fs.readFileSync(new URL('../knowledge/sources/bogam-museum-hall-frame.json',import.meta.url),'utf8')).hallFrame;
  const local=(x,z)=>[frame.center[0]+frame.u[0]*x+frame.v[0]*z,frame.center[1]+frame.u[1]*x+frame.v[1]*z];
  const route=[[-16,52],[-24.2,52],[-30,56.35],[-34,56.35],...museum.stairs.cafe.map(p=>[p[0],p[1]]),[-34,48.3],[-31.5,48.3],[-15,47.5]].map(p=>local(...p));
  let p={x:route[0][0],z:route[0][1],height:.12};
  for(const [x,z] of route.slice(1)){
    p=moveOnFloors(p.x,p.z,p.height,x-p.x,z-p.z,museumObstacles,museumFloors,museum.bounds);
    assert.ok(Math.hypot(p.x-x,p.z-z)<.05,`Blocked cafe route ${x},${z}: ${JSON.stringify(p)}`);
  }
  assert.ok(Math.abs(p.height-museum.bridgeHeight)<.001);
  assert.equal(currentPlace(p.x,p.z,museum.places,p.height)?.id,'cafe');
  for(const [x,z] of route.slice(0,-1).reverse()){
    p=moveOnFloors(p.x,p.z,p.height,x-p.x,z-p.z,museumObstacles,museumFloors,museum.bounds);
    assert.ok(Math.hypot(p.x-x,p.z-z)<.05);
  }
  assert.ok(Math.abs(p.height-.12)<.001);
});

test('museum GLB includes the observed interior, 41 traced facilities, 22 jar burials and 38 theatre seats',()=>{
  assert.equal(destinationFromSearch('?place=bogam-museum'),'bogam-museum');
  assert.equal(museum.burials.length,41);
  assert.equal(museum.burials.filter(b=>b.category==='jar_coffin').length,22);
  assert.equal(museum.burials.filter(b=>b.category==='stone_burial').length,18);
  const buffer=fs.readFileSync(new URL('../public/models/bogam-museum.glb',import.meta.url));
  assert.equal(buffer.readUInt32LE(8),buffer.length);
  const gltf=JSON.parse(buffer.toString('utf8',20,20+buffer.readUInt32LE(12)));
  assert.match(gltf.asset.generator,/Blender/);
  for(const name of ['replica_excavation_surface','pottery_case_glass','walk-floor_bridge_0','cutaway_main_roof','cutaway_visitor_roof','theatre_screen'])assert.ok(gltf.nodes.some(n=>n.name===name),name);
  for(let i=1;i<=22;i++)assert.ok(gltf.nodes.some(n=>n.name===`burial_J${i}`),`Jar burial ${i}`);
  assert.equal(gltf.nodes.filter(n=>/^theatre_seat_\d+_\d+$/.test(n.name)).length,38);
  assert.equal(gltf.nodes.filter(n=>/^S96_internal_jar_\d$/.test(n.name)).length,4);
  assert.ok(gltf.nodes.some(n=>n.extras?.hide_in_overview));
  assert.ok(gltf.images.every(i=>!i.uri));
});

test('museum high roof junction blocks sky while the entrance and bridge remain accessible',()=>{
  const {scene}=readModel(new URL('../public/models/bogam-museum.glb',import.meta.url));
  const f=JSON.parse(fs.readFileSync(new URL('../knowledge/sources/bogam-museum-hall-frame.json',import.meta.url),'utf8')).hallFrame;
  const c=Math.cos(f.worldXZangle),s=Math.sin(f.worldXZangle);
  const point=(x,y,z)=>new THREE.Vector3(f.center[0]+x*c-z*s,y,f.center[1]+x*s+z*c);
  const closure=[];scene.traverse(o=>{if(o.name==='cutaway_south_closure')closure.push(o);});
  for(const x of [-20,-8,5,20]){
    const hits=new THREE.Raycaster(point(x,8.5,21),new THREE.Vector3(-s,0,c),.01,4).intersectObjects(closure,true);
    assert.ok(hits.length,`Open south roof seam at ${x}`);
  }
  for(const p of museum.places){
    assert.ok(canTravelTo(mapArrival(p,museum),museum,p.arrivalHeight??0),`New exhibit blocks arrival ${p.id}`);
  }
});

test('museum fitted chamber paving has geometry under the displayed vessels',()=>{
  const {scene}=readModel(new URL('../public/models/bogam-museum.glb',import.meta.url));
  const f=JSON.parse(fs.readFileSync(new URL('../knowledge/sources/bogam-museum-hall-frame.json',import.meta.url),'utf8')).hallFrame;
  const c=Math.cos(f.worldXZangle),s=Math.sin(f.worldXZangle),b=museum.burials.find(b=>b.id==='S12');
  const [x,z]=b.model_center, floors=[];
  scene.traverse(o=>{if(o.name.startsWith('S12_fitted_flagstone')||o.name==='S12_joint_bed')floors.push(o);});
  for(const [dx,dz] of [[0,0],[-.3,.3],[.3,-.3]]){
    const ray=new THREE.Raycaster(new THREE.Vector3(f.center[0]+(x+dx)*c-(z+dz)*s,b.replica_floor+.35,f.center[1]+(x+dx)*s+(z+dz)*c),new THREE.Vector3(0,-1,0),.01,.4);
    assert.ok(ray.intersectObjects(floors,true).length,`Missing fitted chamber floor ${dx},${dz}`);
  }
});

test('Bogam preserves four individually shaped mounds, source scale and numbering',()=>{
  assert.equal(bogam.site_osm_id,'471352010');
  assert.match(bogam.source,/OpenStreetMap.*ODbL/);
  assert.equal(bogam.mounds.length,4);
  const [one,two,three,four]=bogam.mounds;
  assert.ok(one.center[1]<two.center[1] && two.center[1]<three.center[1]);
  assert.ok(four.center[0]<three.center[0]);
  assert.deepEqual([one.width,one.height],[18,4.5]);
  assert.deepEqual([three.width,three.depth,three.height],[38,42,6]);
  assert.deepEqual([four.width,four.depth,four.height],[23,31.5,3.15]);
  assert.match(two.dimensions_source,/estimate.*NOT a recorded/);
  for(const m of bogam.mounds)assert.ok(bogamColliders.some(c=>hitsPolygon(...m.center,c)));
});

test('walk a complete Bogam circuit to all four mounds and back without crossing a mound',()=>{
  let p={x:bogam.spawn.x,z:bogam.spawn.z};
  assert.ok(canTravelTo([p.x,p.z],bogam));
  for(const [x,z] of bogam.walkRoute.slice(1)){
    p=movePlayer(p.x,p.z,x-p.x,z-p.z,bogamColliders,bogam.bounds);
    assert.ok(Math.hypot(p.x-x,p.z-z)<.03,`Blocked mound circuit ${x},${z}: ${JSON.stringify(p)}`);
  }
  assert.ok(Math.hypot(p.x-bogam.spawn.x,p.z-bogam.spawn.z)<.03);
  const from=[55,35],through=[-5,35];
  const hit=movePlayer(...from,through[0]-from[0],0,bogamColliders,bogam.bounds);
  assert.ok(hit.x>40,'Walking cannot pass through the large mound');
});

test('map relocation rejects obstacles, nonfinite coordinates and out-of-bounds destinations',()=>{
  assert.equal(destinationFromSearch('?place=bogam'),'bogam');
  for(const d of Object.values(destinations)){
    const w=JSON.parse(fs.readFileSync(new URL('../public'+d.worldUrl,import.meta.url),'utf8'));
    assert.ok(canTravelTo([w.spawn.x,w.spawn.z],w,w.spawn.height??0));
    for(const p of w.places){
      const target=mapArrival(p,w);
      assert.ok(target,`No accessible arrival for ${d.name} / ${p.name}`);
      assert.ok(canTravelTo(target,w,p.arrivalHeight??0));
    }
    for(const point of [[NaN,0],[0,Infinity],[w.bounds[0]-.1,0],[0,w.bounds[3]+1]])assert.equal(canTravelTo(point,w),false);
    const pin=regionalPoint(d.coordinates.lon,d.coordinates.lat);
    assert.ok(pin[0]>0&&pin[0]<regionalSize[0]&&pin[1]>0&&pin[1]<regionalSize[1]);
  }
  for(const m of bogam.mounds)assert.equal(canTravelTo(m.center,bogam),false);
  for(const p of bogam.places)assert.deepEqual(mapArrival(p,bogam),p.arrival);
});

test('Bogam exported GLB has four solid mound surfaces with upward normals and embedded original grass',()=>{
  const buffer=fs.readFileSync(new URL('../public/models/bogam-tumuli.glb',import.meta.url));
  assert.equal(buffer.toString('utf8',0,4),'glTF');
  assert.equal(buffer.readUInt32LE(8),buffer.length);
  const jsonLength=buffer.readUInt32LE(12);
  const gltf=JSON.parse(buffer.toString('utf8',20,20+jsonLength));
  assert.match(gltf.asset.generator,/Blender/);
  assert.ok(gltf.images.length>0&&gltf.images.every(i=>i.bufferView!==undefined&&!i.uri));
  assert.ok(gltf.buffers.every(b=>!b.uri));
  for(const m of bogam.mounds){
    const node=gltf.nodes.find(n=>n.name===`mound_${m.id}`);
    assert.ok(node,`Missing mound ${m.id}`);
    const primitive=gltf.meshes[node.mesh].primitives[0];
    const position=gltf.accessors[primitive.attributes.POSITION];
    assert.ok(Math.abs(position.max[1]-position.min[1]-m.height)<.001);
    const normals=gltf.accessors[primitive.attributes.NORMAL];
    const view=gltf.bufferViews[normals.bufferView];
    let up=0;
    for(let i=0;i<normals.count;i++){
      const offset=20+jsonLength+8+(view.byteOffset??0)+(normals.byteOffset??0)+i*(view.byteStride??12);
      if(buffer.readFloatLE(offset+4)>.5)up++;
    }
    assert.ok(up>normals.count*.3,'Most visible slopes and plateau should face upward');
  }
});

const neighborhood = JSON.parse(fs.readFileSync(new URL('../public/dasi-neighborhood-world.json', import.meta.url), 'utf8'));
const neighborhoodColliders = neighborhood.solids.filter(s => s.collision).map(solidCollider);

test('neighborhood preserves school coordinates, mapped station and source attribution', () => {
  assert.deepEqual(neighborhood.bounds,[-285,285,-245,195]);
  assert.equal(neighborhood.campus_osm_id,'963585633');
  assert.match(neighborhood.source,/OpenStreetMap.*ODbL/);
  assert.ok(neighborhood.buildings.length > 55);
  const station = neighborhood.buildings.find(b=>b.osm_id==='605798599');
  assert.ok(station && station.footprint.length===4);
  for (const building of neighborhood.buildings) {
    assert.ok(building.osm_id || building.trace_id,'Every building needs source coordinates');
    assert.ok(building.height_source,'Estimated heights must have provenance');
  }
  for (const [id,count] of [['963585625',10],['963585637',5],['963585641',4]]) {
    const b=neighborhood.buildings.find(b=>b.osm_id===id);
    assert.equal(b.floors,count);assert.match(b.floors_source,/^https:/);
  }
  for (const id of ['W03','W16','W27']) assert.ok(!neighborhood.buildings.some(b=>b.trace_id===id),'Mapped silhouettes must not be duplicated');
  assert.equal(neighborhoodColliders.some(c=>hitsPolygon(neighborhood.spawn.x,neighborhood.spawn.z,c)),false);
});

test('walk from school grounds along Dasi-ro to the station and back',()=>{
  const gate=neighborhood.neighborhood.school_gate.center;
  const route=[[3,7],[-35,7],[-42,5],[-40,14],[-44,35],gate,[-36.44,49.72],[80,73],[100,78]];
  let p={x:route[0][0],z:route[0][1]};
  for(const [x,z] of [...route.slice(1),...route.slice(0,-1).reverse()]){
    p=movePlayer(p.x,p.z,x-p.x,z-p.z,neighborhoodColliders,neighborhood.bounds);
    assert.ok(Math.hypot(p.x-x,p.z-z)<.03,`Blocked station route ${x},${z}: ${JSON.stringify(p)}`);
  }
  const station=neighborhood.buildings.find(b=>b.osm_id==='605798599');
  const center=station.footprint.reduce((p,q)=>[p[0]+q[0]/4,p[1]+q[1]/4],[0,0]);
  assert.ok(neighborhoodColliders.some(c=>hitsPolygon(...center,c)),'Station exterior must block entry');
});

test('railway uses paired 1435 mm rails and platforms raise the walking floor',()=>{
  const floors=worldFloors(neighborhood.solids);
  const platforms=neighborhood.solids.filter(s=>s.name.startsWith('walk-floor_platform_'));
  assert.equal(platforms.length,2);
  for(const platform of platforms){
    const pts=platform.footprint; const p=pts.reduce((a,b)=>[a[0]+b[0]/pts.length,a[1]+b[1]/pts.length],[0,0]);
    assert.ok(floorHeight(...p,floors)>.4);
  }
  for(const r of neighborhood.neighborhood.railways)assert.equal(r.gauge,1.435);
  const left=neighborhood.solids.find(s=>s.name.startsWith('rail_')&&s.name.endsWith('_-1'));
  const right=neighborhood.solids.find(s=>s.name===left.name.replace(/_-1$/,'_1'));
  assert.ok(Math.abs(Math.hypot(left.position[0]-right.position[0],left.position[2]-right.position[2])-1.435)<1e-6);
  const covers=neighborhood.solids.filter(s=>s.name.startsWith('crop-cover'));
  assert.ok(covers.length>=4);assert.ok(covers.every(s=>!s.collision&&s.size[1]<.1));
});

test('neighborhood GLB contains the station and outward-facing roof surfaces',()=>{
  const buffer=fs.readFileSync(new URL('../public/models/dasi-neighborhood.glb',import.meta.url));
  assert.equal(buffer.readUInt32LE(8),buffer.length);
  const gltf=JSON.parse(buffer.toString('utf8',20,20+buffer.readUInt32LE(12)));
  assert.match(gltf.asset.generator,/Blender/);
  assert.ok(gltf.nodes.some(n=>n.name==='station_blue_nameboard'));
  assert.ok(gltf.nodes.some(n=>n.name==='school_name_readable'));
  assert.ok(gltf.buffers.every(b=>!b.uri));assert.ok(!gltf.images?.some(i=>i.uri));
  const sign=neighborhood.signs.find(s=>s.text==='다시역');
  assert.ok(Math.cos(sign.rotation)<-.95,'Station sign must face its north approach');
  // Inspect exported normals rather than just reproducing the roof implementation.
  const roofNode=gltf.nodes.find(n=>n.name==='neighborhood_roof_605798599');
  const normalAccessor=gltf.accessors[gltf.meshes[roofNode.mesh].primitives[0].attributes.NORMAL];
  const view=gltf.bufferViews[normalAccessor.bufferView];
  const binOffset=20+buffer.readUInt32LE(12)+8;
  let upward=0;
  for(let i=0;i<normalAccessor.count;i++){
    const offset=binOffset+(view.byteOffset??0)+(normalAccessor.byteOffset??0)+i*(view.byteStride??12);
    if(buffer.readFloatLE(offset+4)>.2)upward++;
  }
  assert.ok(upward>0,'Roof must have upward-facing exterior normals');
});

const world = JSON.parse(fs.readFileSync(new URL('../public/city-world.json', import.meta.url), 'utf8'));
const colliders = world.solids.filter(s => s.collision).map(solidCollider);

test('mapped city has the five source buildings and an unblocked spawn', () => {
  assert.equal(world.buildings.length, 5);
  assert.ok(world.buildings.some(b => b.osm_id === '832423358'));
  assert.equal(colliders.some(p => hitsPolygon(world.spawn.x, world.spawn.z, p)), false);
});

test('walk from spawn through the actual hall doorway, reach interior, and return', () => {
  let p = { x: world.spawn.x, z: world.spawn.z };
  for(const [x,z] of world.walkRoute.slice(1)){
    p=movePlayer(p.x,p.z,x-p.x,z-p.z,colliders,world.bounds);
    assert.ok(Math.hypot(p.x-x,p.z-z)<.04,`Blocked hall approach ${x},${z}: ${JSON.stringify(p)}`);
  }
  const interior = world.places.find(p => p.id === 'interior');
  assert.ok(Math.hypot(p.x-interior.position[0],p.z-interior.position[1]) < interior.radius);
  assert.ok(p.z < world.spawn.z - 28);
  for(const [x,z] of world.walkRoute.slice(0,-1).reverse())p=movePlayer(p.x,p.z,x-p.x,z-p.z,colliders,world.bounds);
  assert.ok(Math.abs(p.z-world.spawn.z) < .01);
});

test('both mapped historic gates retain a clear passage into the hall courtyard',()=>{
  const route=[];
  for(const id of ['832423356','832423357']){
    const fp=world.buildings.find(b=>b.osm_id===id).footprint;
    const a=fp[1],b=fp[2],length=Math.hypot(b[0]-a[0],b[1]-a[1]);
    const inward=[(b[1]-a[1])/length,-(b[0]-a[0])/length];
    const center=world.places.find(p=>p.id===id).position;const d=Math.hypot(fp[0][0]-a[0],fp[0][1]-a[1])/2+2;
    route.push([center[0]-inward[0]*d,center[1]-inward[1]*d],center,[center[0]+inward[0]*d,center[1]+inward[1]*d]);
  }
  route.push(...world.walkRoute);
  let p={x:route[0][0],z:route[0][1]};
  for(const [x,z] of route.slice(1)){
    p=movePlayer(p.x,p.z,x-p.x,z-p.z,colliders,world.bounds);
    assert.ok(Math.hypot(p.x-x,p.z-z)<.04,`Blocked gate route: ${JSON.stringify(p)}`);
  }
});

test('the mapped western parking entrance connects to Manghwaru and the hall',()=>{
  assert.equal(world.surroundings.parkingOsmId,'478611741');
  for(const car of world.solids.filter(s=>s.name==='parked_vehicle_body')){
    for(const [x,z] of solidCollider(car))assert.ok(hitsPolygon(x,z,world.surroundings.parkingOutline,0),'Parked car must remain inside the mapped car park');
  }
  const route=[...world.surroundings.entranceRoute,...world.walkRoute];
  let p={x:route[0][0],z:route[0][1]};
  for(const [x,z] of [...route.slice(1),...route.slice(0,-1).reverse()]){
    p=movePlayer(p.x,p.z,x-p.x,z-p.z,colliders,world.bounds);
    assert.ok(Math.hypot(p.x-x,p.z-z)<.045,`Entrance or parking route blocked at ${x},${z}: ${JSON.stringify(p)}`);
  }
  for(const s of world.solids.filter(s=>s.name.startsWith('hall-wall_boundary_'))){
    const fp=solidCollider(s),cx=fp.reduce((v,p)=>v+p[0],0)/fp.length,cz=fp.reduce((v,p)=>v+p[1],0)/fp.length;
    assert.equal(canTravelTo([cx,cz],world),false,'Map relocation cannot place a walker inside the new perimeter wall');
  }
});

test('imagery context buildings stay outside the historic precinct and remain collision solid',()=>{
  const observations=world.surroundings.roofObservations;
  assert.equal(observations.length,37);
  assert.equal(mapSolids(world).filter(s=>/^context_.*_wall$/.test(s.name)).length,37,'Surrounding buildings must also appear on the travel map');
  for(const b of observations){
    const x=b.footprint.reduce((s,p)=>s+p[0],0)/b.footprint.length,z=b.footprint.reduce((s,p)=>s+p[1],0)/b.footprint.length;
    assert.equal(hitsPolygon(x,z,world.surroundings.precinctBoundary,0),false,`${b.id} must remain outside the monument grounds`);
    assert.equal(canTravelTo([x,z],world),false,`${b.id} must block map placement and walking`);
  }
});

test('high-speed movement cannot tunnel through a thin wall', () => {
  const wall = [[-2,-.05],[2,-.05],[2,.05],[-2,.05]];
  const p = movePlayer(0,2,0,-10,[wall],[-20,20,-20,20]);
  assert.ok(p.z >= .28);
});

test('walls allow sliding, and map boundaries keep the player inside', () => {
  const wall = [[1,-10],[1.1,-10],[1.1,10],[1,10]];
  const p = movePlayer(0,0,4,4,[wall],[-20,20,-20,20]);
  assert.ok(p.x < .75 && p.z > 3.9);
  const edge = movePlayer(0,0,50,50,[],[-10,10,-10,10]);
  assert.ok(edge.x <= 9.7 && edge.z <= 9.7);
});

test('Blender GLB is complete, self-contained, and contains the hall', () => {
  const buffer = fs.readFileSync(new URL('../public/models/geumseonggwan.glb', import.meta.url));
  assert.equal(buffer.toString('utf8',0,4),'glTF');
  assert.equal(buffer.readUInt32LE(4),2);
  assert.equal(buffer.readUInt32LE(8),buffer.length);
  const jsonLength=buffer.readUInt32LE(12);
  const gltf=JSON.parse(buffer.toString('utf8',20,20+jsonLength));
  assert.match(gltf.asset.generator,/Blender/);
  assert.ok(gltf.nodes.some(n => n.name === 'roof_832423358'));
  for(const name of ['hall_coffer_panel','hall_inner_tall_column','hall_door_front_2_0_paper','manghwaru_upper_floor','old_well_rubble','memorial_stele_body'])assert.ok(gltf.nodes.some(n=>n.name===name),name);
  assert.equal(gltf.nodes.filter(n=>/^hall_inner_tall_column(?:\.\d+)?$/.test(n.name)).length,8,'The public plan shows eight inner tall columns');
  assert.ok(world.signs.some(s=>s.text==='樓 華 望'),'Manghwaru plaque must use the correct Hanja');
  assert.equal(gltf.nodes.some(n=>n.name==='interior_panel'),false,'The fictional gallery must not remain in the photographed open hall');
  assert.ok(gltf.buffers.every(b => !b.uri));
  assert.ok(!gltf.images?.some(i => i.uri));
});

test('compressed model transport restores the exact Blender bytes below the hosting file limit',async()=>{
  const original=fs.readFileSync(new URL('../public/models/geumseonggwan.glb',import.meta.url));
  const packed=fs.readFileSync(new URL('../public/models/geumseonggwan.glb.gz',import.meta.url));
  assert.ok(packed.length<25*1024*1024);
  assert.deepEqual(Buffer.from(await unpackModel(packed.buffer.slice(packed.byteOffset,packed.byteOffset+packed.byteLength))),original);
  assert.deepEqual(Buffer.from(await unpackModel(original.buffer.slice(original.byteOffset,original.byteOffset+original.byteLength))),original);
});

test('stone stairs and elevated hall floors raise the walking eye level', () => {
  const floors=worldFloors(world.solids);
  const interior=world.places.find(p => p.id === 'interior');
  assert.ok(floorHeight(...interior.position,floors) > .9);
  assert.equal(floorHeight(world.spawn.x,world.spawn.z,floors),0);
  const steps=world.solids.filter(s => s.name.startsWith('walk-floor_step'));
  assert.equal(steps.length,5);
  for(const step of steps){
    const polygon=solidCollider(step);const x=polygon.reduce((sum,p)=>sum+p[0],0)/polygon.length,z=polygon.reduce((sum,p)=>sum+p[1],0)/polygon.length;
    assert.ok(floorHeight(x,z,floors)>=step.size[1]-.001);
  }
});

const school = JSON.parse(fs.readFileSync(new URL('../public/dasi-world.json', import.meta.url), 'utf8'));
const schoolColliders = school.solids.filter(s => s.collision).map(solidCollider);

test('school navigation preserves the original destination and selects the school safely', () => {
  assert.equal(destinationFromSearch(''), 'geumseonggwan');
  assert.equal(destinationFromSearch('?place=dasi'), 'dasi');
  assert.equal(destinationFromSearch('?place=unknown'), 'geumseonggwan');
  for (const d of Object.values(destinations)) {
    assert.ok(fs.existsSync(new URL('../public'+d.worldUrl, import.meta.url)));
    assert.ok(fs.existsSync(new URL('../public'+d.modelUrl, import.meta.url)));
  }
});

test('school preserves both mapped building outlines and the campus boundary', () => {
  assert.equal(school.campus_osm_id, '963585633');
  assert.deepEqual(school.buildings.map(b => b.osm_id), ['963585634', '963585635']);
  assert.equal(school.buildings[0].footprint.length, 23);
  assert.equal(schoolColliders.some(c => hitsPolygon(school.spawn.x, school.spawn.z, c)), false);
  const campus = school.solids.find(s => s.name === 'ground_floor_campus');
  assert.ok(hitsPolygon(school.spawn.x, school.spawn.z, solidCollider(campus), 0));
});

test('school route reaches the field and front colonnade without crossing a building', () => {
  let p = { x: school.spawn.x, z: school.spawn.z };
  for (const [x,z] of [[3,7],[40,8],[56,8],[40,8],[3,7],[-35,7],[-42,5],[-29,-4]]) {
    p = movePlayer(p.x,p.z,x-p.x,z-p.z,schoolColliders,school.bounds);
    assert.ok(Math.hypot(p.x-x,p.z-z)<.02, `Unreachable waypoint ${x},${z}: ${JSON.stringify(p)}`);
  }
  const floors=worldFloors(school.solids);
  assert.ok(floorHeight(p.x,p.z,floors)>=.065);
  const wallHit=movePlayer(p.x,p.z,0,-45,schoolColliders,school.bounds);
  assert.ok(wallHit.z>-14, 'The front facade must stop the player');
});

test('the full outdoor route connects parking, lawn, grove path and southeast yard', () => {
  let p={x:-42,z:5};
  for(const [x,z] of [[-40,14],[-44,35],[12,42.5],[12,20],[25,21],[25,16],[3,7]]) {
    p=movePlayer(p.x,p.z,x-p.x,z-p.z,schoolColliders,school.bounds);
    assert.ok(Math.hypot(p.x-x,p.z-z)<.03,`Blocked outdoor route to ${x},${z}: ${JSON.stringify(p)}`);
  }
  for(const name of ['ground_floor_school_lawn','ground_floor_school_parking','ground_floor_south_grove','ground_floor_sport_court']) assert.ok(school.solids.some(s=>s.name===name));
  const field=school.solids.find(s=>s.name==='ground_floor_school_lawn');
  assert.equal(hitsPolygon(-55,0,solidCollider(field)),false,'The west parking area must not be grass');
  assert.equal(hitsPolygon(-10,35,solidCollider(field)),false,'The south grove must not be part of the field');
});

test('school GLB includes photo details and embeds its original brick texture', () => {
  const buffer=fs.readFileSync(new URL('../public/models/dasi-elementary.glb', import.meta.url));
  assert.equal(buffer.toString('utf8',0,4),'glTF');
  assert.equal(buffer.readUInt32LE(8),buffer.length);
  const gltf=JSON.parse(buffer.toString('utf8',20,20+buffer.readUInt32LE(12)));
  assert.match(gltf.asset.generator,/Blender/);
  for (const name of ['osm-building_963585634','roof_west_barrel','school_round_emblem','roof_blue_annex','gate_pier_0']) assert.ok(gltf.nodes.some(n=>n.name===name),name);
  assert.ok(gltf.images?.length>0);
  assert.ok(gltf.images.every(i=>!i.uri && i.bufferView!==undefined));
  assert.ok(gltf.buffers.every(b=>!b.uri));
});

test('school entrance leads continuously to the library and classroom and back outside', () => {
  const route=school.interior.walkRoute;
  let p={x:route[0][0],z:route[0][1]};
  for (const [x,z] of [...route.slice(1),...route.slice(0,-1).reverse()]) {
    p=movePlayer(p.x,p.z,x-p.x,z-p.z,schoolColliders,school.bounds);
    assert.ok(Math.hypot(p.x-x,p.z-z)<.025, `Blocked school interior route to ${x},${z}: ${JSON.stringify(p)}`);
  }
  assert.ok(Math.hypot(p.x-school.spawn.x,p.z-school.spawn.z)<.025);
  const inside=school.places.find(p=>p.id==='corridor');
  assert.ok(floorHeight(...inside.position,worldFloors(school.solids))>=.2);
});

test('classroom partition and furniture block walking even at high speed', () => {
  const [start,end]=school.interior.wallProbe;
  const hit=movePlayer(...start,end[0]-start[0],end[1]-start[1],schoolColliders,school.bounds);
  assert.ok(Math.hypot(hit.x-end[0],hit.z-end[1])>.7);
  const desk=school.solids.find(s=>s.name==='student_desk_0_0_top');
  assert.ok(desk.collision);
  assert.ok(hitsPolygon(desk.position[0],desk.position[2],solidCollider(desk)));
});

test('indoor labels apply only within their room footprint', () => {
  for (const id of ['corridor','classroom','library']) {
    const room=school.places.find(p=>p.id===id);
    assert.equal(currentPlace(...room.position,school.places)?.id,id);
    assert.equal(currentPlace(...room.position,school.places)?.indoor,true);
  }
  assert.notEqual(currentPlace(school.spawn.x,school.spawn.z,school.places)?.indoor,true);
});

test('school facade lettering faces the courtyard and fits above the canopy', () => {
  const text=school.signs.find(s=>s.text==='다시초등학교' && s.width>8);
  assert.ok(text);
  const points=school.buildings[0].footprint;
  const a=points[22],b=points[0],dx=b[0]-a[0],dz=b[1]-a[1],length=Math.hypot(dx,dz);
  const dot=Math.sin(text.rotation)*dz/length+Math.cos(text.rotation)*(-dx)/length;
  assert.ok(dot>.999,'Front face of the letters must point toward the courtyard, not into the wall');
  assert.ok(text.position[1]-text.height/2>4.04,'Canopy/floor band must not hide the lettering');
  const vertical=school.signs.find(s=>s.text==='다\n시\n초\n등\n학\n교');
  assert.ok(vertical.height<=1.8,'Gate sign must fit its nameplate');
});

test('static detail batching preserves world bounds and keeps transparent windows separate', () => {
  const root=new THREE.Group(); root.position.set(4,2,-8); root.rotation.y=.3;
  const parent=new THREE.Group(); parent.position.set(-3,0,5); parent.rotation.y=-.7; root.add(parent);
  const material=new THREE.MeshStandardMaterial({color:'#779966'});
  const shape=new THREE.BoxGeometry(1,2,3);
  for(let i=0;i<25;i++) { const mesh=new THREE.Mesh(shape,material); mesh.position.set(i%5*2,0,Math.floor(i/5)*4); parent.add(mesh); }
  const window=new THREE.Mesh(shape,new THREE.MeshStandardMaterial({transparent:true,opacity:.25})); root.add(window);
  root.updateMatrixWorld(true);
  const before=new THREE.Box3().setFromObject(root,true);
  const stats=batchStaticScene(root);
  root.updateMatrixWorld(true);
  const after=new THREE.Box3().setFromObject(root,true);
  assert.equal(stats.before,26); assert.equal(stats.after,2);
  assert.ok(before.min.distanceTo(after.min)<.00001 && before.max.distanceTo(after.max)<.00001);
  assert.equal(window.parent,root,'Transparent panes must retain independent depth sorting');
});
