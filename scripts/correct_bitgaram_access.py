"""Mapped monorail, photo-informed stone slide, and separately walkable forest approach.
Never overwrite an artist .blend. Plan trace is OSM; elevation and slide offsets are estimates.
"""
import bpy,bmesh,json,math,sys,hashlib,random
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from museum_geometry import MuseumGeometry
revision='v68' if '--junction-fix' in sys.argv else 'v67'
O=R/('outputs/quality-'+revision);O.mkdir(exist_ok=True)
TARGET=O/('bitgaram-access-'+revision+'.blend')
if TARGET.exists():raise RuntimeError('Existing artist revision preserved. Choose a new revision.')
SOURCE=R/'outputs/quality-v58/bitgaram-park-crowns-v58.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene
source=json.loads((R/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf8'))
ways={w['id']:w for w in source['ways']};rail2=ways['508048300']['points']
oldworld=json.loads((R/'work/park-before-v67/bitgaram-park-world.json' if revision=='v68' else R/'public/bitgaram-park-world.json').read_text(encoding='utf8'))
(O/('bitgaram-park-world-before-'+revision+'.json')).write_text(json.dumps(oldworld,ensure_ascii=False),encoding='utf8')
g=MuseumGeometry(scene,(0,0),0)
OLD=('walk-floor_approach','walk-floor_turnaround','deck_plank_joint','path_bollard','timber_guard_post','timber_post_cap','timber_deck_pier','timber_horizontal_rail','timber_deck_stringer','timber_step_riser','pathside_shrub')
removed=[]
for o in list(scene.objects):
 if o.name.startswith(OLD):removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)

def densify(points,step=.55):
 out=[]
 for a,b in zip(points,points[1:]):
  count=max(1,math.ceil(math.dist(a,b)/step))
  out.extend([[a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count] for i in range(count)])
 return out+[points[-1]]
def hill(x,z):return min(16*math.exp(-((x/100)**2+(z/105)**2)*1.6),15.75)
def forest_height(x,z):
 r=math.hypot(x,z);h=hill(x,z)+.16
 return 16 if r<=23 else 16+(h-16)*min(1,(r-23)/9)
def railheight(z):return 16.6+(6.82-16.6)*(z-rail2[0][1])/(rail2[-1][1]-rail2[0][1])
rail=[(x,railheight(z),z) for x,z in densify(rail2,1)]
forest=[(x,forest_height(x,z),z) for x,z in densify(ways['549492174']['points'][:27])]
# Start and end follow the mapped public winding path, distinct from the rail corridor.

# A 96 m historic stone slide is photo-confirmed; centreline curvature below is estimated.
def slide_route(amplitude):
 return [(4+t-amplitude*math.sin(math.pi*t),16-9.78*max(0,(t-.11)/.89),14+92*t) for t in [i/240 for i in range(241)]]
lo,hi=0,30
for _ in range(32):
 mid=(lo+hi)/2;r=slide_route(mid);length=sum(math.dist(a,b) for a,b in zip(r,r[1:]))
 if length<96:lo=mid
 else:hi=mid
slide=slide_route((lo+hi)/2);deck=[(x+1.24,y,z) for x,y,z in slide]

def distance(p,route):
 best=1e9
 for a,b in zip(route,route[1:]):
  dx,dz=b[0]-a[0],b[2]-a[2];t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[2])*dz)/(dx*dx+dz*dz or 1)))
  best=min(best,math.hypot(p[0]-a[0]-t*dx,p[1]-a[2]-t*dz))
 return best
# Remove only estimated plant instances physically occupying the new corridors, paired together.
tree_removals=[];root_positions=[]
candidates=[((o.location.x,-o.location.y),o.get('tree_source_trunk')) for o in scene.objects if o.get('vegetation_lod')=='near']
for p,trunk in candidates:
 if not (distance(p,forest)<1.8 or distance(p,rail)<1.1 or distance(p,deck)<2.15):continue
 root_positions.append(p);tree_removals.append(trunk)
 for q in list(scene.objects):
  if q.name==trunk or q.get('tree_source_trunk')==trunk:
   removed.append(q.name);bpy.data.objects.remove(q,do_unlink=True)

