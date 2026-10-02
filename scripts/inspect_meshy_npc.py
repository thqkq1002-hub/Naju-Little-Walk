import bpy, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/npc-meshy-20261002'
results={}
for key in ['baedoli','beodeuri','hongdoli','teacher']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(OUT/key/'meshy-original.glb'))
    rows=[]
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH': continue
        points=[ob.matrix_world@Vector(c) for c in ob.bound_box]
        rows.append({'name':ob.name,'vertices':len(ob.data.vertices),'faces':len(ob.data.polygons),
                     'bounds':[[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)],
                     'materials':[m.name for m in ob.data.materials], 'matrix':[list(r) for r in ob.matrix_world]})
    results[key]=rows
(OUT/'mesh-inventory.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results))
