import bpy,json,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/monorail-v83/bitgaram-park-monorail-v83.blend'))
rows=[]
for o in bpy.context.scene.objects:
 if o.type in ('MESH','FONT'):
  coords=[o.matrix_world@v.co for v in o.data.vertices] if o.type=='MESH' else [o.matrix_world@__import__('mathutils').Vector(v) for v in o.bound_box]
  bounds=[[min(p[i] for p in coords),max(p[i] for p in coords)] for i in range(3)] if coords else None
  rows.append(dict(name=o.name,type=o.type,location=list(o.location),bounds=bounds,vertices=len(coords),data=o.data.name,shared=o.data.users,extras=dict(o.items())))
(R/'work/bitgaram-terrain-v89/scene-inspection.json').write_text(json.dumps(rows,ensure_ascii=False),encoding='utf8')
print('objects',len(rows),'prefixes',dict(collections.Counter(r['name'].split('.')[0] for r in rows)),flush=True)
