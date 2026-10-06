import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
test('Neureoji separates terrain elevation, upper deck and whole structure height',()=>{
 const w=read('public/neureoji-world.json'),e=read('knowledge/sources/neureoji-polish-v98/elevation-check.json');
 assert.equal(w.spawn.height,e.model.base);assert.equal(w.topDeckHeightMetres,e.model.deck);
 assert.ok(Math.abs(e.terrarium[0].heightMetres-w.spawn.height)<.2);
 assert.equal(w.topDeckHeightMetres-w.spawn.height,12);assert.equal(w.towerHeightMetres,15.35);
 assert.equal(w.elevationAudit.surveyed,false);assert.ok(w.elevationAudit.datum.includes('not an observed'));
});
test('Forest polishing preserves collision solids and their elevation',()=>{
 const w=read('public/neureoji-world.json'),m=read('knowledge/sources/neureoji-polish-v98/model.json');
 assert.deepEqual(w.solids,read('knowledge/sources/neureoji-polish-v98/navigation-solids.json'));
 assert.ok(m.groundedCrowns.length>500);assert.ok(m.export.gzipBytes<16*1024**2);
});


