import bpy, json, sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
O=R/'work/observatory-relief-v96';O.mkdir(parents=True,exist_ok=True)
for key,source in [('neureoji',R/'outputs/neureoji-v95/neureoji-hydrangea-v95c.blend'),
                   ('bitgaram-park',R/'outputs/terrain-v89/bitgaram-park-glo30-terrain-v89d.blend')]:
    bpy.ops.wm.open_mainfile(filepath=str(source))
    rows=[]
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':continue
        pts=[ob.matrix_world@Vector(v) for v in ob.bound_box]
        rows.append(dict(name=ob.name,vertices=len(ob.data.vertices),
                         bounds=[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)],
                         extras=dict(ob.items())))
    (O/(key+'-objects.json')).write_text(json.dumps(rows,ensure_ascii=False,default=str),encoding='utf8')
    print(key,len(rows),flush=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(R/'public/models/bitgaram-overview.glb'))
rows=[]
for ob in bpy.context.scene.objects:
    if ob.type!='MESH':continue
    pts=[ob.matrix_world@Vector(v) for v in ob.bound_box]
    rows.append(dict(name=ob.name,vertices=len(ob.data.vertices),bounds=[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)]))
(O/'overview-objects.json').write_text(json.dumps(rows),encoding='utf8')
print('overview',len(rows),flush=True)
