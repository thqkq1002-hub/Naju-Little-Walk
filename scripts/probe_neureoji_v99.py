import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/neureoji-polish-v98/neureoji-polish-v98.blend'))
out=[]
for o in bpy.context.scene.objects:
 if o.name.startswith(('tower_','walk-floor_top','Neureoji94_')) and o.type=='MESH':out.append(dict(name=o.name,materials=[m.name for m in o.data.materials],vertices=len(o.data.vertices)))
for m in bpy.data.materials:
 if m.name.startswith(('Neureoji95_leaf_','Neureoji94_bloom_cutout','Neureoji93_')):out.append(dict(material=m.name,color=list(m.diffuse_color)))
p=R/'work/neureoji-v99/probe.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2),encoding='utf8');print('PROBE_COMPLETE',len(out))
