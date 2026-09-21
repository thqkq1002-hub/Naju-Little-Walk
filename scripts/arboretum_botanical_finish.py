"""Editable botanical geometry, shared plant meshes, and rounded play joinery."""
import bpy,sys,math,random,gzip,json
import numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
R=Path(__file__).resolve().parents[1];O=R/'outputs/arboretum';target=O/'naju-arboretum-botanical-v11.blend'
if target.exists():raise RuntimeError('Existing artist revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(O/'naju-arboretum-playgarden-v10.blend'))
scene=bpy.context.scene;g=MuseumGeometry(scene,(0,0),0);rng=random.Random(944)
def local(s,t):return (-475+.98*s-.2*t,-50+.2*s+.98*t)
def pt(s,y,t):
 x,z=local(s,t);return (x,y,z)

def textured_leaf():
 n=256;v,u=np.mgrid[0:n,0:n]/(n-1);vein=np.exp(-((u-.5)/.018)**2)
 secondary=np.exp(-(np.sin((v-np.abs(u-.5)*.75)*60)/.16)**2)*.09
 variation=.82+.16*np.sin(v*math.pi)+vein*.15+secondary
 noise=np.random.default_rng(91).random((n,n))*.04
 rgba=np.ones((n,n,4),dtype=np.float32)
 for i,c in enumerate([.34,.49,.17]):rgba[:,:,i]=np.clip(c*(variation+noise),0,1)
 im=bpy.data.images.new('Botanical_leaf_veins',width=n,height=n);im.pixels.foreach_set(rgba.ravel());im.pack()
 mat=bpy.data.materials.new('Botanical_living_leaf');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.72
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 mat.use_backface_culling=False
 return mat
leafmat=textured_leaf();bark=bpy.data.materials['Authored_bark_grain']
stemmat=g.mat('#426331');pink=g.mat('#da7394');lavender=g.mat('#a48ac8');ivory=g.mat('#efe6c9');gold=g.mat('#d5ae50')
for m in [pink,lavender,ivory]:m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.60;m.use_backface_culling=False

class PlantMesh:
 def __init__(self):self.v=[];self.f=[];self.mi=[];self.uv=[]
 def face(self,points,mat,uv=None):
  n=len(self.v);self.v.extend([tuple(p) for p in points]);self.uv.extend(uv or [(p[0]*.4,p[1]*.4) for p in points]);self.f.append(tuple(range(n,n+len(points))));self.mi.append(mat)
 def tube(self,a,b,r1,r2,mat=0,n=7):
  a,b=Vector(a),Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,1,0)))
  if u.length<.01:u=axis.cross(Vector((1,0,0)))
  u.normalize();v=axis.cross(u).normalized()
  for j in range(n):
   t=j*math.tau/n;q=(j+1)*math.tau/n
   self.face([a+r1*(math.cos(t)*u+math.sin(t)*v),a+r1*(math.cos(q)*u+math.sin(q)*v),b+r2*(math.cos(q)*u+math.sin(q)*v),b+r2*(math.cos(t)*u+math.sin(t)*v)],mat,[(j/n,0),((j+1)/n,0),((j+1)/n,1),(j/n,1)])
 def leaf(self,c,d,length,width,mat=1):
  c=Vector(c);axis=Vector(d).normalized();side=axis.cross(Vector((0,1,0)))
  if side.length<.01:side=axis.cross(Vector((1,0,0)))
  side.normalize();normal=axis.cross(side).normalized()
  # Curved lanceolate leaf; six strips replace the old diamond silhouettes.
  for j in range(4):
   a=j/4;b=(j+1)/4
   def row(t):
    mid=c+axis*length*t+normal*(math.sin(t*math.pi)*length*.10);w=math.sin(t*math.pi)*width
    return [mid-side*w,mid+normal*w*.16,mid+side*w]
   p,q=row(a),row(b)
   for k in range(2):self.face([p[k],q[k],q[k+1],p[k+1]],mat,[(k/2,a),(k/2,b),((k+1)/2,b),((k+1)/2,a)])
 def finish(self,name,mats):
  mesh=bpy.data.meshes.new(name);mesh.from_pydata([(x,-z,y) for x,y,z in self.v],[],self.f);mesh.update()
  for m in mats:mesh.materials.append(m)
  layer=mesh.uv_layers.new(name='Botanical_UV')
  for p,i in zip(mesh.polygons,self.mi):
   p.material_index=i;p.use_smooth=True
   for li in p.loop_indices:layer.data[li].uv=self.uv[mesh.loops[li].vertex_index]
  return mesh

