import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {FACE_RANGE,guideYaw,turnYaw,yawToward} from '../lib/npc-facing.ts';

const near=(a,b,e=1e-6)=>Math.abs(Math.atan2(Math.sin(a-b),Math.cos(a-b)))<e;
const front=yaw=>[Math.sin(yaw),Math.cos(yaw)];

test('a settled guide faces the visitor with its authored +Z front',()=>{
  const guide={position:[10,0,5],yaw:0};
  for(const [x,z] of [[10,9],[14,5],[6,1],[7,8]]){
    let yaw=guide.yaw;
    for(let i=0;i<120;i++)yaw=guideYaw(yaw,guide,{x,z,height:0},1/60);
    const [fx,fz]=front(yaw),length=Math.hypot(x-10,z-5);
    assert.ok(Math.abs(fx-(x-10)/length)<1e-3&&Math.abs(fz-(z-5)/length)<1e-3,`faces (${x},${z})`);
  }
});

test('turning takes the shorter way round and never overshoots, even after a long frame',()=>{
  const from=Math.PI-.1,to=-Math.PI+.1;
  const step=turnYaw(from,to,1/60,4);
  assert.ok(Math.cos(step-from)>.99&&Math.sin(step-from)>0,'crosses ±π instead of spinning through 0');
  assert.ok(near(turnYaw(0,1,10,4),1,1e-9),'a stalled frame lands exactly, without passing the target');
  let yaw=0;const seen=[];
  for(let i=0;i<60;i++){yaw=turnYaw(yaw,1,1/30,4);seen.push(yaw);}
  assert.ok(seen.every((v,i)=>i===0||v>=seen[i-1])&&seen.at(-1)<=1);
});

test('guides return to their placement pose when the visitor leaves or is on another level',()=>{
  const guide={position:[0,-6.4,0],yaw:2};
  const settle=visitor=>{let yaw=-1;for(let i=0;i<600;i++)yaw=guideYaw(yaw,guide,visitor,1/60);return yaw;};
  assert.ok(near(settle({x:FACE_RANGE+1,z:0,height:-6.4}),2,1e-3),'out of range');
  assert.ok(near(settle({x:3,z:0,height:0.1}),2,1e-3),'on the embankment above the pier');
  assert.ok(near(settle(null),2,1e-3),'no visitor (overview)');
  assert.ok(near(settle({x:3,z:0,height:-6.4}),yawToward(0,0,3,0),1e-3),'same deck, in range');
});

test('reduced motion snaps to the visitor instead of animating the turn',()=>{
  const guide={position:[0,0,0],yaw:0};
  assert.ok(near(guideYaw(0,guide,{x:-4,z:0,height:0},1/60,true),yawToward(0,0,-4,0)));
});

test('every walk-mode frame turns all placed guides, including extra guides on the same map',()=>{
  const explorer=fs.readFileSync(new URL('../app/explorer.tsx',import.meta.url),'utf8');
  assert.match(explorer,/if\(!bird\)npcs\.forEach\(\(npc,i\)=>\{npc\.root\.rotation\.y=guideYaw\(/);
});
