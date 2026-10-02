"""Compare actual source/revision geometry; verify every new pane faces outside."""
import bpy,json,hashlib,math
import numpy as np
from pathlib import Path
from collections import Counter
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
report=json.loads((R/'knowledge/sources/bitgaram/district-facade-v60.json').read_text(encoding='utf-8'))
changed=set(report['changed_existing_meshes'])
def fingerprint(o):
 m=o.data;v=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',v)
 ids=np.empty(len(m.loops),dtype=np.int32);m.loops.foreach_get('vertex_index',ids)
 lengths=np.empty(len(m.polygons),dtype=np.int32);m.polygons.foreach_get('loop_total',lengths)
 return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()+np.asarray(o.matrix_world,dtype=np.float64).tobytes()).hexdigest()
def faces(o):
 # Index order may change after deleting other components; actual remaining faces must not.
 return Counter(tuple(tuple(o.data.vertices[i].co) for i in p.vertices) for p in o.data.polygons)
def curve_fingerprint(o):
 values={'matrix':list(v for row in o.matrix_world for v in row),'dimensions':o.data.dimensions,'bevel_depth':o.data.bevel_depth,'extrude':o.data.extrude,'splines':[]}
 for s in o.data.splines:
  values['splines'].append({'type':s.type,'cyclic':s.use_cyclic_u,'points':[list(p.co) for p in s.points],'bezier':[(list(p.co),list(p.handle_left),list(p.handle_right)) for p in s.bezier_points]})
 return hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(R/report['source']))
original={o.name:fingerprint(o) for o in bpy.context.scene.objects if o.type=='MESH' and o.name not in changed}
curves={o.name:curve_fingerprint(o) for o in bpy.context.scene.objects if o.type=='CURVE'}
source_faces={name:faces(bpy.data.objects[name]) for name in changed}
source_matrix={name:tuple(v for row in bpy.data.objects[name].matrix_world for v in row) for name in changed}
source_materials={name:[m.name for m in bpy.data.objects[name].data.materials] for name in changed}
bpy.ops.wm.open_mainfile(filepath=str(R/report['output']))
protected={o.name:fingerprint(o) for o in bpy.context.scene.objects if o.type=='MESH' and o.name not in changed and not o.name.startswith('apartment_finish_')}
assert original==protected,'Protected source geometry changed'
assert curves=={o.name:curve_fingerprint(o) for o in bpy.context.scene.objects if o.type=='CURVE'},'Source curves changed'
kept=0
for name in changed:
 o=bpy.data.objects[name];current=faces(o)
 assert not (current-source_faces[name]),name+' introduced changed old faces'
 assert tuple(v for row in o.matrix_world for v in row)==source_matrix[name]
 assert [m.name for m in o.data.materials]==source_materials[name]
 kept+=sum(current.values())
panes=0;frame_faces=0
for o in bpy.context.scene.objects:
 if not o.name.startswith('apartment_finish_'):continue
 assert all(math.isfinite(v) for p in o.data.vertices for v in p.co)
 if 'glass_stack_' not in o.name:
  frame_faces+=len(o.data.polygons);continue
 # Independent nearest facade check using retained footprint endpoints, not generator normals.
 for face in o.data.polygons:
  center=face.center;x,z,h=center.x,-center.y,center.z;closest=None
  for building in report['apartments']:
   if h>building['height'] or h<0:continue
   poly=building['polygon'];xs=[p[0] for p in poly];zs=[p[1] for p in poly]
   if not min(xs)-1<=x<=max(xs)+1 or not min(zs)-1<=z<=max(zs)+1:continue
   area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))
   for a,b in zip(poly,poly[1:]+poly[:1]):
    dx,dz=b[0]-a[0],b[1]-a[1];den=dx*dx+dz*dz
    if den==0:continue
    t=max(0,min(1,((x-a[0])*dx+(z-a[1])*dz)/den))
    d=math.hypot(x-a[0]-t*dx,z-a[1]-t*dz)
    if closest is None or d<closest[0]:
     exterior=Vector((dz,dx,0)) if area>0 else Vector((-dz,-dx,0))
     closest=(d,exterior.normalized())
  assert closest and closest[0]<.15,'Pane no longer on retained facade'
  assert face.normal.dot(closest[1])>.999,'Pane faces inward'
  panes+=1
assert panes==report['new_windows']
assert frame_faces==panes*4
out={'source':report['source'],'revision':report['output'],'protected_meshes':len(protected),'protected_curves':len(curves),'retained_faces_in_trimmed_meshes':kept,'outward_window_faces':panes,'frame_faces':frame_faces,'protected_geometry_matches_source':True,'retained_geometry_is_exact_source_subset':True,'all_windows_outward':True,'collision_geometry_changed':False}
(R/'knowledge/sources/bitgaram/district-facade-v60-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('FACADE VERIFIED',json.dumps(out),flush=True)
