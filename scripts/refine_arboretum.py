"""Reference-traced campus revision. Preserve the original Blender files."""
import bpy,sys,json,math,random,gzip
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
R=Path(__file__).resolve().parents[1];O=R/'outputs/arboretum';target=O/'naju-arboretum-reference-v4.blend'
if target.exists():raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(O/'naju-arboretum-base-v2.blend'))
g=MuseumGeometry(bpy.context.scene,(0,0),0);world=json.loads((R/'public/naju-arboretum-world.json').read_text(encoding='utf-8'));g.solids=world['solids'];rng=random.Random(917)
E=json.loads((R/'knowledge/sources/arboretum/satellite-export.json').read_text())['extent']
def px(u,v):
 x=E['xmin']+(E['xmax']-E['xmin'])*u/1600;y=E['ymax']-(E['ymax']-E['ymin'])*v/1200
 lon=x/6378137*180/math.pi;lat=math.atan(math.sinh(y/6378137))*180/math.pi
 return ((lon-126.8256689)*111320*math.cos(math.radians(35.00648)),-(lat-35.00648)*111320)
def local(s,t):return (-475+s*.98-t*.2,-50+s*.2+t*.98)
def inside(p,poly):
 x,z=p;hit=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:hit=not hit
 return hit
prefixes=('estimated_greenhouse','greenhouse_','estimated_garden_hedge','garden_cross','estimated_building_','roof_visitor','roof_research','window_visitor','window_research')
for o in list(bpy.data.objects):
 if o.name.startswith(prefixes):bpy.data.objects.remove(o,do_unlink=True)
g.solids=[s for s in g.solids if not s['name'].startswith(prefixes)]
traces=[]
def poly(name,points,h,color):
 p=[px(*a) for a in points];g.polygon(name,p,.015,h,color,h>1);traces.append(dict(name=name,pixels=points,height_estimate=h))
 if h>1:
  for o in list(bpy.data.objects):
   if o.name.startswith('estimated_') and inside((o.location.x,-o.location.y),p):bpy.data.objects.remove(o,do_unlink=True)
 return p
# Roof footprints traced in the referenced satellite image; heights are estimates.
for name,points,h in [
 ('visitor',[(351,451),(389,459),(368,532),(337,521)],4.5),
 ('research',[(1260,776),(1313,799),(1300,862),(1241,839)],8),
 ('office',[(1221,682),(1251,689),(1237,758),(1206,751)],5),
 ('nursery_office',[(1222,899),(1253,908),(1237,965),(1207,957)],4)]:
 p=poly('traced_building_'+name,points,h,'#d4d3c0');g.polygon('traced_roof_'+name,p,h+.02,.22,'#486b62')
 # Windows follow the traced long edge, rather than a guessed fixed alignment.
 for a,b in zip(p,p[1:]+p[:1]):
  length=math.dist(a,b);dx,dz=(b[0]-a[0])/length,(b[1]-a[1])/length
  for j in range(2,int(length)-2,3):
   for y in ([2,5.3] if h>6 else [2]):
    c=(a[0]+dx*j+dz*.05,a[1]+dz*j-dx*.05)
    g.segment('traced_window',(c[0]-dx,c[1]-dz),(c[0]+dx,c[1]+dz),.07,1.6,'#476c73',base=y-1,record=False)
greenhouses=[[(1039,271),(1058,276),(1039,368),(1021,363)],[(796,767),(821,774),(801,858),(779,852)],[(752,904),(792,913),(774,977),(736,969)],[(1164,879),(1200,888),(1180,962),(1144,951)]]
for i,pts in enumerate(greenhouses):
 p=poly('traced_greenhouse_'+str(i),pts,3.5,'#c0cecb')
 a,b=p[0],p[3];c,d=p[1],p[2]
 for j in range(13):
  t=j/12;v=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t);w=(c[0]+(d[0]-c[0])*t,c[1]+(d[1]-c[1])*t)
  g.segment('greenhouse_arch_rib',v,w,.10,.10,'#65817b',base=3.56,record=False)
