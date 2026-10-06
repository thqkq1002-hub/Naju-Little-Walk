import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {destinations} from '../lib/destinations.ts';
const root=new URL('../',import.meta.url);
test('confirmed unused files no longer belong to the active source or public tree',()=>{
 const log=JSON.parse(fs.readFileSync(new URL('knowledge/sources/workspace-cleanup-v81.json',root),'utf8'));
 assert.equal(log.applied,true);assert.equal(log.archivedFiles.length,76);
 for(const name of log.archivedFiles)assert.equal(fs.existsSync(new URL(name,root)),false,name);
});
test('cleanup preserves every active destination and current rigged guide asset',()=>{
 for(const d of Object.values(destinations)){
  for(const url of [d.worldUrl,d.modelUrl])assert.ok(fs.existsSync(new URL('public'+url.split('?')[0],root)),url);
 }
 const manifest=JSON.parse(fs.readFileSync(new URL('public/npc-placements.json',root),'utf8'));
 for(const asset of Object.values(manifest.assets)){
  assert.ok(fs.existsSync(new URL('public'+asset.modelUrl,root)),asset.modelUrl);
  assert.ok(fs.existsSync(new URL(asset.authoredExport,root)),asset.authoredExport);
 }
});
test('only current guide versions remain in the public asset directory',()=>{
 const files=fs.readdirSync(new URL('public/models/npc/',root)).filter(n=>n.endsWith('.glb'));
 assert.deepEqual(files.sort(),['baedoli-v6.glb','beodeuri-v6.glb','hongdoli-v6.glb','teacher-v6.glb']);
});
