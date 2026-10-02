"""Preserved-revision detail pass: old pines, soft forest floor and riparian plants.
Mapped routes and river collision boundary remain unchanged. Details are inferred.
"""
import bpy,sys,math,random,json,gzip,struct
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from museum_geometry import MuseumGeometry
O=R/'outputs/deudeulgang';target=O/'deudeulgang-pine-grove-v54.blend'
if target.exists():raise RuntimeError('Existing artist revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(O/'deudeulgang-pine-grove-v3.blend'));scene=bpy.context.scene
g=MuseumGeometry(scene,(0,0),0);rr=random.Random(540921)
for m in bpy.data.materials:
 if len(m.name)==13 and m.name.startswith('Museum_'):g.materials['#'+m.name[7:]]=m
S=R/'knowledge/sources/deudeulgang';meta=json.loads((S/'metrics.json').read_text());grove=meta['grove_polygon'];river=meta['river_polygon']
worldpath=R/'public/deudeulgang-world.json';world=json.loads(worldpath.read_text(encoding='utf8'))
def inside(p,poly):
 x,z=p;hit=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:hit=not hit
 return hit
def dist(p,a,b):
 dx,dz=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dz)/(dx*dx+dz*dz or 1)))
 return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dz)
paths=[]
for s in world['solids']:
 if s['name'].startswith('path_'):
  p=s['footprint'];paths.append((((p[0][0]+p[3][0])/2,(p[0][1]+p[3][1])/2),((p[1][0]+p[2][0])/2,(p[1][1]+p[2][1])/2),s['size'][2]))
def clear(x,z,margin=.5):return not any(dist((x,z),a,b)<w/2+margin for a,b,w in paths)
def ground(o):o['no_shadow']=True;return o
groups={}
def face(color,pts):
 vs,fs=groups.setdefault(color,([],[]));n=len(vs);vs.extend(pts);fs.append(tuple(range(n,n+len(pts))))
def flush(prefix):
 for c,(vs,fs) in groups.items():ground(g.mesh(prefix+'_'+c,vs,fs,c))
 groups.clear()

# Shared near/far prototypes keep their correspondence and instancing properties.
pine_meshes={o.data for o in scene.objects if o.type=='MESH' and o.name.startswith(('old_pine_','distant_pine_'))}
for mesh in pine_meshes:
 seed=int(mesh.name.split('_')[1]);phase=seed*.43
 for v in mesh.vertices:
  h=v.co.z;t=max(0,min(1,(h-1.3)/14))
  v.co.x+=math.sin(t*2.6+phase)*t*t*1.20
  v.co.y+=math.sin(t*3.1+phase*.7)*t*t*.85
  # Crown branches spread sideways as they rise; roots and collision bases stay put.
  if h>5:
   f=1+max(0,h-7)*.018;v.co.x*=f;v.co.y*=f
 mesh.update()
print('PINE shared near/far shapes refined',len(pine_meshes),flush=True)

# Replace cut-out polygons with fine radial color transitions, all in a few meshes.
remove=[o for o in scene.objects if o.name.startswith(('pine_litter_patch','understory_moss','water_glint','shelter_tiled_roof','shelter_ridge'))]
bpy.data.batch_remove(ids=remove)
for o in scene.objects:
 if o.name.startswith('ground_floor_pine_grove'):o.data.materials[0]=g.mat('#898467')
