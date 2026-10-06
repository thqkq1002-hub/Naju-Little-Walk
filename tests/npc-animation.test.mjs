import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {NpcAnimation,guideGestures} from '../lib/npc-animation.ts';
import {guideReply} from '../lib/npc-dialogue.ts';

function fixture(){
  const root=new THREE.Group(),bone=new THREE.Bone();bone.name='Head';root.add(bone);
  const clips=guideGestures.map(name=>new THREE.AnimationClip(name,1,[new THREE.NumberKeyframeTrack('Head.rotation[x]',[0,.5,1],[0,name==='Idle'?.02:.08,0])]));
  return {controller:new NpcAnimation(root,clips),bone};
}
test('guide speech commands choose greeting, nod, listening and local scene explanation',()=>{
  assert.equal(guideReply('안녕하세요','bitgaram-park','배돌이').gesture,'Greeting');
  assert.equal(guideReply('고개 끄덕여줘','yeongsanpo','홍돌이').gesture,'Nod');
  assert.equal(guideReply('내 말 들어줘','dasi','선생님').gesture,'Listen');
  assert.equal(guideReply('멈춰 줘','bogam','버들낭자').gesture,'Idle');
  const answer=guideReply('이곳을 설명해줘','bitgaram-park','배돌이');
  assert.equal(answer.gesture,'Explain');assert.match(answer.text,/전망대/);
});
test('an authored skeletal gesture changes pose, blends and returns to idle after one shot',()=>{
  const {controller,bone}=fixture();controller.setGesture('Nod');
  for(let i=0;i<10;i++)controller.update(.06);
  assert.ok(bone.rotation.x>.03);
  for(let i=0;i<12;i++)controller.update(.06);
  assert.equal(controller.gesture,'Idle');controller.dispose();
});
test('a replaced greeting cannot finish and cancel the newer explanation',()=>{
  const {controller}=fixture();controller.setGesture('Greeting');
  for(let i=0;i<12;i++)controller.update(.06);
  controller.setGesture('Explain');
  for(let i=0;i<12;i++)controller.update(.06);
  assert.equal(controller.gesture,'Explain');controller.dispose();
});
test('reduced motion pauses bone updates without removing guide content',()=>{
  const {controller,bone}=fixture();controller.setGesture('Explain');controller.reducedMotion=true;
  const before=bone.rotation.x;for(let i=0;i<20;i++)controller.update(.06);
  assert.equal(bone.rotation.x,before);assert.equal(controller.gesture,'Explain');controller.dispose();
});