# Satellite-visible research plots and paths introduce structure rather than random scattered trees.
for i,pts in enumerate([[(822,373),(949,410),(917,511),(793,476)],[(951,414),(1138,463),(1107,566),(920,515)],[(651,135),(765,159),(751,219),(636,191)],[(668,282),(826,321),(793,380),(650,344)]]):
 p=poly('traced_research_plot_'+str(i),pts,.012,'#7a885b' if i<2 else '#80795a')
 for j in range(1,14):
  t=j/14;a=(p[0][0]*(1-t)+p[1][0]*t,p[0][1]*(1-t)+p[1][1]*t);b=(p[3][0]*(1-t)+p[2][0]*t,p[3][1]*(1-t)+p[2][1]*t)
  g.segment('nursery_row',a,b,.45,.22,'#4e6e44',base=.06,record=False)
 for o in list(bpy.data.objects):
  if o.name.startswith('estimated_broadleaf') and inside((o.location.x,-o.location.y),p):bpy.data.objects.remove(o,do_unlink=True)
def path(name,points,width=2):
 p=[px(*v) for v in points]
 for a,b in zip(p,p[1:]):
  g.segment(name,a,b,width,.05,'#c0b292',base=.10,record=False)
  dx,dz=b[0]-a[0],b[1]-a[1]
  for o in list(bpy.data.objects):
   if not o.name.startswith(('estimated_broadleaf','estimated_juniper')):continue
   x,z=o.location.x,-o.location.y;u=max(0,min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz or 1)))
   if math.hypot(x-a[0]-u*dx,z-a[1]-u*dz)<width/2+1.5:bpy.data.objects.remove(o,do_unlink=True)
 traces.append(dict(name=name,pixels=points,width_estimate=width))
path('garden_curved_walk',[(475,394),(512,422),(555,432),(605,413),(645,383),(641,352),(619,328),(593,326),(572,343),(567,374),(586,397)],2.3)
path('garden_outer_walk',[(485,432),(557,455),(658,483),(719,493),(753,470),(776,410),(770,369),(750,350),(722,358),(700,389),(687,449)],2.2)
path('garden_connection',[(627,288),(621,328)],2)
# Circle garden corrected to the satellite position; cross paths remain open.
cx,cz=px(402,876)
for o in list(bpy.data.objects):
 if o.name.startswith(('estimated_broadleaf','estimated_juniper')) and math.hypot(o.location.x-cx,-o.location.y-cz)<30:bpy.data.objects.remove(o,do_unlink=True)
for rad in [5,10,15,21,27]:
 for j in range(64):
  a=j*math.tau/64;b=(j+1)*math.tau/64
  if abs(math.sin(a))<.07 or abs(math.cos(a))<.07:continue
  g.segment('traced_round_hedge',(cx+rad*math.cos(a),cz+rad*math.sin(a)),(cx+rad*math.cos(b),cz+rad*math.sin(b)),.8,.65,'#4b6842',base=.07,record=False)
for a in [0,math.pi/2]:g.segment('round_garden_walk',(cx-30*math.cos(a),cz-30*math.sin(a)),(cx+30*math.cos(a),cz+30*math.sin(a)),2,.04,'#cabb9e',base=.11,record=False)
world['places']=[dict(p,position=[cx,cz],arrival=[cx,cz]) if p['id']=='garden' else p for p in world['places']]
# Entrance gate, booth, upright barriers and pale edging visible in the 2023 blog photograph.
for s,t,w,d,h,c in [(-1,-9,3,4,3.8,'#564d3f'),(-1,10,1.1,1,3.4,'#564d3f'),(2,3.9,1.5,2,2.3,'#e2dfcd')]:
 x,z=local(s,t);g.box('photo_gate_structure',x,h/2,z,w,h,d,c,True)
 if w<2:
  g.box('gate_window',x,1.55,z-d/2-.06,w*.8,.75,.07,'#426569',record=False)
for t in [-3.8,6.5]:
 x,z=local(4,t);g.tube('raised_barrier',(x,.7,z),(x,4.3,z),.06,'#ebe4ca')
for s in [1,3,5,7]:
 for t in [-8,9]:
  x,z=local(s,t);g.tube('bollard',(x,0,z),(x,.8,z),.07,'#ba6550')
# Path edge ground-cover bands and board joints from pedestrian photographs.
for s in range(20,424,3):
 for t in [-4,4]:
  x,z=local(s,t);gv=[];gf=[]
  for j in range(28):
   xx=x+rng.uniform(-1.4,1.4);zz=z+rng.uniform(-.4,.4);h=rng.uniform(.15,.38);i=len(gv)
   gv.extend([(xx-.06,.02,zz),(xx+.06,.02,zz),(xx+.09,h,zz+.04),(xx,.02,zz-.06),(xx,.02,zz+.06),(xx-.04,h,zz+.09)]);gf.extend([(i,i+1,i+2),(i+3,i+4,i+5)])
  g.mesh('avenue_groundcover',gv,gf,'#5b793f')
 if s%9==2:
  a,b=local(s,-2.9),local(s,2.9);g.segment('path_expansion_joint',a,b,.025,.008,'#8f8875',base=.105,record=False)
