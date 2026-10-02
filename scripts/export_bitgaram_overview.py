"""Export the existing Blender overview without modifying its editable source."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-overview.blend'))
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/bitgaram-overview.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
data=json.loads((root/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf-8'))
ids={'656235304':('bitgaram-park','호수공원 · 전망대',34),'594386007':('bitgaram-kepco','한국전력 본사',154),'1065747586':('bitgaram-kentech','KENTECH',18)}
pins=[]
for w in data['ways']:
    if w['id'] not in ids:continue
    key,label,y=ids[w['id']];pts=w['points']
    pins.append(dict(id=key,label=label,position=[sum(p[0] for p in pts)/len(pts),y,sum(p[1] for p in pts)/len(pts)]))
(root/'public/bitgaram-orbit.json').write_text(json.dumps(dict(pins=pins),ensure_ascii=False),encoding='utf-8')
