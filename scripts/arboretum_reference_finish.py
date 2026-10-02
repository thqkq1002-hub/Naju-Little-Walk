"""Photo-informed tree habits and rose shrub massing, preserving authored revisions."""
import bpy,bmesh,math,random,ast,json,gzip,sys
from pathlib import Path
from mathutils import Vector
import numpy as np
R=Path(__file__).resolve().parents[1];O=R/'outputs/arboretum';target=O/'naju-arboretum-reference-v15.blend'
if target.exists():raise RuntimeError('Existing revision is preserved')
bpy.ops.wm.open_mainfile(filepath=str(O/'naju-arboretum-botanical-v12.blend'))
sys.path.insert(0,str(R/'scripts'))
from museum_geometry import MuseumGeometry
scene=bpy.context.scene;g=MuseumGeometry(scene,(0,0),0);rng=random.Random(20260920)
# Reuse the mesh builder only, without executing the earlier authoring script.
source=ast.parse((R/'scripts/arboretum_botanical_finish.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='PlantMesh'],type_ignores=[]),'<plant mesh>','exec'))
def local(s,t):return (-475+.98*s-.2*t,-50+.2*s+.98*t)
def inv(x,z):return ((.98*(x+475)+.2*(z+50))/1.0004,(-.2*(x+475)+.98*(z+50))/1.0004)
bark=bpy.data.materials['Authored_bark_grain'];leaf=bpy.data.materials['Botanical_living_leaf']
greens=[leaf,g.mat('#628148'),g.mat('#4e703d').copy(),g.mat('#729252')]
for m in greens:m.use_backface_culling=False
greens[2].name='Reference_dense_foliage'
# Authored fine leaf speckle gives the inner crown depth without huge flat color patches.
n=512;rr=np.random.default_rng(274);field=rr.random((n,n))
for _ in range(3):field=(field+np.roll(field,1,0)+np.roll(field,-1,0)+np.roll(field,1,1)+np.roll(field,-1,1))/5
field=np.clip((field-.4)*4+.15,0,1);rgba=np.ones((n,n,4),dtype=np.float32)
for i,c in enumerate([.36,.48,.22]):rgba[:,:,i]=c*(.70+.55*field)
texture=bpy.data.images.new('Reference_foliage_microcolor',width=n,height=n);texture.pixels.foreach_set(rgba.ravel());texture.pack()
mat=greens[2];bs=mat.node_tree.nodes['Principled BSDF'];tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=texture;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
dx=(np.roll(field,1,1)-np.roll(field,-1,1))*.6;dy=(np.roll(field,1,0)-np.roll(field,-1,0))*.6
normal=np.stack([dx,dy,np.ones_like(dx)],axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True);rgba[:,:,:3]=normal*.5+.5
texture=bpy.data.images.new('Reference_foliage_micronormal',width=n,height=n);texture.colorspace_settings.name='Non-Color';texture.pixels.foreach_set(rgba.ravel());texture.pack()
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=texture;nm=mat.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.45;mat.node_tree.links.new(tex.outputs['Color'],nm.inputs['Color']);mat.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
materials=[bark]+greens
# Replace high-contrast bark striping with fine, irregular longitudinal grain.
im=bpy.data.images.get('Reference_bark_color')
if not im:
 n=256;rr=np.random.default_rng(361);a=rr.random((n,n))
 for _ in range(24):a=(a+np.roll(a,1,0)+np.roll(a,-1,0))/3
 v,u=np.mgrid[0:n,0:n]/n;value=.84+.20*a+.045*np.sin(u*91+np.sin(v*8))
 rgba=np.ones((n,n,4),dtype=np.float32)
 for i,c in enumerate([.40,.32,.23]):rgba[:,:,i]=value*c
 im=bpy.data.images.new('Reference_bark_color',width=n,height=n);im.pixels.foreach_set(rgba.ravel());im.pack()
 tex=bark.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;bark.node_tree.links.new(tex.outputs['Color'],bark.node_tree.nodes['Principled BSDF'].inputs['Base Color'])

def blade(p,c,d,length,width,mi):
 c=Vector(c);d=Vector(d).normalized();side=d.cross(Vector((0,1,0)))
 if side.length<.01:side=d.cross(Vector((1,0,0)))
 side.normalize();normal=d.cross(side);mid=c+d*length*.5+normal*length*.07;tip=c+d*length
 p.face([c,mid-side*width,tip,mid],mi,[(.5,0),(0,.5),(.5,1),(.5,.5)])
 p.face([c,mid,tip,mid+side*width],mi,[(.5,0),(.5,.5),(.5,1),(1,.5)])

def crown(p,center,size,seed,detail=1,needle=False):
 rr=random.Random(seed);c=Vector(center);sx,sy,sz=size
 # Small irregular crown volumes occlude the empty center; surface sprays carry the outline.
 seg=16 if detail else 10;rings=9 if detail else 6
 def point(j,k):
  a=j*math.tau/seg;b=-math.pi/2+k*math.pi/rings
  wob=1+.07*math.sin(a*5+b*7)+.045*math.cos(a*3-b*11)
  return c+Vector((sx*math.cos(b)*math.cos(a),sy*math.sin(b),sz*math.cos(b)*math.sin(a)))*wob
 for k in range(rings):
  for j in range(seg):p.face([point(j,k+1),point(j+1,k+1),point(j+1,k),point(j,k)],3)
 for _ in range((110 if needle else 75) if detail else 19):
  a=rr.random()*math.tau;b=rr.uniform(-1,1);r=math.sqrt(1-b*b);normal=Vector((r*math.cos(a),b,r*math.sin(a)))
  pos=c+Vector((normal.x*sx,normal.y*sy,normal.z*sz))*rr.uniform(.97,1.09)
  blade(p,pos,normal+Vector((rr.uniform(-.4,.4),.2,rr.uniform(-.4,.4))),rr.uniform(.17,.32) if needle else rr.uniform(.25,.43),.04 if needle else rr.uniform(.08,.13),rr.choice([1,1,2,3,4]))

def tree(kind,detail,seed):
 p=PlantMesh();rr=random.Random(seed)
 h=20 if kind=='meta' else 8.4 if kind=='column' else 6.2 if kind=='oval' else 8.4
 for a,b,r,q in [(0,.4,.34 if kind=='meta' else .22,.25 if kind=='meta' else .18),(.4,3,.25 if kind=='meta' else .18,.18 if kind=='meta' else .10),(3,h,.18 if kind=='meta' else .10,.018)]:p.tube((0,a,0),(0,b,0),r,q,n=9)
 if kind in ['column','oval']:
  # Clipped evergreen foliage extends near the ground, unlike the previous bare canopy.
  for tier in range(8):
   y=.65+tier*(.87 if kind=='column' else .60);r=(1.15 if kind=='column' else 1.75)*math.sin((tier+1)/10*math.pi)**.55
   for j in range(3):
    a=j*math.tau/3+tier*.85;c=(r*.35*math.cos(a),y,r*.35*math.sin(a))
    crown(p,c,(r*.79,.93 if kind=='column' else .76,r*.79),seed+tier*7+j,detail,True)
 elif kind=='meta':
  for tier in range(13):
   y=6+tier*.98;spread=3.9*(1-tier/15)
   for j in range(3):
    a=j*math.tau/3+tier*1.2;end=Vector((spread*math.cos(a),y+.55,spread*math.sin(a)));p.tube((0,y,0),end,.054,.014,n=5)
    c=end*.72;c.y=y+.65;crown(p,c,(max(.4,spread*.48),.75,max(.4,spread*.48)),seed+tier*7+j,detail,True)
 else:
  for j in range(21):
   a=j*2.399;y=3.7+(j%5)*.75;spread=2.4*math.sin((y-2)/6*math.pi)
   end=Vector((spread*math.cos(a),y,spread*math.sin(a)));p.tube((0,max(2,y-1.6),0),end,.056,.013,n=6)
   crown(p,end,(rr.uniform(.95,1.35),rr.uniform(.75,1.02),rr.uniform(.95,1.25)),seed+j,detail)
 mesh=p.finish('Reference_'+kind+('_near' if detail else '_far'),materials)
 smooth(mesh)
 return mesh

def smooth(mesh):
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()

protos={(kind,lod):tree(kind,lod=='near',100+i*41) for i,kind in enumerate(['broad','broad2','column','oval','meta']) for lod in ['near','far']}
counts={};originals=[]
for o in list(scene.objects):
 if o.type!='MESH' or not o.name.startswith(('estimated_broadleaf','satellite_grove','estimated_juniper','estimated_meta')):continue
 if o.get('vegetation_lod')=='far':continue
 s,t=inv(o.location.x,-o.location.y)
 kind='meta' if o.name.startswith('estimated_meta') else ('column' if t<-175 else 'oval') if o.name.startswith('estimated_juniper') else ('broad' if len(originals)%2 else 'broad2')
 o.data=protos[kind,'near'];o['authored_vegetation']=True;o['vegetation_lod']='near';o['vegetation_distance']=80;o['reference_habit']=kind
 originals.append(o);counts[kind]=counts.get(kind,0)+1
 far=scene.objects.get('distant_'+o.name)
 if far is None:far=o.copy();far.name='distant_'+o.name;scene.collection.objects.link(far)
 far.data=protos[kind,'far'];far['authored_vegetation']=True;far['vegetation_lod']='far';far['vegetation_distance']=80;far.hide_render=True
print('Reference tree habits',counts,flush=True)

# Rose stems belong in dense, branching shrubs, not a grid of isolated flowers.
def shrub(detail):
 p=PlantMesh()
 for j in range(5):
  a=j*2.4;end=(.23*math.cos(a),.45+j*.05,.23*math.sin(a));p.tube((0,0,0),end,.015,.006,0,n=5)
  crown(p,end,(.32,.28,.32),944+j,detail)
 mesh=p.finish('Reference_rose_shrub_'+str(detail),materials);smooth(mesh);return mesh
shrubs={lod:shrub(lod=='near') for lod in ['near','far']}
def pair(name,near,far,x,z,scale=1,radius=28,height=0):
 angle=rng.random()*math.tau
 for lod,data in [('near',near),('far',far)]:
  o=bpy.data.objects.new(name+'_'+lod,data);scene.collection.objects.link(o);o.location=g.bp(x,height,z);o.scale=(scale,scale,scale);o.rotation_euler.z=angle
  o['authored_vegetation']=True;o['vegetation_lod']=lod;o['vegetation_distance']=radius;o.hide_render=lod=='far'
roses=0
for a,b in [(148,178),(184,217)]:
 for c,d in [(34,49),(55,71),(77,93)]:
  for s in np.arange(a+1.4,b-1.4,1.55):
   for t in np.arange(c+1.4,d-1.4,1.55):
    if abs(s-(a+b)/2)<1.3:continue
    x,z=local(s+rng.uniform(-.28,.28),t+rng.uniform(-.28,.28));pair('reference_rose_foliage',shrubs['near'],shrubs['far'],x,z,rng.uniform(.80,1.2));roses+=1
# Raise existing blossoms above the new shrub crowns; use photo-observed rose colors.
colors=[g.mat(c) for c in ['#e794b1','#f2e6d1','#a93349','#edb28e']]
variants={}
for o in list(scene.objects):
 if not o.name.startswith(('botanical_flower','distant_botanical_flower')):continue
 if o.type!='MESH':continue
 key=(o.data,(round(o.location.x*10)+round(o.location.y*10))%4)
 if key not in variants:
  data=o.data.copy();data.materials[2]=colors[key[1]];variants[key]=data
 o.data=variants[key];o.location.z+=.30
# Low groundcover close to existing trunks; avoid adding trunks or obstructing paths.
p=PlantMesh()
for j in range(34):
 a=j*2.4;r=rng.uniform(.1,.55);blade(p,(r*math.cos(a),0,r*math.sin(a)),(math.cos(a)*.3,.9,math.sin(a)*.3),rng.uniform(.12,.32),.024,rng.choice([1,2,3]))
ground=p.finish('Reference_groundcover',materials);understory=0
for o in originals[::4]:
 if o.get('reference_habit')=='meta':continue
 x,z=o.location.x,-o.location.y;s,t=inv(x,z)
 if 140<s<225 and 23<t<102:continue
 pair('reference_trunk_groundcover',ground,ground,x+.55,z+.30,rng.uniform(.8,1.3));understory+=1
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
out=R/'public/models/naju-arboretum.glb';bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False)
with gzip.open(str(out)+'.gz','wb',compresslevel=9) as f:f.write(out.read_bytes())
metrics=dict(tree_habits=counts,rose_shrubs=roses,groundcover_patches=understory,glb_bytes=out.stat().st_size,gzip_bytes=Path(str(out)+'.gz').stat().st_size,reference='Field photographs describe shapes; individual coordinates, species, sizes and seasonal bloom are estimated.')
(R/'knowledge/sources/arboretum/reference-finish-metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.eevee.taa_render_samples=48
for name,loc,aim in [('reference-forest',(239,2,-37),(255,5,-37)),('reference-roses',(181,1.7,54),(164,.7,42)),('reference-juniper',(140,1.7,-175),(220,2,-175)),('reference-avenue',(110,1.7,0),(170,6,0))]:
 x,z=local(loc[0],loc[2]);scene.camera.location=g.bp(x,loc[1],z);x,z=local(aim[0],aim[2]);scene.camera.rotation_euler=(Vector(g.bp(x,aim[1],z))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.lens=32
 scene.render.filepath=str(O/(name+'-v15.png'));bpy.ops.render.render(write_still=True)
print('REFERENCE FINISH COMPLETE',metrics,flush=True)