# Detailed shared tree mesh: tapered bark and small leaf sprays replace the round cloud canopy.
oldtrees=[o for o in bpy.data.objects if o.name.startswith('estimated_meta')]
before=set(bpy.data.objects);verts=[];faces=[]
for y,r in [(0,.4),(1,.29),(7,.22),(14,.13),(20,.025)]:
 for j in range(12):verts.append((r*math.cos(j*math.tau/12),y,r*math.sin(j*math.tau/12)))
for k in range(4):
 for j in range(12):a=k*12+j;b=k*12+(j+1)%12;faces.append((a,b,b+12,a+12))
trunk=g.mesh('reference_meta_trunk',verts,faces,'#705d43',smooth=True)
for c in ['#65513c','#80694b','#917755']:trunk.data.materials.append(g.mat(c))
for f in trunk.data.polygons:f.material_index=rng.randrange(4)
lv=[];lf=[]
for tier in range(18):
 y=5.4+tier*.76;spread=3.7*(1-tier/22)
 for j in range(4):
  a=j*math.tau/4+tier*.87;end=(spread*math.cos(a),y+.6,spread*math.sin(a))
  g.tube('reference_meta_branch',(0,y,0),end,.055,'#756548',n=5)
  for k in range(1,10):
   u=k/10
   for side in [-1,1]:
    for q in range(3):
     x=end[0]*u+math.cos(a+math.pi/2)*side*(q+1)*.18;z=end[2]*u+math.sin(a+math.pi/2)*side*(q+1)*.18
     yy=y+u*.6+rng.uniform(-.2,.2);i=len(lv);r=.23+rng.random()*.15
     lv.extend([(x-r,yy,z),(x,yy+.06,z-r*.5),(x+r,yy,z),(x,yy-.06,z+r*.5)]);lf.extend([(i,i+1,i+2),(i,i+2,i+3)])
leaf=g.mesh('reference_meta_leaf_sprays',lv,lf,'#648342')
for c in ['#3f6337','#77944a','#52753c']:leaf.data.materials.append(g.mat(c))
for f in leaf.data.polygons:f.material_index=rng.randrange(4)
parts=list(set(bpy.data.objects)-before);bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=trunk;bpy.ops.object.join();proto=bpy.context.object
for o in oldtrees:o.data=proto.data
bpy.data.objects.remove(proto,do_unlink=True)
# Pond edge follows the OSM polygon; low stones add a readable water boundary.
pond=next(s for s in g.solids if s['name']=='pond_boundary')['footprint']
for a,b in zip(pond,pond[1:]+pond[:1]):g.segment('pond_stone_edge',a,b,.55,.22,'#a6a78d',base=.03,record=False)
world['solids']=g.solids;world['subtitle']='나주수목원 · 사진·위성 참고';world['limitations']=['Satellite traced footprints and paths; photographs inform entrance and tree forms; heights and individual plants estimated. Satellite acquisition date unverified.']
(R/'public/naju-arboretum-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(R/'knowledge/sources/arboretum/detail-traces.json').write_text(json.dumps(dict(source='Esri World Imagery export, retrieval 2026-09-16, acquisition date unverified',traces=traces),ensure_ascii=False,indent=2),encoding='utf-8')
scene=bpy.context.scene;bpy.ops.wm.save_as_mainfile(filepath=str(target));out=R/'public/models/naju-arboretum.glb'
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
with gzip.open(str(out)+'.gz','wb',compresslevel=9) as f:f.write(out.read_bytes())
scene.render.filepath=str(O/'detail-overview.png');bpy.ops.render.render(write_still=True)
cam=scene.camera;x,z=local(24,0);tx,tz=local(130,0);cam.location=g.bp(x,1.72,z);cam.rotation_euler=(Vector(g.bp(tx,4,tz))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=24
scene.render.filepath=str(O/'detail-avenue.png');bpy.ops.render.render(write_still=True)
print('DETAIL COMPLETE',out.stat().st_size)
