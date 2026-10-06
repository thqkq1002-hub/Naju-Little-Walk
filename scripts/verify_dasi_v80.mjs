import fs from 'node:fs';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const keys=['solids','bounds','spawn','interior','buildings','neighborhood','signs'];
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const navigation=[];
for(const file of ['dasi-neighborhood-world.json','dasi-world.json']){
  const old=JSON.parse(execFileSync('git',['show','HEAD:public/'+file],{encoding:'utf8',maxBuffer:5*1024*1024}));
  const current=JSON.parse(fs.readFileSync('public/'+file,'utf8'));
  const before=Object.fromEntries(keys.map(k=>[k,old[k]??null]));
  const after=Object.fromEntries(keys.map(k=>[k,current[k]??null]));
  assert.deepEqual(after,before,file+' existing models and navigation');
  navigation.push({file,navigationKeys:keys,unchanged:true,navigationSha256:createHash('sha256').update(JSON.stringify(canonical(after))).digest('hex')});
}
const baselineFile='outputs/palette-v51/dasi-neighborhood-color-v51.blend';
const expected=JSON.parse(fs.readFileSync('outputs/dasi-v80/before-inspection.json','utf8')).sourceSha256;
assert.equal(createHash('sha256').update(fs.readFileSync(baselineFile)).digest('hex'),expected);
const build=JSON.parse(fs.readFileSync('outputs/dasi-v80/build-summary.json','utf8'));
const raw=fs.readFileSync('public/models/dasi-neighborhood.glb');
const gltf=JSON.parse(raw.toString('utf8',20,20+raw.readUInt32LE(12)));
build.materials=gltf.materials.length;build.images=gltf.images.length;
fs.writeFileSync('outputs/dasi-v80/build-summary.json',JSON.stringify(build,null,2)+'\n');
const inspection=JSON.parse(fs.readFileSync('outputs/dasi-v80/before-inspection.json','utf8'));
const crowns=inspection.objects.filter(o=>o.name.startsWith('tree-crown_'));
const canopyBounds={min:[Math.min(...crowns.map(o=>o.lo[0])),Math.min(...crowns.map(o=>o.lo[2])),Math.min(...crowns.map(o=>-o.hi[1]))],max:[Math.max(...crowns.map(o=>o.hi[0])),Math.max(...crowns.map(o=>o.hi[2])),Math.max(...crowns.map(o=>-o.lo[1]))]};
const report={date:'2026-10-03',scope:'Existing school forms, places and navigation retained',sourceBlend:baselineFile,sourceSha256:expected,navigation,canopyBounds,build};
fs.writeFileSync('knowledge/sources/dasi-v80-verification.json',JSON.stringify(report,null,2)+'\n');
console.log('Dasi source and both navigation datasets unchanged from the pre-refinement revision.');
