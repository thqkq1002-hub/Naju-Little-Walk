"""Read-only inventory for lake/land surface comparison."""
import bpy,json,sys,collections
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/quality-v69/bitgaram-access-v69.blend'))
scene=bpy.context.scene;rows=[]
for o in scene.objects:
 if o.type!='MESH':continue
 if any(t in o.name.lower() for t in ['lake','lawn','ground','bank','hill','shore','mapped_paths']):
  corners=[o.matrix_world@Vector(p) for p in o.bound_box]
  rows.append({'name':o.name,'verts':len(o.data.vertices),'faces':len(o.data.polygons),'bounds':[[min(v[i] for v in corners),max(v[i] for v in corners)] for i in range(3)],'materials':[m.name if m else None for m in o.data.materials],'extras':dict(o.items())})
ways=json.loads((R/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf8'))['ways']
water=[{'id':w['id'],'tags':w['tags'],'points':w['points']} for w in ways if w['tags'].get('natural')=='water']
report={'source':'outputs/quality-v69/bitgaram-access-v69.blend','mesh_count':sum(o.type=='MESH' for o in scene.objects),'surfaces':rows,'mapped_water':water}
(R/'work/bitgaram-shore-inventory-v75.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
counts=collections.Counter('lake' if o['name'].startswith('lake') else 'bank' if 'bank' in o['name'] else 'shore' if 'shore' in o['name'] else o['name'] for o in rows)
print('SURFACE INVENTORY',json.dumps({'mesh_count':report['mesh_count'],'categories':dict(counts),'water':[{'id':w['id'],'points':len(w['points']),'tags':w['tags']} for w in water]},ensure_ascii=False),flush=True)