def floor_route(name,route,width,color):
 for a,b in zip(route,route[1:]):
  height=(a[1]+b[1])/2;length=math.hypot(b[0]-a[0],b[2]-a[2]);angle=math.atan2(b[2]-a[2],b[0]-a[0])
  g.box(name,(a[0]+b[0])/2,height-.055,(a[2]+b[2])/2,length+.16,.11,width,color,rotation=angle)
floor_route('walk-floor_mapped_forest_549492174',forest,2.45,'#ae9770')
floor_route('walk-floor_slide_side_stairs',deck,1.36,'#987149')
g.box('walk-floor_lower_station',13,6.165,108,19,.11,8,'#c3c6be')
g.box('walk-floor_slide_landing',5,6.165,107.4,6,.11,3.2,'#baa991')
g.box('walk-floor_upper_station',10.1,15.945,14,5.2,.11,6,'#c2bba8')
# Shared stone speckle texture authored procedurally, never copied from reference photographs.
rng=random.Random(67096);image=bpy.data.images.new('Authored_granite_speckle',width=128,height=128)
pixels=[]
for i in range(128*128):
 v=.23+rng.random()*.16
 if rng.random()<.09:v=.53
 pixels.extend([v,v*1.02,v*1.035,1])
image.pixels.foreach_set(pixels);image.pack()
granite=g.mat('#6f7676');granite.name='Stone_slide_polished_granite';nodes=granite.node_tree.nodes
tex=nodes.new('ShaderNodeTexImage');tex.image=image;granite.node_tree.links.new(tex.outputs['Color'],nodes['Principled BSDF'].inputs['Base Color']);nodes['Principled BSDF'].inputs['Roughness'].default_value=.28
# Closed U section: polished open trough rather than a playground tube.
section=[(-.52,.43),(-.40,.43),(-.35,.19),(-.24,.065),(0,0),(.24,.065),(.35,.19),(.40,.43),(.52,.43),(.52,-.12),(-.52,-.12)]
verts=[];faces=[]
for i,(x,y,z) in enumerate(slide):
 a=slide[max(0,i-1)];b=slide[min(len(slide)-1,i+1)];dx,dz=b[0]-a[0],b[2]-a[2];norm=math.hypot(dx,dz);sx,sz=dz/norm,-dx/norm
 verts.extend([(x+sx*u,y+h,z+sz*u) for u,h in section])
N=len(section)
for i in range(len(slide)-1):
 for j in range(N):faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
faces.extend([tuple(range(N-1,-1,-1)),tuple((len(slide)-1)*N+j for j in range(N))])
trough=g.mesh('photo_stone_slide_U_trough',verts,faces,'#6f7676',smooth=True)
trough['reference']='Newsis 2016-08-30: open granite trough, historic length 96 m';trough['estimated_alignment']=True

# Rail is a single box-beam guideway with two wheel-running strips, on the exact OSM line.
for i,(a,b) in enumerate(zip(rail,rail[1:])):
 g.tube('mapped_monorail_508048300_beam',a,b,.21,'#8e9690',n=4)
 for side in [-1,1]:g.tube('monorail_running_strip',(a[0]+side*.21,a[1]+.14,a[2]),(b[0]+side*.21,b[1]+.14,b[2]),.024,'#bac3c2',n=6)
 if i%7==0:
  base=hill(a[0],a[2]);g.box('monorail_support',a[0],(base+a[1]-.2)/2,a[2],.32,max(.15,a[1]-.2-base),.38,'#969c93',record=False)
  g.box('monorail_support_foot',a[0],base+.08,a[2],.82,.16,.8,'#aeaca0',record=False)
 proxy=g.segment('monorail_guideway_boundary',(a[0],a[2]),(b[0],b[2]),.7,.7,'#8e9690',base=min(a[1],b[1])-.35,collision=True);bpy.data.objects.remove(proxy,do_unlink=True)