pinepoints=[(o.location.x,-o.location.y) for o in scene.objects if o.name.startswith('old_pine_')]
for x,z in pinepoints:
 if not clear(x,z,1.2):continue
 radius=rr.uniform(1.5,3.0);n=32;radii=[radius*rr.uniform(.82,1.12) for _ in range(n)]
 for j in range(n):
  a=j*math.tau/n;b=(j+1)*math.tau/n
  for inner,outer,c in [(0,.38,'#827052'),(.38,.74,'#877959'),(.74,1,'#898064')]:
   face(c,[(x+radii[k%n]*r*math.cos(t),.009,z+radii[k%n]*r*math.sin(t)) for k,t,r in [(j,a,inner),(j+1,b,inner),(j+1,b,outer),(j,a,outer)]])
 # Scattered dry needles and tiny twigs, no tall obstacles on walking routes.
 for j in range(42):
  a=rr.random()*math.tau;r=rr.uniform(.3,radius);xx=x+math.cos(a)*r;zz=z+math.sin(a)*r
  d=rr.uniform(.06,.15);ang=rr.random()*math.tau
  face(rr.choice(['#6d604a','#a18d65']),[(xx,.019,zz),(xx+d*math.cos(ang),.019,zz+d*math.sin(ang)),(xx+.01,.019,zz+.012)])
flush('detail_forest_litter')

# Slightly irregular shoulders and a compacted center soften the old rectangular trail edges.
for a,b,w in paths:
 if w>2.6:continue
 length=math.dist(a,b);dx=(b[0]-a[0])/length;dz=(b[1]-a[1])/length;n=max(2,math.ceil(length/1.8))
 for j in range(n):
  t0=j/n;t1=(j+1)/n
  for lo,hi,c in [(-.78,-.5,'#958e70'),(-.5,.5,'#b4a487'),(.5,.78,'#958e70')]:
   face(c,[(a[0]+dx*length*t-dz*w*s,.087,a[1]+dz*length*t+dx*w*s) for t,s in [(t0,lo),(t1,lo),(t1,hi),(t0,hi)]])
flush('detail_soft_trail')

# A wet-to-dry bank follows the existing traced water edge, without changing its collision line.
bank=[]
for a,b in zip(river,river[1:]+river[:1]):
 length=math.dist(a,b)
 if length<.01:continue
 dx,dz=(b[0]-a[0])/length,(b[1]-a[1])/length;nx,nz=-dz,dx
 mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
 if inside((mid[0]+nx,mid[1]+nz),river):nx,nz=-nx,-nz
 if not (-175<mid[1]<305 and -115<mid[0]<70):continue
 for j in range(max(1,math.ceil(length/2))):
  t=j/max(1,math.ceil(length/2));x=a[0]+dx*length*t;z=a[1]+dz*length*t;bank.append((x,z,nx,nz))
 for lo,hi,y,c in [(-1.7,0,-.014,'#52776b'),(0,.9,.005,'#827f62'),(.9,2.5,.035,'#8b8c65'),(2.5,4.3,.025,'#748159')]:
  face(c,[(p[0]+nx*r,y,p[1]+nz*r) for p,r in [(a,lo),(b,lo),(b,hi),(a,hi)]])
flush('detail_riverbank')
for x,z,nx,nz in bank:
 for j in range(5):
  xx=x+nx*rr.uniform(1.4,4.5)+rr.uniform(-.7,.7);zz=z+nz*rr.uniform(1.4,4.5)+rr.uniform(-.7,.7)
  if not clear(xx,zz,.65) or inside((xx,zz),river):continue
  h=rr.uniform(.42,1.18)
  for k in range(7):
   a=k*2.4+rr.random();tip=(xx+math.cos(a)*h*.35,h,zz+math.sin(a)*h*.35)
   face(['#576f40','#738849','#92946a'][k%3],[(xx,.04,zz),(xx+.055*math.sin(a),h*.45,zz-.055*math.cos(a)),tip,(xx-.04*math.sin(a),h*.5,zz+.04*math.cos(a))])
flush('detail_riparian_reeds')

# Low spreading crowns on the existing willows, with drooping leaf sprays.
willow=next(o.data for o in scene.objects if o.name.startswith('bank_willow'))
vs=[tuple(v.co) for v in willow.vertices];fs=[tuple(p.vertices) for p in willow.polygons];mis=[p.material_index for p in willow.polygons]
for j in range(420):
 a=rr.random()*math.tau;r=rr.uniform(.8,3.5);x=r*math.cos(a);y=r*math.sin(a);z=rr.uniform(3.6,6.6)-r*.15
 ix=len(vs);vs.extend([(x-.12,y,z),(x,y-.035,z-.34),(x+.12,y,z),(x,y+.035,z+.13)]);fs.append((ix,ix+1,ix+2,ix+3));mis.append(1+j%2)
