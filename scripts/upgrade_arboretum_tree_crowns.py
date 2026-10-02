"""Guarded photo-informed foliage revision; wood and planted transforms retained."""
import bpy,bmesh,ast,json,math,random,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];dense='--dense' in sys.argv;revision='v74' if dense else 'v73';O=R/('outputs/quality-'+revision);O.mkdir(parents=True,exist_ok=True)
source=R/'outputs/quality-v66/naju-arboretum-juniper-budget-v66.blend'
target=O/('naju-arboretum-tree-crowns-'+revision+'.blend')
if target.exists():raise RuntimeError('Existing artist revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
tree=ast.parse((R/'scripts/arboretum_botanical_finish.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PlantMesh'],type_ignores=[]),'<PlantMesh>','exec'))
def habit(o):
 v=o.get('reference_habit')
 if v:return v
 if o.name.startswith('distant_'):
  near=scene.objects.get(o.name[8:])
  if near:return near.get('reference_habit')
 return None
def fingerprint(o):
 m=o.data;v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v)
 ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids)
 lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
 return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
changed=[o for o in scene.objects if o.type=='MESH' and habit(o) in ['meta','broad','broad2']]
names={o.name for o in changed};protected={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o.name not in names}
old={(habit(o),o.get('vegetation_lod')):o.data for o in changed}

# Original compound-leaf drawings. Photographs are observation references only.
def foliage_material(kind):
 n=512;yy,xx=np.mgrid[0:n,0:n]/(n-1);mask=np.zeros((n,n),np.float32)
 def segment(a,b,width):
  dx=b[0]-a[0];dy=b[1]-a[1];t=np.clip(((xx-a[0])*dx+(yy-a[1])*dy)/(dx*dx+dy*dy),0,1)
  dist=np.sqrt((xx-a[0]-t*dx)**2+(yy-a[1]-t*dy)**2)
  return np.clip((width-dist)*n+.5,0,1)
 def leaf(a,b,width):
  dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy)
  t=((xx-a[0])*dx+(yy-a[1])*dy)/(length*length)
  side=np.abs((xx-a[0])*dy-(yy-a[1])*dx)/length
  envelope=np.maximum(0,np.sin(np.clip(t,0,1)*math.pi))**.7*width
  return np.clip((envelope-side)*n+.5,0,1)*((t>=0)&(t<=1))
 mask=np.maximum(mask,segment((.5,.05),(.5,.93),.004))
 if kind=='meta':
  count=30 if dense else 18
  for j in range(count):
   y=.10+j*(.77/count);reach=.33*math.sin((j+2)/(count+3)*math.pi)**.65
   for sign in [-1,1]:mask=np.maximum(mask,leaf((.5,y),(.5+sign*reach,y+.035 if dense else y+.055),.014 if dense else .011))
 else:
  for j in range(5):
   y=.11+j*.148;reach=.30*(.90+.1*math.sin(j*2))
   for sign in [-1,1]:
    a=(.5,y);b=(.5+sign*reach,y+.20)
    mask=np.maximum(mask,leaf(a,b,.092));mask=np.maximum(mask,segment(a,b,.004))
  mask=np.maximum(mask,leaf((.5,.73),(.50,.985),.086))
 noise=np.random.default_rng(7301+(kind=='meta')).random((n,n));tone=.83+.15*noise+.12*yy
 rgba=np.ones((n,n,4),np.float32);rgba[:,:,3]=mask
 for i,c in enumerate((.25,.405,.16) if kind=='meta' else (.24,.39,.12)):rgba[:,:,i]=c*tone
 im=bpy.data.images.new('Authored_'+kind+'_compound_leaves_'+revision,width=n,height=n,alpha=True);im.pixels.foreach_set(rgba.ravel());im.pack()
 mat=bpy.data.materials.new('Arboretum_'+kind+'_alpha_leaves_'+revision);mat.use_nodes=True;mat.use_backface_culling=False;mat.surface_render_method='DITHERED'
 bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.86
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
 mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);mat.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
 return mat
alpha={k:foliage_material(k) for k in ['meta','broad']}
opaque=bpy.data.materials['Reference_dense_foliage']