# Photo-informed white cab with dark continuous glazing, orange lower trim, flat vented roof.
cx,cz=rail2[0];cy=railheight(cz)
g.box('photo_monorail_cab_body',cx,cy+1.13,cz+.8,2.15,1.48,3.3,'#e1e3d9',collision=True)
g.box('photo_monorail_cab_orange_skirt',cx,cy+.45,cz+.8,2.18,.22,3.35,'#b56e36',record=False)
g.box('photo_monorail_cab_roof',cx,cy+1.94,cz+.8,2.22,.15,3.42,'#b7bfbc',record=False)
for side in [-1,1]:
 for off in [-.72,.72]:
  g.box('photo_monorail_cab_side_glass',cx+side*1.085,cy+1.30,cz+.8+off,.025,.91,1.24,'#284b50',record=False)
 g.box('photo_monorail_cab_end_glass',cx,cy+1.3,cz+.8+side*1.666,1.74,.92,.025,'#284b50',record=False)
 for off in [-.73,.73]:g.box('photo_monorail_cab_door_frame',cx+side*1.108,cy+1.25,cz+.8+off,.035,1.14,.045,'#d1d6ce',record=False)
for i in range(12):g.box('monorail_roof_vent',cx-.7+i*.12,cy+2.026,cz+.8,.027,.012,1.1,'#687871',record=False)
# Covered slide gallery: timber arches, longitudinal slats, translucent blue outer wall.
blue=g.mat('#9ccad0');blue.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value=.38;blue.diffuse_color=(*blue.diffuse_color[:3],.38);blue.surface_render_method='DITHERED';blue.use_backface_culling=False
for i in range(0,len(slide)-1,8):
 x,y,z=slide[i];ax=x+.48
 arc=[(ax+1.64*math.cos(j*math.pi/16),y+.48+2.35*math.sin(j*math.pi/16),z) for j in range(17)]
 for a,b in zip(arc,arc[1:]):g.tube('slide_gallery_timber_arch',a,b,.065,'#654b33',n=6)
 for side in [-1,1]:g.box('slide_gallery_post',ax+side*1.64,y+.30,z,.13,.6,.13,'#725335',record=False)
 if i+8<len(slide):
  bx,by,bz=slide[i+8];bx+=.48
  for j in range(1,16):
   theta=j*math.pi/16
   g.tube('slide_gallery_longitudinal_slats',(ax+1.64*math.cos(theta),y+.48+2.35*math.sin(theta),z),(bx+1.64*math.cos(theta),by+.48+2.35*math.sin(theta),bz),.025,'#826244',n=4)
  g.mesh('slide_gallery_blue_side',[(ax-1.64,y+.3,z),(ax-1.5,y+1.42,z),(bx-1.5,by+1.42,bz),(bx-1.64,by+.3,bz)],[(0,1,2,3)],'#9ccad0')
  for h in [.25,.58,.91,1.1]:g.tube('slide_gallery_wood_guard',(ax+1.64,y+h,z),(bx+1.64,by+h,bz),.034,'#9a7149',n=4)
  # Stone trough blocks casual walking; the parallel stairs remain walkable.
  proxy=g.segment('stone_slide_safety_boundary',(x,z),(slide[i+8][0],bz),1.07,1.05,'#6f7676',base=min(y,by),collision=True);bpy.data.objects.remove(proxy,do_unlink=True)
  proxy=g.segment('slide_gallery_outer_guard',(ax+1.64,z),(bx+1.64,bz),.1,1.1,'#725335',base=min(y,by),collision=True);bpy.data.objects.remove(proxy,do_unlink=True)
# Plank joints and stair risers follow the corrected gallery, without hundreds of draw calls.
for i,(a,b) in enumerate(zip(deck,deck[1:])):
 if i%2==0:
  g.box('slide_gallery_tread_joint',a[0],a[1]+.002,a[2],1.34,.005,.012,'#765333',record=False)
 if a[1]-b[1]>.001:g.box('slide_gallery_stair_riser',(a[0]+b[0])/2,(a[1]+b[1])/2-.055,b[2],1.34,a[1]-b[1],.026,'#84613e',record=False)

