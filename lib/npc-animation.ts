import * as THREE from 'three';

export type GuideGesture = 'Idle' | 'Greeting' | 'Explain' | 'Nod' | 'Listen';
export const guideGestures: GuideGesture[] = ['Idle', 'Greeting', 'Explain', 'Nod', 'Listen'];

/** Smooth transitions between authored skeleton clips; never move the character's feet. */
export class NpcAnimation {
  readonly root: THREE.Object3D;
  readonly mixer: THREE.AnimationMixer;
  private readonly actions = new Map<GuideGesture, THREE.AnimationAction>();
  private active: THREE.AnimationAction | undefined;
  gesture: GuideGesture = 'Idle';
  reducedMotion = false;
  private readonly finished = (event:{action:THREE.AnimationAction}) => {if(event.action===this.active)this.setGesture('Idle');};

  constructor(root: THREE.Object3D, clips: THREE.AnimationClip[]) {
    this.root=root;
    this.mixer = new THREE.AnimationMixer(root);
    for (const name of guideGestures) {
      const clip = clips.find(c => c.name === name || c.name.endsWith(`_${name}`));
      if (!clip) throw new Error(`안내 캐릭터의 ${name} 동작이 없습니다.`);
      this.actions.set(name, this.mixer.clipAction(clip));
    }
    this.mixer.addEventListener('finished', this.finished);
    this.setGesture('Idle');
    this.mixer.update(0);
  }

  setGesture(name: GuideGesture) {
    if (this.active && this.gesture === name) return;
    const next = this.actions.get(name)!;
    const previous = this.active;
    next.reset().setEffectiveWeight(1).setEffectiveTimeScale(1);
    const once = name === 'Greeting' || name === 'Nod';
    next.setLoop(once ? THREE.LoopOnce : THREE.LoopRepeat, once ? 1 : Infinity);
    next.clampWhenFinished = once;
    next.fadeIn(.35).play();
    if (previous && previous !== next) previous.fadeOut(.35);
    this.active = next;
    this.gesture = name;
  }

  update(dt: number) { if (!this.reducedMotion) this.mixer.update(Math.min(Math.max(dt, 0), .06)); }
  dispose() {
    this.mixer.removeEventListener('finished', this.finished);
    this.mixer.stopAllAction();
    this.mixer.uncacheRoot(this.root);
    this.root.traverse(o => { if (o instanceof THREE.SkinnedMesh) o.skeleton.dispose(); });
  }
}