def tree_mesh(kind,seed):
 rr=random.Random(seed);p=PlantMesh()
 h=7.8 if kind!='column' else 8.6
 rings=[(0,.24),(.35,.19),(2.7,.13),(4.7,.085),(h,.015)]
 for (a,r),(b,q) in zip(rings,rings[1:]):p.tube((0,a,0),(.10*math.sin(b),b,.05*math.cos(b)),r,q,n=10)
 for k in range(5):
  a=k*math.tau/5;p.tube((0,.34,0),(.34*math.cos(a),.035,.34*math.sin(a)),.09,.035,n=6)
 for j in range(17 if kind=='column' else 14):
  a=j*2.399;yy=2.1+j*(.34 if kind=='column' else .34);spread=(1.5 if kind=='column' else 2.65)*math.sin((yy-1.1)/(h-.5)*math.pi)**.7
  end=Vector((spread*math.cos(a),yy+.8,spread*math.sin(a)));start=Vector((0,yy,0));p.tube(start,end,.063,.014,n=7)
  for k in range(3):
   base=start.lerp(end,.50+k*.20);ta=a+(k-1)*.65;tip=base+Vector((.7*math.cos(ta),.4+rr.random()*.25,.7*math.sin(ta)));p.tube(base,tip,.021,.006,n=5)
   for q in range(13):
    c=base.lerp(tip,rr.uniform(.15,1.15))+Vector((rr.uniform(-.45,.45),rr.uniform(-.25,.55),rr.uniform(-.45,.45)))
    direction=(rr.uniform(-1,1),rr.uniform(-.25,.65),rr.uniform(-1,1))
    p.leaf(c,direction,rr.uniform(.30,.52) if kind!='column' else rr.uniform(.27,.40),rr.uniform(.09,.16) if kind!='column' else .07)
 return p.finish('Botanical_'+kind,[bark,leafmat])
trees=[tree_mesh('spreading',12),tree_mesh('rounded',38),tree_mesh('column',61)]
tree_count=0
for o in list(scene.objects):
 if o.type=='MESH' and o.name.startswith(('estimated_broadleaf','satellite_grove','estimated_juniper')):
  column=o.name.startswith('estimated_juniper');o.data=trees[2] if column else trees[tree_count%2]
  o['authored_vegetation']=True;o['botanical_form']='columnar' if column else 'broadleaf';tree_count+=1

# Remove the triangular flowers and flat hedge blades; preserve their ground plan.
for o in list(scene.objects):
 if o.name.startswith('flower_detail_'):bpy.data.objects.remove(o,do_unlink=True)
def blossom_mesh(kind,seed):
 rr=random.Random(seed);p=PlantMesh();h=.60 if kind=='rose' else .52
 p.tube((0,0,0),(.015,h,0),.011,.005,0,n=5)
 for j in range(5):
  a=j*2.4;p.leaf((0,.08+j*.065,0),(math.cos(a),.28,math.sin(a)),.17,.048,1)
 # Petals have rounded scalloped edges and a cup; roses have three overlapping whorls.
 for ring in range(3 if kind=='rose' else 1):
  count=7 if kind=='rose' else 8;rad=.155*(1-ring*.23)
  for k in range(count):
   a=k*math.tau/count+ring*.4;u=Vector((math.cos(a),0,math.sin(a)));v=Vector((-math.sin(a),0,math.cos(a)))
   center=Vector((.015,h+ring*.028,0))
   for i in range(4):
    for j in range(4):
     def cp(t,w):
      width=math.sin(t*math.pi*.94)**.65*rad*.60
      return center+u*rad*t+v*(w*width)+Vector((0,rad*(.10+.36*t*t+.13*w*w),0))
     t=i/4;tt=(i+1)/4;w=-1+j*.5;ww=w+.5
     p.face([cp(t,w),cp(tt,w),cp(tt,ww),cp(t,ww)],2,[(t,(w+1)/2),(tt,(w+1)/2),(tt,(ww+1)/2),(t,(ww+1)/2)])
 for k in range(8):
  a=k*math.tau/8;center=(.015+.023*math.cos(a),h+.046,.023*math.sin(a))
  p.tube((center[0],h,center[2]),center,.007,.010,3,n=5)
 return p.finish('Botanical_flower_'+kind,[stemmat,leafmat,pink if kind=='rose' else lavender if kind=='perennial' else ivory,gold])
flowers=[blossom_mesh('rose',5),blossom_mesh('perennial',11),blossom_mesh('cream',22)]
def plant(data,name,s,t,scale=1,y=0):
 x,z=local(s,t);o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=g.bp(x,y,z);o.scale=(scale,scale,scale);o.rotation_euler.z=rng.random()*math.tau;o['authored_vegetation']=True;return o
for a,b in [(148,178),(184,217)]:
 for row,(c,d) in enumerate([(34,49),(55,71),(77,93)]):
  for j in range(480):
   s=rng.uniform(a+1,b-1);t=rng.uniform(c+1,d-1)
   if abs(s-(a+b)/2)<1:continue
   plant(flowers[row],'botanical_flower',s,t,rng.uniform(.8,1.35))
  if row==0:
   s=(a+b)/2+5;t=(c+d)/2
   for j in range(55):
    h=rng.uniform(.15,1.9);ang=rng.random()*math.tau;r=1.05-h*.34
    plant(flowers[0],'climbing_rose',s+r*math.cos(ang),t+r*math.sin(ang),rng.uniform(.65,.95),h)
# Leafy hedge crowns disguise the old straight box tops without expanding into paths.
p=PlantMesh()
for j in range(18):
 a=rng.random()*math.tau;c=(rng.uniform(-.13,.13),rng.uniform(-.06,.10),rng.uniform(-.13,.13));p.leaf(c,(math.cos(a),rng.uniform(.1,.8),math.sin(a)),.12,.037,0)
