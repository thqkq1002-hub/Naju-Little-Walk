"""Keep the mapped asphalt visible through research rows; sync walking floors."""
import bpy,bmesh,json,math,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v65';O.mkdir(parents=True,exist_ok=True);source=R/'outputs/quality-v64/naju-arboretum-juniper-avenue-v64.blend';target=O/'naju-arboretum-juniper-road-v65.blend'
if target.exists():raise RuntimeError('Existing artist revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
world=json.loads((R/'outputs/quality-v64/naju-arboretum-world-v64.json').read_text(encoding='utf-8'));data=json.loads((R/'knowledge/sources/arboretum/geometry.json').read_text(encoding='utf-8'));road=next(w for w in data['ways'] if w['id']=='1258471015')['points']
def fingerprint(o):
 m=o.data;v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v);ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids);lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
 return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
original={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH'}
def area(p):return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1])))/2 if len(p)>=3 else 0
def intersect(subject,clip):
 result=subject
 for a,b in zip(clip,clip[1:]+clip[:1]):
  if not result:break
  output=[];previous=result[-1]
  def side(p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
  for current in result:
   x,y=side(previous),side(current)
   if (x>=0)!=(y>=0):
    t=x/(x-y);output.append((previous[0]+(current[0]-previous[0])*t,previous[1]+(current[1]-previous[1])*t))
   if y>=0:output.append(current)
   previous=current
  result=output
 return result
cutters=[];footprints=[]
for index,(a,b) in enumerate(zip(road,road[1:])):
 a,b=Vector(a),Vector(b);axis=(b-a).normalized();side=Vector((-axis.y,axis.x));poly=[a-side*1.91,b-side*1.91,b+side*1.91,a+side*1.91];footprints.append([list(p) for p in poly])
 verts=[(p.x,-p.y,z) for z in [-.05,.7] for p in poly];faces=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
 mesh=bpy.data.meshes.new('Temporary road trim');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('__temporary_road_cutter_'+str(index),mesh);scene.collection.objects.link(o);cutters.append(o)
changed_rows=[]
for o in list(scene.objects):
 if o.type!='MESH' or not o.name.startswith('nursery_row'):continue
 points={(round((o.matrix_world@v.co).x,6),round(-(o.matrix_world@v.co).y,6)) for v in o.data.vertices};cx=sum(p[0] for p in points)/len(points);cz=sum(p[1] for p in points)/len(points);poly=sorted(points,key=lambda p:math.atan2(p[1]-cz,p[0]-cx))
 selected=[i for i,p in enumerate(footprints) if area(intersect(poly,p))>.00001]
 if not selected:continue
 bpy.context.view_layer.objects.active=o;o.select_set(True)
 for i in selected:
  modifier=o.modifiers.new('Trim field planting over mapped road','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutters[i];bpy.ops.object.modifier_apply(modifier=modifier.name)
 o.select_set(False);changed_rows.append(o.name)
for o in cutters:bpy.data.objects.remove(o,do_unlink=True)
changed_roads=[]
for o in scene.objects:
 if o.type!='MESH' or not o.name.startswith('mapped_path_1258471015'):continue
 inverse=o.matrix_world.inverted();count=0
 for v in o.data.vertices:
  p=o.matrix_world@v.co
  if abs(p.z-.1)<.00001:p.z=.102;v.co=inverse@p;count+=1
 assert count>=4;o.data.update();changed_roads.append(o.name)
floors=[]
for index,(a,b) in enumerate(zip(road,road[1:])):
 a,b=Vector(a),Vector(b);axis=(b-a).normalized();side=Vector((-axis.y,axis.x));poly=[a-side*1.90,b-side*1.90,b+side*1.90,a+side*1.90]
 floors.append({'name':'walk-floor-juniper-asphalt-'+str(index),'kind':'box','position':[0,.051,0],'size':[0,.102,0],'footprint':[list(p) for p in poly],'color':'#333638','collision':False,'reference':'Existing OSM path 1258471015; authored surface elevation'})
world['solids'].extend(floors);world['verticalNavigation']=True;world['arrivals']['juniper']['height']=.102;world['places']=[dict(p,arrivalHeight=.102) if p['id']=='juniper' else p for p in world['places']]
bpy.context.view_layer.update();changed=set(changed_rows+changed_roads)
report={'source':str(source.relative_to(R)),'output':str(target.relative_to(R)),'world_source':'outputs/quality-v64/naju-arboretum-world-v64.json','world_output':'outputs/quality-v65/naju-arboretum-world-v65.json','trimmed_research_rows':changed_rows,'raised_asphalt_surfaces':changed_roads,'walking_floors':floors,'protected_geometry_hashes':{name:sha for name,sha in original.items() if name not in changed},'surface_height':.102,'limitation':'Only planted row portions overlapping the retained mapped road are trimmed. Paving and marking colours and planting positions remain estimates.'}
(O/'naju-arboretum-world-v65.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8');(R/'knowledge/sources/arboretum/juniper-road-v65.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target));bpy.ops.export_scene.gltf(filepath=str(O/'naju-arboretum-v65.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
print('ROAD FINISHED',len(changed_rows),len(changed_roads),len(floors),flush=True)
