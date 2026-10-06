import bpy,json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/palette-v51/geumseonggwan-color-v51.blend'))
scene=bpy.context.scene
summary={'scene':scene.name,'objects':len(scene.objects),'collections':list(bpy.data.collections.keys()),'prefixes':collections.Counter(o.name.split('.')[0] for o in scene.objects).most_common(55),'materials':len(bpy.data.materials),'sourceImages':len(bpy.data.images),'selectedObjects':[]}
for o in scene.objects:
    if o.name in ['roof_832423358','roof_832423358_back','roof_west_wing','roof_east_wing','ground_geumseonggwan_boundary','ground_floor_hall','photo-tree_trunk','photo-tree_fine_foliage','Overview_camera']:
        summary['selectedObjects'].append({'name':o.name,'type':o.type,'location':list(o.location),'bounds':[list(o.matrix_world@__import__('mathutils').Vector(v)) for v in o.bound_box],'materials':[m.name for m in o.data.materials] if o.type=='MESH' else []})
(ROOT/'outputs/geumseonggwan-exclusive-v76/source-inspection.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print('INSPECTION_COMPLETE',len(scene.objects),flush=True)
