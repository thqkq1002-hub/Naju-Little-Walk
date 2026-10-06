import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import zlib from 'node:zlib';
import {initialRailState,railLength,railPose,railObstacle,nearRailStation,requestRail,boardRail,leaveRail,stepRail} from '../lib/monorail.ts';
import {blocksWalking} from '../lib/world.ts';
import {canTravelTo} from '../lib/map-navigation.ts';
const root=new URL('../',import.meta.url);
const world=JSON.parse(fs.readFileSync(new URL('public/bitgaram-park-world.json',root)));
const d=world.monorail;
function runToStation(s,id){s=requestRail(d,s,id);for(let i=0;s.target&&i<12000;i++)s=stepRail(d,s,1/60);assert.equal(s.station,id);for(let i=0;i<60;i++)s=stepRail(d,s,1/60);return s;}
test('mapped route remains exact in plan and car floor meets both reachable platforms',()=>{
 const original=JSON.parse(fs.readFileSync(new URL('knowledge/sources/bitgaram/access-v69.json',root))).rail_route;
 assert.deepEqual(d.route.map(p=>[p[0],p[2]]),[...original].reverse().map(p=>[p[0],p[2]]));
 assert.ok(Math.abs(railLength(d)-d.stations[1].distance)<1e-6);
 for(const s of d.stations){assert.ok(canTravelTo(s.arrival,world,s.height),s.name);assert.ok(Math.abs(railPose(d,s.distance).y+d.floorOffset-s.height)<.001);assert.equal(nearRailStation(d,s.arrival,s.height)?.id,s.id);}
 assert.ok(!nearRailStation(d,d.stations[0].arrival,16),'No boarding from the wrong level');
});
test('empty car can be called, doors close before movement and distance cannot overshoot',()=>{
 let s=requestRail(d,initialRailState(d),'lower');const distance=s.distance;
 s=stepRail(d,s,.25);assert.equal(s.distance,distance);assert.ok(s.door>0&&s.door<1);
 for(let i=0;i<12000&&s.target;i++){s=stepRail(d,s,1/60);assert.ok(s.distance>=0&&s.distance<=railLength(d));if(s.speed>0)assert.equal(s.door,0);}
 assert.equal(s.station,'lower');assert.equal(s.distance,0);assert.equal(s.speed,0);
});
test('passenger makes a complete round trip, cannot leave while moving and keeps a window-view position',()=>{
 let s=runToStation(initialRailState(d),'lower');
 assert.equal(boardRail(d,s,[100,100],6.22),s);
 s=boardRail(d,s,d.stations[0].arrival,d.stations[0].height);assert.ok(s.aboard);
 s=requestRail(d,s,'upper');assert.equal(leaveRail(d,s),null);
 const locked=requestRail(d,s,'lower');assert.equal(locked,s,'Do not reverse a departing service');
 s=runToStation(s,'upper');assert.ok(s.aboard);assert.equal(leaveRail(d,s).station.id,'upper');
 s=runToStation(s,'lower');const left=leaveRail(d,s);assert.ok(!left.state.aboard);assert.deepEqual(left.station.arrival,[16,108]);
});
test('pause retains trip state and invalid frame times cannot move the cabin',()=>{
 let s=requestRail(d,initialRailState(d),'lower');for(let i=0;i<300;i++)s=stepRail(d,s,1/60);
 const snapshot={...s};assert.deepEqual(stepRail(d,s,0),snapshot);assert.deepEqual(stepRail(d,s,NaN),snapshot);
 assert.equal(requestRail(d,s,'invalid'),s);assert.ok(stepRail(d,s,1/60).distance<s.distance);
});
test('the moving cabin has a matching physical footprint without blocking platform arrivals',()=>{
 for(const station of d.stations){const p=railPose(d,station.distance),o=railObstacle(d,station.distance);assert.ok(blocksWalking(p.x,p.z,p.y+d.floorOffset,[o]));assert.ok(!blocksWalking(...station.arrival,station.height,[o]));}
 const p=railPose(d,railLength(d)/2);assert.ok(blocksWalking(p.x,p.z,p.y+d.floorOffset,[railObstacle(d,railLength(d)/2)]));
});
test('independent Blender cabin is hollow, has sliding doors, bogies, clear glazing and exact gzip',()=>{
 const raw=fs.readFileSync(new URL('public/models/bitgaram-monorail.glb',root));
 assert.deepEqual(zlib.gunzipSync(fs.readFileSync(new URL('public/models/bitgaram-monorail.glb.gz',root))),raw);
 const g=JSON.parse(raw.subarray(20,20+raw.readUInt32LE(12)));
 for(const n of ['photo_monorail_cab_body','cab_floor','cab_roof_aircon','cab_running_wheel','cab_guide_wheel','monorail_door_left','monorail_door_right'])assert.ok(g.nodes.some(p=>p.name===n),n);
 const doors=g.nodes.filter(p=>p.name.startsWith('monorail_door_'));assert.equal(doors.length,2);assert.ok(doors.every(p=>p.children?.length&&p.extras.authored_dynamic));
 assert.ok(g.materials.some(m=>m.alphaMode==='BLEND'&&m.pbrMetallicRoughness.baseColorFactor[3]<.3));
 assert.ok(raw.length<512*1024);
 const report=JSON.parse(fs.readFileSync(new URL('knowledge/sources/bitgaram/monorail-v83.json',root)));assert.ok(report.sourceUnchanged&&report.nonMonorailGeometryUnchanged);
});
