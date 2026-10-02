"""Photo-informed rose foliage and open timber canopy; preserve all author revisions."""
import bpy,math,json,random,ast,sys,hashlib,struct
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v61';O.mkdir(parents=True,exist_ok=True)
target=O/'naju-arboretum-garden-v61.blend'
if target.exists():raise RuntimeError('Existing artist revision preserved')
source=R/'outputs/arboretum/naju-arboretum-reference-v15.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
raw=(R/'public/models/naju-arboretum.glb').read_bytes();size=struct.unpack_from('<I',raw,12)[0]
palette={m['name']:m for m in json.loads(raw[20:20+size])['materials']}
for mat in bpy.data.materials:
 if mat.name not in palette:continue
 pbr=palette[mat.name].get('pbrMetallicRoughness',{});rgba=pbr.get('baseColorFactor',[1,1,1,1]);mat.diffuse_color=rgba
 bsdf=mat.node_tree.nodes.get('Principled BSDF') if mat.use_nodes else None
 if bsdf:
  bsdf.inputs['Base Color'].default_value=rgba;bsdf.inputs['Roughness'].default_value=pbr.get('roughnessFactor',1);bsdf.inputs['Metallic'].default_value=pbr.get('metallicFactor',0)
code=ast.parse((R/'scripts/arboretum_botanical_finish.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in code.body if isinstance(n,ast.ClassDef) and n.name=='PlantMesh'],type_ignores=[]),'<plant mesh>','exec'))
def mat(name,color,rough=.78):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;m.use_backface_culling=False;return m
stem=mat('Garden_live_canes',(.055,.105,.027));leaf=mat('Garden_compound_leaf',(.067,.16,.031));bud=mat('Garden_rose_calyx',(.067,.11,.025));pollen=mat('Garden_pollen',(.43,.27,.047))
# Own painted vein pattern. No visitor photograph is copied into the material.
n=256;v,u=np.mgrid[0:n,0:n]/(n-1);rr=np.random.default_rng(618)
vein=np.exp(-((u-.5)/.014)**2)*.14;vein+=np.exp(-(np.sin((v-abs(u-.5)*.56)*46)/.18)**2)*.035
field=.83+.13*np.sin(v*math.pi)+vein+rr.random((n,n))*.035
pixels=np.ones((n,n,4),np.float32)
for i,c in enumerate([.068,.163,.031]):pixels[:,:,i]=field*c
im=bpy.data.images.new('Garden_leaf_vein_paint',width=n,height=n);im.pixels.foreach_set(pixels.ravel());im.pack()
tex=leaf.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;leaf.node_tree.links.new(tex.outputs['Color'],leaf.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
def oval_leaf(p,c,d,length,width,mi=1,detail=True):
 c=Vector(c);axis=Vector(d).normalized();side=axis.cross(Vector((0,1,0)))
 if side.length<.01:side=axis.cross(Vector((1,0,0)))
 side.normalize();normal=axis.cross(side).normalized();rows=5 if detail else 2
 def row(t):
  center=c+axis*length*t+normal*math.sin(math.pi*t)*length*.12
  w=math.sin(math.pi*t)**.68*width*(1+.045*math.sin(t*math.pi*16))
  return [center-side*w,center+normal*w*.12,center+side*w]
 for j in range(rows):
  a,b=j/rows,(j+1)/rows;aa,bb=row(a),row(b)
  for k in range(2):p.face([aa[k],bb[k],bb[k+1],aa[k+1]],mi,[(k/2,a),(k/2,b),((k+1)/2,b),((k+1)/2,a)])
def compound(p,c,d,detail=True,length=.24):
 c=Vector(c);axis=Vector(d).normalized();side=axis.cross(Vector((0,1,0)))
 if side.length<.01:side=axis.cross(Vector((1,0,0)))
 side.normalize();end=c+axis*length;p.tube(c,end,.003,.0015,0,n=4)
 for t in [.28,.59]:
  for sign in [-1,1]:oval_leaf(p,c+axis*length*t,axis*.35+side*sign+Vector((0,.22,0)),length*.43,length*.12,detail=detail)
 oval_leaf(p,c+axis*length*.83,axis+Vector((0,.18,0)),length*.50,length*.14,detail=detail)
def foliage(detail):
 p=PlantMesh();rng=random.Random(619)
 for j in range(7):
  a=j*2.399;end=Vector((math.cos(a)*.34,.38+(j%3)*.13,math.sin(a)*.34));p.tube((0,0,0),end,.009,.003,0,n=5)
  for k in range(3 if detail else 2):
   c=end*(.45+.25*k);direction=Vector((math.cos(a+k*.7),.28,math.sin(a+k*.7)))
   compound(p,c,direction,detail,length=.28 if detail else .34)
 if detail:
  for j in range(25):
   a=j*2.399;c=Vector((.30*math.cos(a),rng.uniform(.24,.65),.30*math.sin(a)))
   oval_leaf(p,c,(math.cos(a),.24,math.sin(a)),.14,.046,detail=True)
 return p.finish('Garden_rose_foliage_'+('near' if detail else 'far'),[stem,leaf])
def blossom(kind,color,detail):
 p=PlantMesh();height=.88 if kind=='rose' else .71;head=Vector((.025,height,0));p.tube((0,0,0),head,.009,.003,0,n=5)
 for j in range(4 if detail else 2):
  a=j*2.399;c=(.025*j/4,.13+j*.15,0);direction=(math.cos(a),.26,math.sin(a))
  if kind=='rose':compound(p,c,direction,detail,length=.22)
  else:oval_leaf(p,c,direction,.18,.035,detail=detail)
 # Rose petals rise from a cupped base, then turn out at the rim; no horizontal discs.
 rings=[(10,.135,.078),(8,.095,.103),(6,.060,.125),(4,.034,.145)] if kind=='rose' else [(7,.09,.015)]
 if not detail:rings=rings[:2] if kind=='rose' else rings
 for ring,(count,radius,lift) in enumerate(rings):
  for k in range(count):
   angle=k*math.tau/count+ring*.49;radial=Vector((math.cos(angle),0,math.sin(angle)));side=Vector((-math.sin(angle),0,math.cos(angle)))
   def point(t,w):
    width=math.sin(math.pi*t*.96)**.60*radius*.57
    if kind=='rose':distance=radius*(.12+.88*t);y=lift*math.sin(t*math.pi/2)-radius*.13*t**4+abs(w)**2*.016
    else:distance=radius*t;y=.018+radius*(.13+.19*t*t+.10*w*w)
    return head+radial*distance+side*width*w+Vector((0,y,0))
   rows=5 if detail else 2;cols=4 if detail else 2
   for j in range(rows):
    for q in range(cols):
     a,b=j/rows,(j+1)/rows;c,d=-1+2*q/cols,-1+2*(q+1)/cols
     p.face([point(a,c),point(b,c),point(b,d),point(a,d)],2,[(a,(c+1)/2),(b,(c+1)/2),(b,(d+1)/2),(a,(d+1)/2)])
 if kind=='rose':
  for j in range(5):
   a=j*math.tau/5;oval_leaf(p,head,(math.cos(a),-.48,math.sin(a)),.07,.019,mi=3,detail=detail)
 else:
  for j in range(5):
   a=j*math.tau/5;p.tube(head+Vector((.018*math.cos(a),.02,.018*math.sin(a))),head+Vector((.018*math.cos(a),.047,.018*math.sin(a))),.003,.006,4,n=4)
 return p.finish('Garden_'+kind+'_'+color.name+'_'+('near' if detail else 'far'),[stem,leaf,color,bud,pollen])
def fingerprint(o):
 m=o.data;v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v);ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids)
 lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
 return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
changed={};pairs={};flower_protos={};petal_materials={};shrubs={lod:foliage(lod=='near') for lod in ['near','far']}
for o in list(scene.objects):
 if o.type!='MESH':continue
 lod=o.get('vegetation_lod');name=o.name
 if name.startswith(('botanical_flower','distant_botanical_flower','climbing_rose','distant_climbing_rose')):
  old=o.data;kind='rose' if 'rose' in old.name else 'cream' if 'cream' in old.name else 'perennial'
  oldcolor=old.materials[2];key=oldcolor.name
  if key not in petal_materials:petal_materials[key]=mat('Garden_petals_'+key,tuple(oldcolor.diffuse_color[:3]),.67)
  proto=(kind,key,lod)
  if proto not in flower_protos:flower_protos[proto]=blossom(kind,petal_materials[key],lod=='near')
  changed[name]={'matrix_before':[v for row in o.matrix_world for v in row],'original_mesh':old.name,'category':'flower'}
  o.data=flower_protos[proto]
  if name.startswith(('botanical_flower','distant_botanical_flower')):o.location.z=.052
  o['garden_revision']='photo-informed v61; bloom season and modules estimated';o['garden_kind']=kind
 elif name.startswith('reference_rose_foliage'):
  changed[name]={'matrix_before':[v for row in o.matrix_world for v in row],'original_mesh':o.data.name,'category':'shrub'};o.data=shrubs[lod]
 elif name.startswith('play_canopy'):
  changed[name]={'matrix_before':[v for row in o.matrix_world for v in row],'original_mesh':o.data.name,'category':'canopy'}
  # Split the original canopy quad into narrow boards, using its exact corners.
  mesh=o.data;verts=[];faces=[]
  for f in mesh.polygons:
   a,b,c,d=[mesh.vertices[i].co.copy() for i in f.vertices]
   for j in range(16):
    lo=(j+.025)/16;hi=(j+.975)/16
    q=[a.lerp(b,lo),a.lerp(b,hi),d.lerp(c,hi),d.lerp(c,lo)];base=len(verts)
    verts.extend(q+[v-Vector((0,0,.027)) for v in q]);faces.extend([(base,base+1,base+2,base+3),(base+7,base+6,base+5,base+4),(base,base+4,base+5,base+1),(base+1,base+5,base+6,base+2),(base+2,base+6,base+7,base+3),(base+3,base+7,base+4,base)])
  data=bpy.data.meshes.new('Garden_open_timber_canopy');data.from_pydata(verts,[],faces);data.materials.append(bpy.data.materials['Crafted_timber']);data.update();o.data=data
protected={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o.name not in changed}
for name,item in changed.items():item['matrix_after']=[v for row in bpy.data.objects[name].matrix_world for v in row]
report={'source':str(source.relative_to(R)),'output':str(target.relative_to(R)),'palette_snapshot':palette,'changed_objects':changed,'protected_geometry_hashes':protected,'shared_flower_prototypes':len(flower_protos),'shared_shrub_prototypes':len(shrubs),'world_sha256':hashlib.sha256((R/'public/naju-arboretum-world.json').read_bytes()).hexdigest(),'references':['https://hangamja.tistory.com/1607','https://v.daum.net/v/20241027073357405'],'limitations':'2021 rose and play photographs inform form only. Existing interpreted garden layout, species, dimensions and bloom remain estimated.'}
(R/'knowledge/sources/arboretum/garden-quality-v61.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(O/'naju-arboretum-v61.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False)
print('GARDEN FINISH',len(changed),len(protected),len(flower_protos),flush=True)