hedge=p.finish('Botanical_hedge_spray',[leafmat])
for a,b in [(148,178),(184,217)]:
 for c,d in [(34,49),(55,71),(77,93)]:
  for s in np.arange(a,b,.4):
   for t in [c,d]:plant(hedge,'hedge_leaf_spray',s,t+rng.uniform(-.1,.1),rng.uniform(.8,1.2),.56)
  for t in np.arange(c,d,.4):
   for s in [a,b]:plant(hedge,'hedge_leaf_spray',s+rng.uniform(-.1,.1),t,rng.uniform(.8,1.2),.56)

# Subtle natural timber grain avoids the previous strong repeating stripes.
n=256;rr=np.random.default_rng(44);grain=rr.random((n,n))
for _ in range(38):grain=(grain+np.roll(grain,1,0)+np.roll(grain,-1,0))/3
grain=.86+.22*grain
rgba=np.ones((n,n,4),dtype=np.float32)
for i,c in enumerate([.44,.31,.19]):rgba[:,:,i]=c*grain
im=bpy.data.images.new('Crafted_timber_grain',width=n,height=n);im.pixels.foreach_set(rgba.ravel());im.pack()
wood=bpy.data.materials.new('Crafted_timber');wood.use_nodes=True;bs=wood.node_tree.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.78
tex=wood.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;wood.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
rounded=0
for o in list(scene.objects):
 if o.type!='MESH':continue
 if o.name.startswith(('play_platform','play_guard','play_deck','play_bridge','play_stair','play_bench','play_rest','play_climbing','flower_hedge','flower_label')):
  bpy.context.view_layer.objects.active=o
  bevel=o.modifiers.new('Soft physical edges','BEVEL');bevel.width=.018 if o.name.startswith('play_') else .075;bevel.segments=3
  bpy.ops.object.modifier_apply(modifier=bevel.name)
  weighted=o.modifiers.new('Face weighted normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=weighted.name);rounded+=1
  if o.name.startswith('play_'):o.data.materials.clear();o.data.materials.append(wood)
 if o.name.startswith('play_timber_post'):o.data.materials.clear();o.data.materials.append(wood)
 if o.name.startswith('play_green_slide'):
  bpy.context.view_layer.objects.active=o
  sub=o.modifiers.new('Moulded slide curves','SUBSURF');sub.levels=2;bpy.ops.object.modifier_apply(modifier=sub.name)
  solid=o.modifiers.new('Plastic thickness','SOLIDIFY');solid.thickness=.035;bpy.ops.object.modifier_apply(modifier=solid.name)
  for f in o.data.polygons:f.use_smooth=True
  mat=o.data.materials[0];mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.31
 if o.name.startswith('play_cream_tube_slide'):
  bpy.context.view_layer.objects.active=o;sub=o.modifiers.new('Smooth moulded tube','SUBSURF');sub.levels=1;bpy.ops.object.modifier_apply(modifier=sub.name)
# Visible bolt heads at timber joins; same structural envelope and collisions.
for s in [233,235]:
 for t in [-61,-59,-64.1,-62.1]:
  for h in [1.52,2.47]:
   x,z=local(s,t);bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=6,radius=.043,location=g.bp(x,h,z+.11));o=bpy.context.object;o.name='play_join_bolt';o.scale=(1,.45,1);o.data.materials.append(g.mat('#8a8d80'))
# Small timber end caps rather than open-looking posts.
for s,t,h in [(233,-61,2.85),(235,-61,2.85),(233,-59,2.85),(235,-59,2.85),(233,-64.1,3.5),(235,-64.1,3.5)]:
 x,z=local(s,t);g.box('play_post_cap',x,h,z,.24,.05,.24,'#514432',record=False)

scene.eevee.taa_render_samples=48;scene.view_settings.exposure=.7
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
out=R/'public/models/naju-arboretum.glb';bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
with gzip.open(str(out)+'.gz','wb',compresslevel=9) as f:f.write(out.read_bytes())
metrics={'trees_replaced':tree_count,'rounded_parts':rounded,'shared_tree_meshes':len(trees),'flower_prototypes':len(flowers),'glb_bytes':out.stat().st_size,'compressed_bytes':Path(str(out)+'.gz').stat().st_size,'note':'Geometry is Blender authored. Repeated vegetation is instanced in 96m cells by Three.js. No measured browser FPS.'}
(R/'knowledge/sources/arboretum/botanical-metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.render.resolution_percentage=100
for name,loc,aim,lens in [('botanical-play',(248,4,-42),(234,1.5,-61),37),('botanical-flowers',(181,1.7,54),(164,.55,42),32),('botanical-trees',(239,2,-37),(255,4,-37),32)]:
 cam=scene.camera;cam.location=g.bp(*pt(*loc));cam.rotation_euler=(Vector(g.bp(*pt(*aim)))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
 scene.render.filepath=str(O/(name+'-v11.png'));bpy.ops.render.render(write_still=True)
print('BOTANICAL FINISH COMPLETE',metrics)
