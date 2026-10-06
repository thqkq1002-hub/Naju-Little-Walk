"""Publish only selected validated exports into the existing placements manifest."""
from pathlib import Path
import json,struct
root=Path(__file__).resolve().parents[1]
path=root/'public/npc-placements.json'
manifest=json.loads(path.read_text(encoding='utf-8'))
versions={'baedoli':'v6','beodeuri':'v6','hongdoli':'v6','teacher':'v6'}
manifest['version']=3
manifest['source']='사용자 지정 지역의 창작 안내 캐릭터. 실제 현장 인물이 아님. Meshy 7.1 채색 모델, Blender 맞춤 리깅과 다섯 가지 안내 동작. 배돌이 손 분리 참조 재생성, 버들낭자 팔과 치마 보정 v6.'
for character,version in versions.items():
    model=root/f'public/models/npc/{character}-{version}.glb'
    raw=model.read_bytes();length=struct.unpack_from('<I',raw,12)[0]
    gltf=json.loads(raw[20:20+length])
    pos=gltf['accessors'][gltf['meshes'][0]['primitives'][0]['attributes']['POSITION']]
    low,high=pos['min'],pos['max']
    asset=manifest['assets'][character]
    asset.update(modelUrl=f'/models/npc/{character}-{version}.glb',webBytes=len(raw),
                 width=high[0]-low[0],height=high[1]-low[1],depth=high[2]-low[2])
    base='assets/npc/meshy71-baedoli-clean-20261002' if character=='baedoli' else f'assets/npc/meshy71-rigged-20261002/{character}'
    asset['authoredExport']=f'{base}/{character}-rigged-{version}.glb'
path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
