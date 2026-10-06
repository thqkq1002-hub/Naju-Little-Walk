import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {createHash} from 'node:crypto';
import {worldFloors,worldObstacles,moveOnFloors} from '../lib/world.ts';
import {canTravelTo,mapArrival} from '../lib/map-navigation.ts';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));const w=read('public/yeongsanpo-history-world.json'),r=read('knowledge/sources/history-gallery-v91.json');
test('gallery covers observed first-floor exhibits and protects the preserved source',()=>{
 assert.equal(w.exhibitSections.length,11);assert.equal(r.craftCases,4);assert.equal(r.riverScenes,8);
 for(const name of ['홍어애국','홍어삼합','홍어찜','자미공방','어울리기공방','목사골공방','최현공방'])assert.ok(w.signs.some(s=>s.text===name),name);
 assert.equal(createHash('sha256').update(fs.readFileSync(new URL('../'+r.sourceBlend,import.meta.url))).digest('hex'),r.sourceSha256);
 assert.ok(r.unchangedDoorwayAndSpawn);assert.equal(w.viewMode,'panorama');assert.ok(w.limitations.some(x=>x.includes('second-floor')));
});
test('new display cases leave the exhibit loop, entry and exit accessible',()=>{
 let p={x:w.spawn.x,z:w.spawn.z,height:w.spawn.height??0};const floors=worldFloors(w.solids),obs=worldObstacles(w.solids);
 for(const [x,z] of w.walkRoute.slice(1)){p=moveOnFloors(p.x,p.z,p.height,x-p.x,z-p.z,obs,floors,w.bounds,w.requireFloor);assert.ok(Math.hypot(p.x-x,p.z-z)<.05,`blocked ${x},${z}: ${JSON.stringify(p)}`);}
 for(const place of w.places){const a=mapArrival(place,w);assert.ok(a,place.id);assert.ok(canTravelTo(a,w,place.arrivalHeight??0));}
});
