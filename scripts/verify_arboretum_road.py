"""Verify preserved scene, unoccluded asphalt and synchronized walking floors."""
import bpy,json,math,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];report=json.loads((R/'knowledge/sources/arboretum/juniper-road-v65.json').read_text(encoding='utf-8'));changed=set(report['trimmed_research_rows']+report['raised_asphalt_surfaces'])
def fingerprint(o):
 m=o.data;v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v);ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids);lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
 return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(R/report['source']));before={o.name:fingerprint(o) for o in bpy.context.scene.objects if o.type=='MESH' and o.name not in changed};matrices={o.name:np.asarray(o.matrix_world).copy() for o in bpy.context.scene.objects if o.type=='MESH'}
bpy.ops.wm.open_mainfile(filepath=str(R/report['output']));bpy.context.view_layer.update();actual={o.name:fingerprint(o) for o in bpy.context.scene.objects if o.type=='MESH' and o.name not in changed};assert actual==before
vertices=[];faces=[];owners=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 assert np.allclose(np.asarray(o.matrix_world),matrices[o.name],atol=1e-6,rtol=0),'Object moved while trimming rows'
 if not o.name.startswith(('nursery_row','mapped_path_')):continue
 points=[o.matrix_world@v.co for v in o.data.vertices];index=len(vertices);vertices.extend(points)
 for face in o.data.polygons:faces.append([index+i for i in face.vertices]);owners.append(o.name)
tree=BVHTree.FromPolygons(vertices,faces,all_triangles=False);data=json.loads((R/'knowledge/sources/arboretum/geometry.json').read_text(encoding='utf-8'));road=next(w for w in data['ways'] if w['id']=='1258471015')['points'];probes=0
for a,b in zip(road,road[1:]):
 a,b=Vector(a),Vector(b);axis=(b-a).normalized();side=Vector((-axis.y,axis.x))
 for i in range(100):
  for offset in [-1.4,0,1.4]:
   p=a.lerp(b,(i+.5)/100)+side*offset;point,normal,index,d=tree.ray_cast(Vector((p.x,-p.y,1)),Vector((0,0,-1)),2)
   assert index is not None and owners[index].startswith('mapped_path_1258471015'),'Research planting still occludes asphalt'
   assert abs(point.z-report['surface_height'])<.00001;probes+=1
old=json.loads((R/report['world_source']).read_text(encoding='utf-8'));world=json.loads((R/report['world_output']).read_text(encoding='utf-8'));assert world['solids']==old['solids']+report['walking_floors'];assert world['verticalNavigation'] is True
for floor in report['walking_floors']:assert abs(floor['position'][1]+floor['size'][1]/2-report['surface_height'])<.000001
for key,value in old.items():
 if key not in ['solids','verticalNavigation','arrivals','places']:assert world[key]==value
for key,value in old['arrivals'].items():
 if key!='juniper':assert world['arrivals'][key]==value
assert world['arrivals']['juniper']==dict(old['arrivals']['juniper'],height=report['surface_height'])
for a,b in zip(old['places'],world['places']):assert b==(dict(a,arrivalHeight=report['surface_height']) if a['id']=='juniper' else a)
result={'source':report['source'],'revision':report['output'],'protected_meshes':len(before),'protected_geometry_matches_source':True,'trimmed_overlapping_research_rows':len(report['trimmed_research_rows']),'retained_all_object_transforms':True,'clear_asphalt_probes':probes,'walking_surface_matches_model':True,'new_walking_floors':len(report['walking_floors']),'other_world_state_unchanged':True}
(R/'knowledge/sources/arboretum/juniper-road-v65-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('ROAD VERIFIED',json.dumps(result),flush=True)
