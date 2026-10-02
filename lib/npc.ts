import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { batchStaticScene } from './static-scene.ts';
import { unpackModel } from './model-transport.ts';
import type { Point } from './world.ts';

export type NpcDefinition = { id: string; name: string; modelUrl: string; position: Point; height?: number; yaw: number; radius: number; lines: string[] };

export class NpcTroupe {
  private members: { definition: NpcDefinition; object: THREE.Group }[] = [];
  constructor(private definitions: NpcDefinition[]) {}
  async load(scene: THREE.Scene) {
    const loader = new GLTFLoader();
    const cache = new Map<string, THREE.Group>();
    for (const definition of this.definitions) {
      let template = cache.get(definition.modelUrl);
      if (!template) {
        const response = await fetch(definition.modelUrl);
        if (!response.ok) throw new Error(`${definition.name} 모델을 불러오지 못했습니다.`);
        const isPacked = definition.modelUrl.split('?')[0].endsWith('.gz');
        const gltf = isPacked ? await loader.parseAsync(await unpackModel(await response.arrayBuffer()), '') : await loader.loadAsync(definition.modelUrl);
        gltf.scene.traverse(o => { if (o instanceof THREE.Mesh) { o.castShadow = true; o.receiveShadow = true; } });
        batchStaticScene(gltf.scene);
        template = gltf.scene;
        cache.set(definition.modelUrl, template);
      }
      const object = template.clone(true);
      object.position.set(definition.position[0], definition.height ?? 0, definition.position[1]);
      object.rotation.y = definition.yaw;
      scene.add(object);
      this.members.push({ definition, object });
    }
  }
  nearest(x: number, z: number): NpcDefinition | undefined {
    let found: NpcDefinition | undefined, best = Infinity;
    for (const { definition } of this.members) {
      const d = Math.hypot(definition.position[0] - x, definition.position[1] - z);
      if (d < definition.radius && d < best) { best = d; found = definition; }
    }
    return found;
  }
}
