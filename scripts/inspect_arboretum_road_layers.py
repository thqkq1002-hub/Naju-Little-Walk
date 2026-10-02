"""Read-only ground ray inspection along the mapped road."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/quality-v64/naju-arboretum-juniper-avenue-v64.blend'))
vertices=[];faces=[];owners=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.get('authored_vegetation') or o.get('vegetation_lod'):continue
 p=[o.matrix_world@v.co for v in o.data.vertices]
 if not p or max(v.z for v in p)>1:continue
 index=len(vertices);vertices.extend(p)
 for face in o.data.polygons:faces.append([index+i for i in face.vertices]);owners.append(o.name)
tree=BVHTree.FromPolygons(vertices,faces,all_triangles=False)
data=json.loads((R/'knowledge/sources/arboretum/geometry.json').read_text(encoding='utf-8'));road=next(w for w in data['ways'] if w['id']=='1258471015')['points']
for a,b in zip(road,road[1:]):
 for t in [.15,.35,.55,.75,.95]:
  x=a[0]*(1-t)+b[0]*t;z=a[1]*(1-t)+b[1]*t;origin=Vector((x,-z+.8,1));hits=[]
  for _ in range(3):
   p,n,index,d=tree.ray_cast(origin,Vector((0,0,-1)),3)
   if index is None:break
   hits.append((owners[index],round(p.z,4)));origin=p+Vector((0,0,-.0001))
  print('ROAD LAYERS',round(x,2),round(z,2),hits,flush=True)
