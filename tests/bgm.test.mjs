import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {destinations} from '../lib/destinations.ts';
import {bgmCredit,bgmForDestination,bgmTracks,bgmUrl} from '../lib/bgm.ts';

const root=new URL('../',import.meta.url);

test('every place has a background loop and every bundled loop is used',()=>{
  assert.deepEqual(Object.keys(bgmForDestination).sort(),Object.keys(destinations).sort());
  const used=new Set(Object.values(bgmForDestination));
  assert.deepEqual([...used].sort(),Object.keys(bgmTracks).sort());
  const files=fs.readdirSync(new URL('public/audio/bgm/',root)).sort();
  assert.deepEqual(files,Object.keys(bgmTracks).map(id=>`${id}.mp3`).sort(),'No stray audio is deployed');
});

test('loops are light web MP3s that stream on tablets',()=>{
  for(const id of Object.keys(bgmTracks)){
    const bytes=fs.readFileSync(new URL('public'+bgmUrl(id),root));
    assert.ok(bytes.subarray(0,3).toString('latin1')==='ID3'||(bytes[0]===0xff&&(bytes[1]&0xe0)===0xe0),`${id} is MP3`);
    assert.ok(bytes.length<3.5*1024*1024,`${id} stays under 3.5 MB`);
  }
});

test('credits name the work, the author and the source as CC BY 4.0 requires',()=>{
  assert.equal(bgmCredit('easy-lemon'),'“Easy Lemon” Kevin MacLeod (incompetech.com)');
  const guide=fs.readFileSync(new URL('app/walk-guide.tsx',root),'utf8');
  assert.match(guide,/CC BY 4\.0/);assert.match(guide,/BGM_LICENSE_URL/);assert.match(guide,/96kbps로 변환/);
});