def fine_bark(kind):
 base=old['meta' if kind=='meta' else 'broad','near'].materials[0].copy();base.name='Arboretum_'+kind+'_bark_'+revision
 n=256;rr=np.random.default_rng(7401+(kind=='meta'));grain=rr.random((n,n))
 for _ in range(28):grain=(grain+np.roll(grain,1,0)+np.roll(grain,-1,0))/3
 yy,xx=np.mgrid[0:n,0:n]/n;tone=.87+.16*grain+.024*np.sin(xx*125+np.sin(yy*9))
 rgba=np.ones((n,n,4),np.float32)
 for i,c in enumerate((.355,.343,.303) if kind=='meta' else (.34,.315,.27)):rgba[:,:,i]=c*tone
 im=bpy.data.images.new('Authored_'+kind+'_fine_bark_'+revision,width=n,height=n);im.pixels.foreach_set(rgba.ravel());im.pack()
 bs=base.node_tree.nodes['Principled BSDF'];tex=base.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;base.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 for node in base.node_tree.nodes:
  if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.22
 return base
barks={k:fine_bark(k) for k in ['meta','broad']} if dense else {}

def copy_wood(p,m):
 for f in m.polygons:
  if f.material_index!=0:continue
  p.face([(m.vertices[i].co.x,m.vertices[i].co.z,-m.vertices[i].co.y) for i in f.vertices],0,[tuple(m.uv_layers.active.data[i].uv) for i in f.loop_indices])
def spray(p,c,d,length,width,roll):
 c=Vector(c);axis=Vector(d).normalized();u=axis.cross(Vector((0,1,0)))
 if u.length<.01:u=axis.cross(Vector((1,0,0)))
 u.normalize();v=axis.cross(u).normalized();side=u*math.cos(roll)+v*math.sin(roll);normal=axis.cross(side)
 for j in range(3):
  a=j/3;b=(j+1)/3
  def row(t):
   center=c+axis*length*t+normal*math.sin(t*math.pi)*length*.11
   return [center-side*width*.5,center+side*width*.5]
  x,y=row(a),row(b);p.face([x[0],x[1],y[1],y[0]],1,[(0,a),(1,a),(1,b),(0,b)])
def clump(p,c,rad,seed):
 rr=random.Random(seed);c=Vector(c);n=5
 rings=[]
 for y,r in [(-.70,.50),(0,1),(.7,.48)]:
  rings.append([c+Vector((math.cos(k*math.tau/n)*rad*r,y*rad*.60,math.sin(k*math.tau/n)*rad*r)) for k in range(n)])
 for k in range(n):
  q=(k+1)%n
  p.face([c+Vector((0,-rad*.6,0)),rings[0][q],rings[0][k]],2)
  for a,b in zip(rings,rings[1:]):p.face([a[k],a[q],b[q],b[k]],2)
  p.face([rings[-1][k],rings[-1][q],c+Vector((0,rad*.6,0))],2)

