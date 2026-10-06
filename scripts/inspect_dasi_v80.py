import bpy,json,hashlib
from pathlib import Path
from collections import Counter
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/dasi-v80';O.mkdir(exist_ok=True)
source=R/'outputs/palette-v51/dasi-neighborhood-color-v51.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
objects=[]
for o in bpy.context.scene.objects:
    if o.type!='MESH':continue
    pts=[o.matrix_world@Vector(v) for v in o.bound_box]
    objects.append(dict(name=o.name,materials=[m.name for m in o.data.materials if m],lo=[min(v[i] for v in pts) for i in range(3)],hi=[max(v[i] for v in pts) for i in range(3)],props=dict(o.items()),vertices=len(o.data.vertices)))
report=dict(sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),objects=objects,materials=[dict(name=m.name,color=list(m.diffuse_color),images=[n.image.name for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image])for m in bpy.data.materials if m.use_nodes])
(O/'before-inspection.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('COUNTS',len(objects),len(report['materials']))
print('NAMES',list(Counter(o['name'].split('_')[0].split('-')[0] for o in objects).items()))
for o in objects:
    if any(v in o['name'] for v in ['ivy','roof_beam','roof_support','main_roof','emblem','cutaway']):print(json.dumps(o))
