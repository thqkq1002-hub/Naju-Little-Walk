import test from 'node:test';
import assert from 'node:assert/strict';
import { enterLandscape, needsLandscape, pixelRatioFor } from '../lib/display-mode.ts';
import { ViewGesture } from '../lib/view-gesture.ts';

test('landscape lock waits for fullscreen and handles unsupported tablets', async () => {
  const calls = [];
  const target = { requestFullscreen: async () => { calls.push('fullscreen'); } };
  assert.equal(await enterLandscape(target, { lock: async mode => { calls.push(mode); } }), 'locked');
  assert.deepEqual(calls, ['fullscreen', 'landscape']);
  assert.equal(await enterLandscape(target, undefined), 'rotate');
  assert.equal(await enterLandscape({}, undefined), 'unavailable');
  assert.equal(await enterLandscape({ requestFullscreen: async () => { throw Error('denied'); } }, undefined), 'unavailable');
  assert.equal(await enterLandscape(target, { lock: async () => { throw Error('unsupported'); } }), 'rotate');
  assert.equal(await enterLandscape({}, { lock: async () => {} }, true), 'locked');
});

test('portrait gate only applies to touch and display quality stays bounded', () => {
  assert.equal(needsLandscape(768, 1024, true), true);
  assert.equal(needsLandscape(1024, 768, true), false);
  assert.equal(needsLandscape(768, 1024, false), false);
  assert.equal(pixelRatioFor('balanced', 3), 1.1);
  assert.equal(pixelRatioFor('detail', 3), 1.75);
  assert.equal(pixelRatioFor('balanced', 1), 1);
});

test('movement-pad pointers do not change a canvas look gesture', () => {
  const gesture = new ViewGesture();
  gesture.down(11, 100, 100);
  assert.equal(gesture.move(22, 10, 10, false), null);
  assert.deepEqual(gesture.move(11, 110, 120, false), { dx: 10, dy: 20, scale: 1 });
  gesture.up(22);
  assert.deepEqual(gesture.move(11, 120, 125, false), { dx: 10, dy: 5, scale: 1 });
});

test('pinch zoom does not jump rotation and resumes single-finger look after release', () => {
  const gesture = new ViewGesture();
  gesture.down(1, 100, 100); gesture.down(2, 200, 100);
  assert.deepEqual(gesture.move(2, 250, 100, true), { dx: 0, dy: 0, scale: 2 / 3 });
  assert.equal(gesture.move(1, 90, 100, false), null);
  gesture.up(2);
  assert.deepEqual(gesture.move(1, 85, 110, false), { dx: -5, dy: 10, scale: 1 });
  gesture.clear();
  assert.equal(gesture.move(1, 90, 100, false), null);
});
