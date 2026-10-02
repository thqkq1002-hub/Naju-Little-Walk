"""Protect unrelated authored geometry and match route geometry to world metadata."""
import bpy,json,hashlib,sys
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];revision='v69' if '--final' in sys.argv else 'v68' if '--junction-fix' in sys.argv else 'v67';P=R/('knowledge/sources/bitgaram/access-'+revision+'.json');report=json.loads(P.read_text(encoding='utf8'));removed=set(report['removed_objects']+report.get('modified_existing_meshes',[]))
def fingerprint(o):
 m=o.data;v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v);ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids);lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
 return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(R/report['source']));before={o.name:fingerprint(o) for o in bpy.context.scene.objects if o.type=='MESH' and o.name not in removed}
bpy.ops.wm.open_mainfile(filepath=str(R/report['output']));after={o.name:fingerprint(o) for o in bpy.context.scene.objects if o.name in before};assert after==before,'Unrelated artist geometry changed'
assert not any(o.name.startswith(('walk-floor_approach','timber_horizontal_rail','deck_plank_joint')) for o in bpy.context.scene.objects),'Old guessed path remains'
for name in ['mapped_monorail_508048300_beam','photo_monorail_cab_body','photo_stone_slide_U_trough','slide_gallery_timber_arch','slide_gallery_blue_side','walk-floor_mapped_forest_549492174','walk-floor_slide_side_stairs']:
 assert bpy.data.objects.get(name) is not None,name
world=json.loads((R/report['world_output']).read_text(encoding='utf8'));old=json.loads((R/report['world_source']).read_text(encoding='utf8'))
for key,value in old.items():
 if key not in ['solids','arrivals','places','bounds']:assert world[key]==value,key
assert world['places'][0]==old['places'][0] and world['arrivals']['start']==old['arrivals']['start']
assert abs(report['slide_authored_length']-96)<.00001
floors=[s for s in world['solids'] if s['name']=='walk-floor_mapped_forest_549492174'];assert len(floors)==len(report['forest_route'])-1
stairs=[s for s in world['solids'] if s['name']=='walk-floor_slide_side_stairs'];assert len(stairs)==len(report['stairs_route'])-1
for route,parts in [(report['forest_route'],floors),(report['stairs_route'],stairs)]:
 for a,b,s in zip(route,route[1:],parts):
  assert abs(s['position'][1]+s['size'][1]-(a[1]+b[1])/2)<1e-6
  assert abs(a[1]-b[1])<.36,'Unwalkable step height'
result={'protected_meshes':len(before),'unchanged_geometry_and_transforms':True,'mapped_monorail_way':'508048300','forest_floor_segments':len(floors),'gallery_stair_segments':len(stairs),'historic_slide_length':report['slide_authored_length'],'old_guessed_approach_removed':True,'other_world_state_unchanged':True}
(R/('knowledge/sources/bitgaram/access-'+revision+'-verification.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('ACCESS VERIFIED',json.dumps(result),flush=True)