def build(kind,lod,variant):
 p=PlantMesh();base=old[kind,lod];copy_wood(p,base);rr=random.Random(7300+variant*43+(0 if kind=='meta' else 101 if kind=='broad' else 211));near=lod=='near'
 if kind=='meta':
  for tier in range(13):
   y=6+tier*.98;spread=3.9*(1-tier/15)
   for j in range(3):
    a=j*math.tau/3+tier*1.2;start=Vector((0,y,0));end=Vector((spread*math.cos(a),y+.55,spread*math.sin(a)))
    for k in range(5 if near else 3):
     root=start.lerp(end,.34+k*(.14 if near else .27));sign=-1 if k%2 else 1
     side=Vector((-math.sin(a),0,math.cos(a)))*sign
     tip=root+side*rr.uniform(.35,.85)*(1-tier/18)+Vector((math.cos(a)*.28,rr.uniform(-.22,.35),math.sin(a)*.28))
     p.tube(root,tip,.016,.003,0,n=4 if near else 3)
     sprays=(7 if near else 4) if dense else (3 if near else 2)
     for q in range(sprays):
      c=root.lerp(tip,.15+q*(.85/sprays));d=(tip-root).normalized()+Vector((rr.uniform(-.5,.5),rr.uniform(-.42,.42),rr.uniform(-.5,.5)))
      spray(p,c,d,rr.uniform(.76,1.14) if dense else rr.uniform(.65,1.03)*(1.14 if not near else 1),rr.uniform(.54,.76) if dense else rr.uniform(.30,.47),rr.uniform(-1.2,1.2) if dense else rr.uniform(-.6,.6))
     if k%2==variant%2:clump(p,root.lerp(tip,.72),rr.uniform(.18,.27) if dense else rr.uniform(.10,.18),k+tier*41+j)
 else:
  for j in range(21):
   a=j*2.399;y=3.7+(j%5)*.75;spread=2.4*math.sin((y-2)/6*math.pi);end=Vector((spread*math.cos(a),y,spread*math.sin(a)))
   for k in range(13 if near else 6):
    ang=rr.random()*math.tau;cos=rr.uniform(-.85,.9);r=math.sqrt(1-cos*cos);normal=Vector((r*math.cos(ang),cos,r*math.sin(ang)))
    c=end+normal*rr.uniform(.42,1.02);root=end.lerp(c,.38);p.tube(root,c,.009,.002,0,n=3)
    direction=normal+Vector((rr.uniform(-.45,.45),.35,rr.uniform(-.45,.45)))
    spray(p,c,direction,rr.uniform(.43,.66)*(1.28 if not near else 1),rr.uniform(.40,.61),rr.random()*math.tau)
    if k%3==variant%3:clump(p,end+normal*rr.uniform(.37,.77),rr.uniform(.15,.23),j*31+k)
 mk='meta' if kind=='meta' else 'broad'
 mesh=p.finish('Arboretum_'+kind+'_'+lod+'_'+revision+'_'+str(variant),[barks[mk] if dense else base.materials[0],alpha[mk],opaque])
 # Preserve all original wood coordinates; confine new foliage to the former envelope.
 lower=np.array([min(v.co[a] for v in base.vertices) for a in range(3)]);upper=np.array([max(v.co[a] for v in base.vertices) for a in range(3)])
 woodverts={i for f in mesh.polygons if f.material_index==0 for i in f.vertices}
 for v in mesh.vertices:
  if v.index not in woodverts:
   for axis in range(3):v.co[axis]=max(lower[axis],min(upper[axis],v.co[axis]))
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update();mesh.calc_loop_triangles()
 print('CROWN',kind,lod,variant,len(mesh.loop_triangles),flush=True);return mesh
protos={(k,l,v):build(k,l,v) for k in ['meta','broad','broad2'] for l in ['near','far'] for v in range(3)}
placements={};counts={}
for o in changed:
 k=habit(o);l=o['vegetation_lod'];v=int(hashlib.sha256(','.join(str(round(a,3)) for a in o.location).encode()).hexdigest()[:8],16)%3
 placements[o.name]=dict(habit=k,lod=l,variant=v,matrix=[a for row in o.matrix_world for a in row],original_mesh=o.data.name)
 o.data=protos[k,l,v];o['reference_habit']=k;o['tree_crown_revision']='Compound leaves and fine twigs '+revision+'; dimensions and planting remain estimated';o['tree_crown_variant']=v
 counts[k+'_'+l]=counts.get(k+'_'+l,0)+1
report=dict(source=str(source.relative_to(R)),output=str(target.relative_to(R)),changed_objects=placements,protected_geometry_hashes=protected,world_sha256=hashlib.sha256((R/'public/naju-arboretum-world.json').read_bytes()).hexdigest(),counts=counts,shared_prototypes=len(protos),triangles={m.name:len(m.loop_triangles) for m in protos.values()},reference='https://hangamja.tistory.com/1607',reference_published='2021-06-13',limitation='Reference-only photographs, original authored leaf textures; no current measured tree dimensions, planting or species assignment.')
(R/('knowledge/sources/arboretum/tree-crowns-'+revision+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.context.view_layer.update();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(O/('naju-arboretum-'+revision+'.glb')),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
print('CROWNS EXPORTED',counts,len(protected),flush=True)
