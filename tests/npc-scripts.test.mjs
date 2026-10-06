import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {introScript,introScripts,speechText} from '../lib/npc-scripts.ts';

const manifest=JSON.parse(fs.readFileSync(new URL('../public/npc-placements.json',import.meta.url),'utf8'));
const pictograph=/\p{Extended_Pictographic}/u;

test('every placed guide has a saved intro script, reached by either intro quick reply',()=>{
  for(const id of Object.keys(manifest.placements)){
    const lines=introScripts[id];
    assert.ok(lines?.length>0,`${id} has no saved script`);
    assert.ok(lines.every(line=>line.trim().length>0),`${id} has an empty line`);
    assert.deepEqual(introScript('이곳을 소개해 줘',id),lines);
    assert.deepEqual(introScript('이곳을 소개해 주세요',id),lines);
    assert.deepEqual(introScript('  이곳을 소개해 주세요  ',id),lines);
  }
});

test('other messages and unscripted maps keep the ordinary guide reply',()=>{
  assert.equal(introScript('안녕!','dasi'),null);
  assert.equal(introScript('안녕하세요','dasi'),null);
  assert.equal(introScript('지붕을 소개해 줘','geumseonggwan'),null);
  assert.equal(introScript('이곳을 소개해 줘','bitgaram-observatory'),null);
});

test('spoken text drops pictographs and keeps punctuation tidy',()=>{
  assert.equal(speechText('지구를 지키는 에너지 연구실 🧪: 수소 에너지 끝! 🌧️☀️'),'지구를 지키는 에너지 연구실: 수소 에너지 끝!');
  for(const [id,lines] of Object.entries(introScripts))for(const line of lines){
    const spoken=speechText(line);
    assert.ok(spoken.length>0,`${id} line is silent after stripping`);
    assert.equal(pictograph.test(spoken),false,`${id}: pictograph left in "${spoken.slice(0,30)}"`);
  }
});
