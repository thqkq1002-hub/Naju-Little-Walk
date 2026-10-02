"""Verify map alignment, exact prior geometry, markings and collision inventory."""
import bpy,json,hashlib,math,sys
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];revision='v64' if '--clear-crossings' in sys.argv else 'v63';P=R/('knowledge/sources/arboretum/juniper-avenue-'+revision+'.json');report=json.loads(P.read_text(encoding='utf-8'));moved=report['moved_trees']
def geometry(o):
 m=o.data;v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v);ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids);lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
 return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(R/report['source']));before={o.name:(geometry(o),np.asarray(o.matrix_world).copy()) for o in bpy.context.scene.objects if o.type=='MESH'}
bpy.ops.wm.open_mainfile(filepath=str(R/report['output']));bpy.context.view_layer.update();actual={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
assert set(actual)==set(before)|set(report['new_markings'])
for name,(shape,matrix) in before.items():
 o=actual[name];assert geometry(o)==shape,'Existing geometry changed: '+name
 new=np.asarray(o.matrix_world)
 if name in moved:
  assert np.allclose(new[:3,:3],matrix[:3,:3],atol=1e-6,rtol=0)
  assert abs(new[2,3]-matrix[2,3])<.00001
  assert math.hypot(new[0,3]-moved[name]['after'][0],-new[1,3]-moved[name]['after'][1])<.0001
 else:assert np.allclose(new,matrix,atol=1e-6,rtol=0),'Unrelated object moved'
near=[];far=[]
for o in actual.values():
 lod=o.get('vegetation_lod')
 if lod:
  key=tuple(round(v,5) for row in o.matrix_world for v in row)+(o.get('vegetation_distance'),o.get('juniper_variant',-1))
  (near if lod=='near' else far).append(key)
assert sorted(near)==sorted(far)
for name in report['new_markings']:
 o=actual[name];assert all(p.normal.z>.999 for p in o.data.polygons),'Road marking face is downward'
 assert all(abs(v.co.z-.106)<.000001 for v in o.data.vertices)
world_before=json.loads((R/'public/naju-arboretum-world.json').read_text(encoding='utf-8'));world=json.loads((R/report['world_output']).read_text(encoding='utf-8'))
assert hashlib.sha256((R/'public/naju-arboretum-world.json').read_bytes()).hexdigest()==report['world_before_sha256']
old_solids=world_before['solids'].copy()
for item in report['updated_colliders']:
 assert item['before'] in old_solids and item['after'] in world['solids'];old_solids.remove(item['before'])
 o=actual[item['tree']];position=item['after']['position'];assert math.hypot(o.location.x-position[0],-o.location.y-position[2])<.0001
 radius=item['after']['size'][0]/2;assert radius>=max(math.hypot(v.co.x*o.scale.x,v.co.y*o.scale.y) for v in o.data.vertices)-.00001
for item in report['removed_ghost_colliders']:assert item in old_solids;old_solids.remove(item)
new_solids=[s for s in world['solids'] if s not in [item['after'] for item in report['updated_colliders']]]
assert old_solids==new_solids,'Other collisions changed'
for key,value in world_before.items():
 if key not in ['solids','arrivals','places']:assert world[key]==value
for key,value in world_before['arrivals'].items():assert world['arrivals'][key]==value
for old,new in zip(world_before['places'],world['places']):
 if old['id']!='juniper':assert old==new
result={'source':report['source'],'revision':report['output'],'preserved_mesh_geometry':len(before),'retained_object_matrices':len(before)-len(moved),'moved_avenue_trees':len(moved)//2,'updated_matching_colliders':len(report['updated_colliders']),'removed_verified_ghosts':len(report['removed_ghost_colliders']),'upward_road_markings':len(report['new_markings']),'paired_vegetation_instances':len(near),'other_world_state_unchanged':True}
(R/('knowledge/sources/arboretum/juniper-avenue-'+revision+'-verification.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('AVENUE VERIFIED',json.dumps(result),flush=True)