# Merge new repeated pieces by category and material. Floors keep exact individual JSON footprints.
groups={}
for c in g.groups.values():
 for o in list(c.objects):
  if o.type=='MESH':groups.setdefault(o.name.split('.')[0],[]).append(o)
for name,objects in groups.items():
 if len(objects)<2:continue
 vertices=[];polygons=[];uvs=[]
 for o in objects:
  offset=len(vertices);vertices.extend([tuple(o.matrix_world@v.co) for v in o.data.vertices]);polygons.extend([tuple(offset+i for i in p.vertices) for p in o.data.polygons]);uvs.extend([tuple(u.uv) for u in o.data.uv_layers.active.data])
 mesh=bpy.data.meshes.new(name+'_shared');mesh.from_pydata(vertices,[],polygons);mesh.update();mesh.materials.append(objects[0].data.materials[0]);uv=mesh.uv_layers.new()
 for i,p in enumerate(uvs):uv.data[i].uv=p
 owner=objects[0].users_collection[0]
 for o in objects:bpy.data.objects.remove(o,do_unlink=True)
 obj=bpy.data.objects.new(name,mesh);owner.objects.link(obj)
obj=bpy.data.objects.get('mapped_monorail_508048300_beam');obj['osm_way']='508048300';obj['reference_category']='mapped_plan_estimated_elevation'
world=dict(oldworld);world['solids']=[dict(s,size=[s['size'][0],6.1,s['size'][2]]) if s['name']=='photo_exhibition_shell' else s for s in oldworld['solids'] if not s['name'].startswith(('walk-floor_approach','walk-floor_turnaround','timber_walk_guard')) and not (s['name'] in ['tree_trunk','woodland_trunk'] and any(math.hypot(s['position'][0]-p[0],s['position'][2]-p[1])<.1 for p in root_positions))]+g.solids
world['bounds']=[-32,85,-30,185]
world['arrivals']=dict(oldworld.get('arrivals',{}),lower={'x':16,'z':108,'height':6.22,'yaw':0},forest={'x':forest[0][0],'z':forest[0][2],'height':forest[0][1],'yaw':0},slide={'x':deck[-1][0],'z':deck[-1][2],'height':deck[-1][1],'yaw':0})
world['places']=oldworld['places']+[{'id':'lower-station','name':'전시동 · 모노레일 하부','description':'모노레일과 돌미끄럼틀을 바라보세요. 숲길과 나란한 계단으로 걸어 올라갈 수 있습니다.','position':[13,108],'radius':10,'arrival':[16,108],'arrivalHeight':6.22}]
WP=O/('bitgaram-park-world-'+revision+'.json');WP.write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf8')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.export_scene.gltf(filepath=str(O/('bitgaram-park-'+revision+'.glb')),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False)
report={'source':str(SOURCE.relative_to(R)),'output':str(TARGET.relative_to(R)),'world_source':str((O/('bitgaram-park-world-before-'+revision+'.json')).relative_to(R)),'world_output':str(WP.relative_to(R)),'removed_objects':removed,'cleared_estimated_tree_roots':tree_removals,'mapped_monorail_way':'508048300','mapped_monorail_plan':rail2,'rail_route':rail,'mapped_forest_way':'549492174','forest_route':forest,'slide_route':slide,'stairs_route':deck,'slide_authored_length':sum(math.dist(a,b) for a,b in zip(slide,slide[1:])),'estimated':['all vertical profiles; no DEM','slide plan offset, width and gallery dimensions','cab dimensions and static position','vegetation clearance of previously estimated trees'],'references':[{'url':'https://live112.tistory.com/4710','date':'2017-01-27','evidence':'cab, lower/upper stations, site guide and building relation'},{'url':'https://www.newsis.com/view/NISX20160830_0014355874','date':'2016-08-30','evidence':'96 m historic stone slide, granite U trough, timber arched gallery and blue side screen'}]}
(R/('knowledge/sources/bitgaram/access-'+revision+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print('ACCESS EXPORTED',len(removed),len(forest),len(g.solids),flush=True)