willow.clear_geometry();willow.from_pydata(vs,[],fs);willow.update()
for p,m in zip(willow.polygons,mis):p.material_index=m

# Layered hipped roofs, rafters and tiled ribs at the already mapped shelters.
for o in list(scene.objects):
 if not o.name.startswith('shelter_platform'):continue
 verts=[o.matrix_world@v.co for v in o.data.vertices];x=sum(v.x for v in verts)/len(verts);z=-sum(v.y for v in verts)/len(verts)
 g.mesh('detail_shelter_hip_roof',[(x-3.1,2.72,z-2.6),(x+3.1,2.72,z-2.6),(x+3.1,2.72,z+2.6),(x-3.1,2.72,z+2.6),(x-1.4,3.62,z),(x+1.4,3.62,z)],[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],'#4d5b5a')
 for i in range(27):
  xx=x-3+i*.23;topx=max(x-1.4,min(x+1.4,xx))
  for sign in [-1,1]:g.tube('detail_shelter_tile_roll',(xx,2.74,z+sign*2.6),(topx,3.65,z),.055,'#6e7871',n=6)
 for sign in [-1,1]:g.box('detail_shelter_eave',x,2.60,z+sign*2.35,5.4,.18,.17,'#795136',record=False)
 g.box('detail_shelter_ridge',x,3.69,z,3.0,.16,.22,'#6e7871',record=False)

# Matte forest floor and quieter green water; authored texture resources are preserved.
water=g.mat('#356c70').node_tree.nodes['Principled BSDF'];water.inputs['Roughness'].default_value=.20;water.inputs['Metallic'].default_value=.18
scene.eevee.taa_render_samples=48;scene.view_settings.exposure=.35
world['detailProvenance']={'revision':'v54','basis':'OSM and existing Esri outline; 2025 Ohmynews river photographs; 2026 Naju Senior field report','estimated':'pine curvature, forest-floor patches, bank heights, reeds and shelter roof details'}
worldpath.write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(target))
out=R/'public/models/deudeulgang.glb'
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False)
blob=out.read_bytes();n=struct.unpack_from('<I',blob,12)[0];d=json.loads(blob[20:20+n]);tail=blob[20+n:]
for m in d['materials']:
 if m.get('name')=='Pine_needles_alpha_clip':m['alphaMode']='MASK';m['alphaCutoff']=.48;m['doubleSided']=True
j=json.dumps(d,separators=(',',':')).encode();j+=b' '*((-len(j))%4);raw=struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail
out.write_bytes(raw);packed=gzip.compress(raw,compresslevel=9,mtime=0);Path(str(out)+'.gz').write_bytes(packed)
(S/'detail-v54-metrics.json').write_text(json.dumps(dict(glbBytes=len(raw),gzipBytes=len(packed),pinePrototypes=len(pine_meshes),bankSamples=len(bank),renderObjects=len(scene.objects)),indent=2))
print('DETAIL EXPORT',len(raw),len(packed),flush=True)
cam=scene.camera
for name,pos,aim,lens in [('pine-walk',(world['spawn']['x'],1.72,world['spawn']['z']),(-5,6,25),24),('riverside',(-28,1.72,15),(-130,7,70),26),('overview',(-260,290,420),(-10,0,35),38)]:
 cam.location=g.bp(*pos);cam.rotation_euler=(Vector(g.bp(*aim))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;scene.render.filepath=str(O/(name+'-v54.png'));bpy.ops.render.render(write_still=True)
print('DEUDEULGANG DETAIL COMPLETE',flush=True)
