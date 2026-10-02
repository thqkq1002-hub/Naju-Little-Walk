import test from 'node:test';
import assert from 'node:assert/strict';
import {RenderDemand} from '../lib/render-demand.ts';

test('a stopped scene renders once then stays idle until an interaction invalidates it',()=>{
  const demand=new RenderDemand();
  assert.equal(demand.take(false,false),true);
  assert.equal(Array.from({length:120},()=>demand.take(false,false)).some(Boolean),false);
  demand.invalidate();demand.invalidate();
  assert.equal(demand.take(false,false),true);
  assert.equal(demand.take(false,false),false);
});

test('hidden, portrait and lost-context frames retain the latest scene change for recovery',()=>{
  const demand=new RenderDemand();
  demand.take(false,false);
  demand.invalidate();
  assert.equal(demand.take(true,true),false);
  assert.equal(demand.take(false,true),false);
  assert.equal(demand.take(false,false),true);
  assert.equal(demand.take(false,false),false);
});

test('active walking keeps animation frames and returns to idle after the last invalidation',()=>{
  const demand=new RenderDemand();
  for(let i=0;i<120;i++)assert.equal(demand.take(true,false),true);
  demand.invalidate();
  assert.equal(demand.take(false,false),true);
  assert.equal(demand.take(false,false),false);
});
