"""Reopen saved Blender revision and independently protect active geometry/world."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
report=json.loads((R/'knowledge/sources/bitgaram/shore-v75.json').read_text(encoding='utf8'))
removed=set(report['removed_objects']);cache={}
def fingerprint(o):
 m=o.data
 if m.as_pointer() not in cache:
  v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v);ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids);lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
  cache[m.as_pointer()]=v.tobytes()+ids.tobytes()+lengths.tobytes()
 return hashlib.sha256(cache[m.as_pointer()]+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(R/report['source']))
before={o.name:fingerprint(o) for o in bpy.context.scene.objects if o.type=='MESH' and o.name not in removed};cache.clear()
bpy.ops.wm.open_mainfile(filepath=str(R/report['output']))
after={o.name:fingerprint(o) for o in bpy.context.scene.objects if o.name in before}
assert before==after==report['protected_geometry'],'Protected geometry/placement changed'
assert not any(bpy.data.objects.get(n) for n in removed)
mesh=bpy.data.objects['mapped_park_lawn_shore_v75'];prepared=json.loads((R/'outputs/quality-v75/shore-surface-v75.json').read_text(encoding='utf8'))
assert len(mesh.data.vertices)==len(prepared['vertices']) and len(mesh.data.polygons)==len(prepared['faces'])
for v,p in zip(mesh.data.vertices,prepared['vertices']):assert np.allclose(v.co,(p[0],-p[2],p[1]),atol=.00005,rtol=0)
for f,p,mi in zip(mesh.data.polygons,prepared['faces'],prepared['material_indices']):assert set(f.vertices)==set(p) and f.material_index==mi
assert mesh.get('visual_context_only')==True
assert report['world_sha256']==hashlib.sha256((R/'public/bitgaram-park-world.json').read_bytes()).hexdigest()
assert report['geometry_source_sha256']==hashlib.sha256((R/'knowledge/sources/bitgaram/geometry.json').read_bytes()).hexdigest()
assert len(mesh.data.polygons)<report['old_surface_triangles']
result={'protected_meshes':len(before),'unchanged_geometry_and_transforms':True,'protected_water_meshes':[n for n in before if n.startswith('lake_osm_')],'hill_and_active_routes_unchanged':True,'world_unchanged':True,'geometry_source_unchanged':True,'saved_surface_matches_prepared_geometry':True,'old_surface_triangles':report['old_surface_triangles'],'new_surface_triangles':len(mesh.data.polygons),'estimated_bank_height_and_width':True,'visual_context_only':True}
(R/'knowledge/sources/bitgaram/shore-v75-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('SHORE VERIFIED',json.dumps(result),flush=True)
