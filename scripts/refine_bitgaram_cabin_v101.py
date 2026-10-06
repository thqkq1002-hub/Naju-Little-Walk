"""Preserve the shipped cabin as source; author a rounded, photo-informed shell."""
import bpy,json,sys,math,gzip,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from museum_geometry import MuseumGeometry
O=R/'outputs/bitgaram-v101';O.mkdir(exist_ok=True,parents=True)
source=O/'cabin-source-v83.glb'
if not source.exists():shutil.copyfile(R/'public/models/bitgaram-monorail.glb',source)
target=O/'bitgaram-monorail-v101.blend'
if target.exists():raise RuntimeError('Existing artist cabin preserved')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source));scene=bpy.context.scene
for o in list(scene.objects):
 if o.name.startswith(('cab_end_glass','cab_end_window_lower_frame','cab_end_lower_panel','cab_marker_light','cab_corner_pillar','cab_roof','cab_ceiling','label_')) and not o.name.startswith(('cab_roof_aircon','cab_ceiling_light')):bpy.data.objects.remove(o,do_unlink=True)
g=MuseumGeometry(scene,(0,0),0);white='#e3e6df';black='#253135';orange='#ec9d24';silver='#b0b8b5'
def box(n,p,sz,c):return g.box(n,*p,*sz,c,record=False)
def rounded(w,lo,hi,r):
 pts=[]
 for cx,cy,start in [(w/2-r,lo+r,-90),(w/2-r,hi-r,0),(-w/2+r,hi-r,90),(-w/2+r,lo+r,180)]:
  for j in range(9):
   a=math.radians(start+j*90/8);pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
 return pts
def ring(name,outer,inner,z,depth,c):
 n=len(outer);verts=[(x,y,zz) for zz in (z-depth/2,z+depth/2) for loop in (outer,inner) for x,y in loop];faces=[]
 for i in range(n):
  k=(i+1)%n;faces.extend([(i,k,n+k,n+i),(2*n+i,3*n+i,3*n+k,2*n+k),(i,2*n+i,2*n+k,k),(n+i,n+k,3*n+k,3*n+i)])
 return g.mesh(name,verts,faces,c)
glass=g.mat('#8eafac');bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Alpha'].default_value=.22;bs.inputs['Roughness'].default_value=.14;glass.surface_render_method='DITHERED';glass.use_backface_culling=False
outer=rounded(2.14,.29,2.64,.56);window=rounded(1.94,.80,2.50,.47);inner=rounded(1.81,.87,2.43,.43)
for side in (-1,1):
 z=side*2.005
 ring('cab101_rounded_white_shell',outer,window,z,.075,white)
 ring('cab101_dark_window_seal',window,inner,z+side*.045,.025,black)
 pane=g.mesh('cab101_curved_end_glazing',[(x,y,z+side*.047) for x,y in inner],[tuple(range(len(inner)))],'#8eafac')
 box('cab101_orange_front_band',(0,1.22,z+side*.07),(1.93,.15,.016),orange)
 for x in (-.77,.77):box('cab101_marker_light',(x,.69,z+side*.05),(.11,.055,.02),'#fff2cc')
 # Rounded quarter pillars follow the actual end silhouette instead of full
 # height square corner bars cutting across the glazing.
 for x in (-1.02,1.02):box('cab101_side_end_pillar',(x,1.49,side*1.80),(.075,1.65,.11),black)
roof=box('cab101_rounded_roof',(0,2.55,0),(2.16,.18,4.05),white)
mod=roof.modifiers.new('Rounded manufactured roof edge','BEVEL');mod.width=.085;mod.segments=5
box('cab_ceiling',(0,2.45,0),(1.98,.028,3.85),'#d5d8d0')
# Keep hollow floor/door origins/bogies. Shift the orange visual band to the
# window line visible on the 2025 photograph; white skirt stays below it.
for o in list(scene.objects):
 if o.type=='MESH' and o.name.startswith(('cab_orange_sill','door_bottom')):
  o.data.materials.clear();o.data.materials.append(g.mat(white))
for side in (-1,1):
 for zz,L in ([(-1.33,1.02),(1.33,1.02)] if side>0 else [(0,3.77)]):box('cab101_side_orange_band',(side*1.06,1.22,zz),(.012,.15,L),orange)
for label,z in [('left',-.37),('right',.37)]:
 ob=box('cab101_door_orange_band',(1.077,1.22,z),(.012,.15,.69),orange);ob.parent=bpy.data.objects['monorail_door_'+label]
for o in scene.objects:
 if o.type=='MESH':o['reference_revision']='bitgaram-access-v101';o['dimensions_surveyed']=False
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
path=O/'bitgaram-monorail.glb';bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,export_animations=False)
raw=path.read_bytes();assert len(raw)<512*1024
path.with_suffix('.glb.gz').write_bytes(gzip.compress(raw,9,mtime=0))
for ext in ('.glb','.glb.gz'):shutil.copyfile(path.with_suffix(ext),R/('public/models/bitgaram-monorail'+ext))
report=dict(source=str(source.relative_to(R)),sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),sourceType='preserved shipped v83 GLB; original v83 blend unavailable locally',output=str(target.relative_to(R)),modelBytes=len(raw),gzipBytes=path.with_suffix('.glb.gz').stat().st_size,doorsPreserved=True,surveyed=False)
(R/'knowledge/sources/bitgaram/access-v101/cabin.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('CABIN_V101',json.dumps(report))
