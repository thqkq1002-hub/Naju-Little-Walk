"""Continuous clipped evergreen habits, guarded revision after garden v61."""
import bpy,bmesh,math,random,json,ast,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v62';O.mkdir(parents=True,exist_ok=True)
source=R/'outputs/quality-v61/naju-arboretum-garden-v61-soft.blend'
target=O/'naju-arboretum-junipers-v62.blend'
if target.exists():raise RuntimeError('Existing artist revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
tree=ast.parse((R/'scripts/arboretum_botanical_finish.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PlantMesh'],type_ignores=[]),'<PlantMesh>','exec'))
bark=bpy.data.materials['Authored_bark_grain'];dense=bpy.data.materials['Reference_dense_foliage']
def material(name,rgb):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*rgb,1);m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*rgb,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.86;m.use_backface_culling=False;return m
greens=[material('Clipped_juniper_spray_'+str(i),c) for i,c in enumerate([(.042,.105,.018),(.062,.144,.025),(.080,.176,.039)])]
materials=[bark,dense,*greens]
def habit(o):
 value=o.get('reference_habit')
 if value:return value
 if o.name.startswith('distant_'):
  original=scene.objects.get(o.name[len('distant_'):])
  if original:return original.get('reference_habit')
 return None
old_meshes={(habit(o),o.get('vegetation_lod')):o.data for o in scene.objects if o.type=='MESH' and habit(o) in ['column','oval']}
def build(kind,lod,variant):
 detail=lod=='near';p=PlantMesh();rr=random.Random(6200+variant*97+(0 if kind=='column' else 401));h=8.4 if kind=='column' else 6.2
 # Leaf-bearing volume is continuous; no stack of separate ellipsoids.
 profile=[(0,.52),(.12,.87),(.27,.91),(.43,.76),(.62,.53),(.80,.29),(.94,.11),(1,.002)] if kind=='column' else [(0,.43),(.12,.74),(.29,.95),(.47,1),(.65,.94),(.81,.75),(.94,.41),(1,.002)]
 radius=1.35 if kind=='column' else 2.12;bottom=.12;top=h-.08
 def width(t):
  for (a,x),(b,y) in zip(profile,profile[1:]):
   if t<=b:
    f=(t-a)/(b-a);return radius*(x+(y-x)*f)
  return .002*radius
 def surface(t,a):
  r=width(t)*(1+.036*math.sin(a*7+t*31+variant)+.025*math.sin(a*13-t*53+variant*.7))
  center=Vector((.055*math.sin(t*3+variant)*t,bottom+(top-bottom)*t,.045*math.sin(t*4+variant)*t))
  return center+Vector((r*math.cos(a),0,r*math.sin(a)))
 p.tube((0,0,0),(0,h,0),.18,.016,0,n=9 if detail else 6)
 seg=40 if detail else 24;rows=40 if detail else 26
 for j in range(rows):
  for k in range(seg):
   a,b=k*math.tau/seg,(k+1)*math.tau/seg;t,u=j/rows,(j+1)/rows
   p.face([surface(t,a),surface(t,b),surface(u,b),surface(u,a)],1,[(k/seg,t*3),((k+1)/seg,t*3),((k+1)/seg,u*3),(k/seg,u*3)])
 # Tiny folded scale-leaf sprays interrupt the outline without large blades.
 for j in range(390 if detail else 55):
  t=rr.uniform(.018,.98);a=rr.random()*math.tau;c=surface(t,a);normal=Vector((math.cos(a),.28,math.sin(a))).normalized();tangent=Vector((-math.sin(a),.15,math.cos(a))).normalized()
  axis=(normal*.55+Vector((0,1,0))*.62+tangent*rr.uniform(-.32,.32)).normalized();length=rr.uniform(.11,.20)
  tip=c+axis*length;p.tube(c,tip,.002,.0008,2,n=3)
  for q in range(5 if detail else 3):
   root=c+axis*length*(.12+.16*q)
   for sign in [-1,1]:
    end=root+tangent*(sign*length*(.46-.045*q))+axis*length*.22
    mid=root.lerp(end,.52)+normal*.008;w=axis*length*.09
    p.face([root,mid-w,end,mid+normal*.004],2+j%3,[(.5,0),(0,.5),(.5,1),(.5,.5)])
    p.face([root,mid+normal*.004,end,mid+w],2+j%3,[(.5,0),(.5,.5),(.5,1),(1,.5)])
 mesh=p.finish('Clipped_'+kind+'_'+lod+'_'+str(variant),materials)
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()
 # Stay within the former mesh bounds. Preserve trunk origin and original height.
 old=np.asarray([v.co[:] for v in old_meshes[kind,lod].vertices]);new=np.asarray([v.co[:] for v in mesh.vertices]);scale=[1.,1.,old[:,2].max()/new[:,2].max()]
 for axis in [0,1]:
  pos=old[:,axis].max()/new[:,axis].max();neg=old[:,axis].min()/new[:,axis].min();scale[axis]=min(1,pos,neg)*.995
 for v in mesh.vertices:
  for axis in range(3):v.co[axis]*=scale[axis]
 mesh.update();return mesh
def fingerprint(o):
 m=o.data;v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v);ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids);lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
 return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
protos={(kind,lod,v):build(kind,lod,v) for kind in ['column','oval'] for lod in ['near','far'] for v in range(3)}
changed={};counts={}
for o in scene.objects:
 if o.type!='MESH' or habit(o) not in ['column','oval']:continue
 kind=habit(o);lod=o['vegetation_lod'];variant=int(hashlib.sha256((','.join(str(round(x,3)) for x in o.location)).encode()).hexdigest()[:8],16)%3
 before=np.asarray([v.co[:] for v in o.data.vertices]);old=o.data.name
 o.data=protos[kind,lod,variant];o['reference_habit']=kind;o['juniper_revision']='Continuous photo-informed clipped habit v62; species and size estimated';o['juniper_variant']=variant
 changed[o.name]={'original_mesh':old,'habit':kind,'lod':lod,'variant':variant,'matrix':[v for row in o.matrix_world for v in row],'bounds_before':[before.min(axis=0).tolist(),before.max(axis=0).tolist()]};counts[kind+'_'+lod]=counts.get(kind+'_'+lod,0)+1
report={'source':str(source.relative_to(R)),'output':str(target.relative_to(R)),'changed_objects':changed,'protected_geometry_hashes':{o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o.name not in changed},'world_sha256':hashlib.sha256((R/'public/naju-arboretum-world.json').read_bytes()).hexdigest(),'counts':counts,'shared_prototypes':len(protos),'reference':'https://hangamja.tistory.com/1607','limitation':'2021 photograph informs silhouette; original interpreted planting coordinates and inferred species/height retained.'}
(R/'knowledge/sources/arboretum/juniper-quality-v62.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.context.view_layer.update();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(O/'naju-arboretum-v62.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
print('JUNIPER FINISH',counts,flush=True)
