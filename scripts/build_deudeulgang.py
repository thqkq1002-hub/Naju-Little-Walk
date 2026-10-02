"""Drdeulgang pine grove. OSM paths/POIs, satellite shoreline, photo-informed trees.
Individual trees, elevations and minor furniture are estimates, not surveyed objects.
"""
import bpy,sys,json,math,random,gzip,struct,numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
R=Path(__file__).resolve().parents[1];O=R/'outputs/deudeulgang';O.mkdir(exist_ok=True)
S=R/'knowledge/sources/deudeulgang';target=O/'deudeulgang-pine-grove-v2.blend'
if target.exists():raise RuntimeError('Existing artist revision preserved')
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;g=MuseumGeometry(scene,(0,0),0);rng=random.Random(200951)
D=json.loads((S/'geometry.json').read_text(encoding='utf-8'))
def geo(lon,lat):return ((lon-126.85475)*91175,(35.0185-lat)*111195)
def pixel(u,v):return geo(126.851+u*.009/1500,35.0245-v*.009/1500)
def inside(p,poly):
 x,z=p;hit=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:hit=not hit
 return hit
def distance(p,a,b):
 dx,dz=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dz)/(dx*dx+dz*dz or 1)))
 return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dz)
def smooth(points,steps=2):
 for _ in range(steps):points=[tuple(a[k]*t+b[k]*(1-t) for k in range(2)) for a,b in zip(points,points[1:]+points[:1]) for t in [.75,.25]]
 return points
grove=smooth([pixel(*p) for p in [(605,750),(728,718),(708,848),(680,1000),(663,1140),(690,1295),(659,1365),(564,1386),(495,1340),(493,1200),(519,1080),(536,990),(529,910),(555,820)]])
river=smooth([pixel(*p) for p in [(865,0),(840,240),(835,435),(765,540),(711,740),(580,772),(528,938),(510,1089),(480,1200),(484,1360),(503,1500),(237,1500),(217,1330),(246,1190),(251,1050),(279,840),(306,705),(311,629),(367,565),(413,486),(500,438),(620,334),(736,179),(800,0)]])
g.box('ground_floor_landscape',0,-.24,0,1100,.30,1400,'#92946a',record=False)
g.polygon('ground_floor_pine_grove',grove,-.08,.08,'#7b8057')
g.polygon('mapped_river_water',river,-.05,.02,'#356c70')
g.collider('river_no_walking',river,-8,10)
water=g.mat('#356c70');water.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.27;water.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value=.25
paths=[]
def path(name,pts,width,color,y=.025):
 for a,b in zip(pts,pts[1:]):
  g.segment(name,a,b,width,.025,color,base=y,record=True);paths.append((a,b,width))
# Exact mapped centre lines; the modest widths and materials are visual estimates.
for w in D['ways']:
 t=w['tags'];pts=[geo(*p) for p in w['points']];kind=t.get('highway')
 if kind and kind in ['track','service','footway','path','tertiary','secondary']:
  pts2=[]
  for a,b in zip(pts,pts[1:]):
   if min(a[0],b[0])<-450 or max(a[0],b[0])>550 or min(a[1],b[1])<-420 or max(a[1],b[1])>430:continue
   if t.get('bridge')=='yes':
    # Background bridge: elevated deck is not an explorable walk surface.
    g.segment('bridge_deck',a,b,10,.75,'#949386',base=3.1,record=False)
    dx,dz=b[0]-a[0],b[1]-a[1];ll=math.hypot(dx,dz);nx,nz=-dz/ll,dx/ll
    for sign in [-1,1]:
     aa=(a[0]+nx*4.9*sign,a[1]+nz*4.9*sign);bb=(b[0]+nx*4.9*sign,b[1]+nz*4.9*sign)
     g.segment('bridge_rail',aa,bb,.16,.75,'#e0dcca',base=3.8,record=False)
    for j in range(1,5):
     q=j/5;g.box('bridge_pier',a[0]+dx*q,1,a[1]+dz*q,1.5,4,6,'#9d9b8b',True)
   else:path('path_osm_'+w['id'],[a,b],2.5 if kind in ['footway','path'] else 4 if kind in ['track','service'] else 8,'#c4b799' if kind in ['footway','path'] else '#939789' if kind in ['track','service'] else '#626c69',.025 if kind in ['footway','path'] else .06)
 if t.get('amenity')=='parking':g.polygon('road_parking',pts,.035,.015,'#a4a18e')
# River-edge footpath is interpreted from visible bare strips in the satellite image.
edge=[pixel(*p) for p in [(670,745),(603,815),(572,920),(566,1017),(551,1140),(537,1260),(560,1335),(615,1344),(652,1300)]]
path('path_satellite_riverside',edge,2.4,'#b1a27f',.027)
path('path_link_south',[edge[-1],geo(126.8550257,35.0173335)],2.3,'#b1a27f',.030)
path('path_link_middle',[edge[4],geo(126.854724,35.0178871)],2.3,'#b1a27f',.031)
# Farmland parcel shapes traced from the same imagery; crop type is illustrative.
fields=[[(749,820),(961,820),(923,984),(718,973)],[(725,985),(923,993),(927,1079),(713,1086)],[(714,1098),(905,1090),(849,1313),(706,1337)],[(989,826),(1126,813),(1157,1054),(956,1076)],[(975,1107),(1160,1120),(1115,1324),(904,1319)],[(818,473),(903,444),(1022,507),(973,651),(801,638)],[(972,646),(1072,493),(1203,560),(1149,660)]]
for i,f in enumerate(fields):
 p=[pixel(*v) for v in f];g.polygon('satellite_field_'+str(i),p,-.075,.025,['#869559','#a9a070','#76894e','#adb082'][i%4])
 if len(p)!=4:continue
 a,b,c,d=p
 for j in range(1,22):
  t=j/22;aa=(a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t);bb=(d[0]*(1-t)+c[0]*t,d[1]*(1-t)+c[1]*t)
  g.segment('crop_row',aa,bb,.28,.025,'#747c4d',base=-.035,record=False)

class Plant:
 def __init__(self):self.v=[];self.f=[];self.mi=[];self.uv=[]
 def face(self,ps,mi=0):
  n=len(self.v);self.v.extend(ps);self.f.append(tuple(range(n,n+len(ps))));self.mi.append(mi)
  self.uv.extend([(0,0),(1,0),(1,1),(0,1)] if mi==5 else [(math.atan2(p[2],p[0])/math.tau,p[1]*.55) for p in ps])
 def tube(self,a,b,r,q,mi=0,n=8):
  a,b=Vector(a),Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,1,0)))
  if u.length<.01:u=axis.cross(Vector((1,0,0)))
  u.normalize();v=axis.cross(u)
  for j in range(n):
   t=j*math.tau/n;tt=(j+1)*math.tau/n
   self.face([a+r*(math.cos(t)*u+math.sin(t)*v),a+r*(math.cos(tt)*u+math.sin(tt)*v),b+q*(math.cos(tt)*u+math.sin(tt)*v),b+q*(math.cos(t)*u+math.sin(t)*v)],mi)
 def blade(self,a,d,length,width,mi):
  a=Vector(a);d=Vector(d).normalized();side=d.cross(Vector((0,1,0)))
  if side.length<.01:side=d.cross(Vector((1,0,0)))
  side.normalize();mid=a+d*length*.5;tip=a+d*length
  self.face([a,mid+side*width,tip,mid-side*width],mi)
 def finish(self,name,mats):
  me=bpy.data.meshes.new(name);me.from_pydata([(p[0],-p[2],p[1]) for p in self.v],[],self.f);me.update()
  for mat in mats:me.materials.append(mat)
  uv=me.uv_layers.new(name='Pine_UV')
  for p,mi in zip(me.polygons,self.mi):
   p.material_index=mi;p.use_smooth=mi<2
   for li in p.loop_indices:uv.data[li].uv=self.uv[me.loops[li].vertex_index]
  return me
pine_mats=[g.mat(c) for c in ['#654636','#a16943','#284933','#385d38','#537246']]
for mat in pine_mats[2:]:mat.use_backface_culling=False
# Original procedural pine-needle texture, authored here (no borrowed photo artwork).
n=512;rgba=np.zeros((n,n,4),dtype=np.float32);rr=random.Random(871)
def stroke(a,b,width,color):
 a=np.array(a);b=np.array(b);steps=max(2,int(np.linalg.norm(b-a)*1.5))
 for t in np.linspace(0,1,steps):
  p=a+(b-a)*t;x,y=int(p[0]),int(p[1]);r=max(1,int(width*(1-t*.65)))
  if r<x<n-r and r<y<n-r:rgba[y-r:y+r+1,x-r:x+r+1,:3]=color;rgba[y-r:y+r+1,x-r:x+r+1,3]=1
for j in range(13):
 angle=j*2.399;rad=rr.uniform(25,100);c=np.array([256+math.cos(angle)*rad,256+math.sin(angle)*rad*.72])
 for k in range(42):
  a=k*math.tau/42+rr.uniform(-.12,.12);end=c+np.array([math.cos(a)*rr.uniform(58,112),math.sin(a)*rr.uniform(40,94)])
  stroke(c,end,rr.uniform(1.1,2.1),[rr.uniform(.13,.25),rr.uniform(.27,.40),rr.uniform(.12,.20)])
im=bpy.data.images.new('Authored_pine_needle_spray',width=n,height=n,alpha=True);im.pixels.foreach_set(rgba.ravel());im.pack()
mat=bpy.data.materials.new('Pine_needles_alpha_clip');mat.use_nodes=True;mat.surface_render_method='DITHERED';mat.use_backface_culling=False;bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.82
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);mat.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);pine_mats.append(mat)
# Cracked, vertically varied bark. UVs follow height instead of assigning a flat colour band.
for index,base in enumerate([(.32,.24,.17),(.43,.29,.18)]):
 size=256;yy,xx=np.mgrid[0:size,0:size];noise=np.random.default_rng(61+index).random((size,size));crack=np.abs(np.sin(xx*.12+np.sin(yy*.046)*1.4)*np.sin(yy*.07+np.sin(xx*.16)))
 grain=.67+.48*noise;grain[crack<.085]*=.42;pixels=np.ones((size,size,4),dtype=np.float32)
 for channel,c in enumerate(base):pixels[:,:,channel]=c*grain
 bark=bpy.data.images.new('Authored_pine_bark_'+str(index),width=size,height=size);bark.pixels.foreach_set(pixels.ravel());bark.pack()
 material=pine_mats[index];node=material.node_tree.nodes.new('ShaderNodeTexImage');node.image=bark;material.node_tree.links.new(node.outputs['Color'],material.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
def pine(seed,far=False):
 rr=random.Random(seed);p=Plant();h=rr.uniform(12.5,17.2);lean=Vector((rr.uniform(-1.4,1.4),0,rr.uniform(-1,1)))
 def trunk(t):return lean*t*t+Vector((math.sin(t*5)*.17,h*t,math.cos(t*4)*.15))
 for j in range(10):
  a=j/10;b=(j+1)/10;p.tube(trunk(a),trunk(b),.39*(1-a)**.85+.025,.39*(1-b)**.85+.016,0 if j<4 else 1,9)
 for j in range(5):
  ang=j*math.tau/5;p.tube((0,.45,0),(.85*math.cos(ang),.04,.85*math.sin(ang)),.16,.035,0,7)
 # Bark fissures and broken stubs are geometrical details on the near variant.
 if not far:
  for j in range(85):
   t=rr.uniform(.02,.55);a=rr.random()*math.tau;r=.39*(1-t)**.85+.028;c=trunk(t)+Vector((math.cos(a)*r,0,math.sin(a)*r));p.tube(c,c+Vector((.01,rr.uniform(.08,.31),.01)),.014,.005,0,4)
 for j in range(19):
  t=.39+j*.029;ang=j*2.399+seed;reach=rr.uniform(2.4,4.8)*math.sin((t-.24)/.76*math.pi)**.5;start=trunk(t);elbow=start+Vector((reach*.6*math.cos(ang),rr.uniform(-.1,.5),reach*.6*math.sin(ang)));end=start+Vector((reach*math.cos(ang),rr.uniform(.5,1.4),reach*math.sin(ang)))
  p.tube(start,elbow,.115*(1-t)+.025,.047,1,7);p.tube(elbow,end,.047,.01,1,6)
  for k in range(3):
   a=ang+(k-1)*.8;branch=elbow.lerp(end,.35+.3*k);tip=branch+Vector((1.05*math.cos(a),.25+rr.random()*.35,1.05*math.sin(a)));p.tube(branch,tip,.025,.005,1,5)
   for q in range(4):
    c=branch.lerp(tip,.25+.28*q)+Vector((rr.uniform(-.28,.28),rr.uniform(-.15,.18),rr.uniform(-.28,.28)))
    # Three crossed sprays retain dense, feathery crown silhouettes in both variants.
    for plane in range(2 if far else 3):
     ang=plane*math.pi/3+a;u=Vector((math.cos(ang),0,math.sin(ang)))*rr.uniform(.8,1.15);v=Vector((-.2*math.sin(ang),.65,.2*math.cos(ang)))
     p.face([c-u-v,c+u-v,c+u+v,c-u+v],5)
    count=3 if far else 8
    for m in range(count):
     aa=rr.random()*math.tau;d=(math.cos(aa),rr.uniform(-.15,.8),math.sin(aa));p.blade(c,d,rr.uniform(.25,.48)*(1.4 if far else 1),.058 if far else .018,2+m%3)
 return p.finish('Pine_'+str(seed)+('_far' if far else '_near'),pine_mats)
pines=[(pine(s),pine(s,True)) for s in [13,27,49,81]]
def plant(mesh,name,x,z,scale=1,angle=0,lod=None):
 o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);o.location=g.bp(x,0,z);o.scale=(scale,scale,scale);o.rotation_euler.z=angle;o['authored_vegetation']=True
 if lod:o['vegetation_lod']=lod;o['vegetation_distance']=60;o.hide_render=lod=='far'
 return o
points=[];pois=[geo(*n['point']) for n in D['pois'] if n['tags'].get('amenity') in ['shelter','toilets'] or n['tags'].get('historic')=='memorial']
for _ in range(6000):
 x=rng.uniform(-85,72);z=rng.uniform(-182,260);pt=(x,z)
 if not inside(pt,grove) or inside(pt,river) or any(distance(pt,a,b)<w*.5+1.3 for a,b,w in paths) or any(math.dist(pt,p)<4.5 for p in pois) or any(math.dist(pt,p)<4.2 for p in points):continue
 points.append(pt)
 if len(points)>=280:break
for i,(x,z) in enumerate(points):
 near,far=pines[i%len(pines)];sc=rng.uniform(.72,1.20);a=rng.random()*math.tau
 plant(near,'old_pine_'+str(i),x,z,sc,a,'near');plant(far,'distant_pine_'+str(i),x,z,sc,a,'far')
 g.solids.append(dict(name='pine_trunk_'+str(i),kind='cylinder',position=[x,1,z],size=[.85*sc,2,.85*sc],color='#654636',collision=True))
# Small willow leaf sprays / grassy river margins use shared authored geometry.
leafmats=[g.mat('#5c523d'),g.mat('#467249'),g.mat('#638947')]
def willow():
 p=Plant();p.tube((0,0,0),(.4,5,0),.28,.075,0)
 for j in range(14):
  a=j*2.4;end=Vector((3*math.cos(a),5+j%3*.6,3*math.sin(a)));p.tube((.3,3+j%4*.5,0),end,.08,.018,0,6)
  for k in range(8):
   c=end+Vector((rng.uniform(-1,1),rng.uniform(-1.8,.6),rng.uniform(-1,1)))
   for n in range(6):p.blade(c,(rng.uniform(-1,1),rng.uniform(-1,.5),rng.uniform(-1,1)),rng.uniform(.3,.6),.07,1+n%2)
 return p.finish('Willow_leaf_sprays',leafmats)
willowmesh=willow()
for i in range(36):
 a,b=edge[i%(len(edge)-1)],edge[i%(len(edge)-1)+1];t=rng.random();x=a[0]*(1-t)+b[0]*t-4;z=a[1]*(1-t)+b[1]*t
 if not inside((x,z),river):plant(willowmesh,'bank_willow',x,z,rng.uniform(.65,1.05),rng.random()*math.tau)
grass=Plant()
for j in range(16):
 a=rng.random()*math.tau;grass.blade((rng.uniform(-.2,.2),0,rng.uniform(-.2,.2)),(math.cos(a)*.4,1,math.sin(a)*.4),rng.uniform(.23,.62),.025,0 if j%3 else 1)
grassmesh=grass.finish('Understory_grass',[g.mat('#667845'),g.mat('#989861')])
for _ in range(1100):
 x=rng.uniform(-85,70);z=rng.uniform(-180,260)
 if inside((x,z),grove) and not any(distance((x,z),a,b)<w/2+.35 for a,b,w in paths):plant(grassmesh,'grass_tuft',x,z,rng.uniform(.6,1.25),rng.random()*math.tau)
# Fine litter patches avoid rectangular turf seams and keep the grove walkable.
for x,z in points[::3]:
 pts=[(x+math.cos(j*math.tau/12)*rng.uniform(1,2.1),z+math.sin(j*math.tau/12)*rng.uniform(1,2.1)) for j in range(12)]
 g.polygon('pine_litter_patch',pts,.003,.004,'#897151')
for i,(x,z) in enumerate(points):
 pts=[(x+math.cos(j*math.tau/15)*rng.uniform(1.1,3),z+math.sin(j*math.tau/15)*rng.uniform(1.1,3)) for j in range(15)]
 if not any(distance((x,z),a,b)<w/2+2.8 for a,b,w in paths):g.polygon('understory_moss',pts,.008,.004,['#687648','#758052','#80875b'][i%3])
# Benches along the OSM trail. Specific pieces are estimated and kept clear of walking lanes.
for i in [2,5,8,11,15]:
 w=next(w for w in D['ways'] if w['id']=='1306096510');p=w['points'][min(i,len(w['points'])-1)];x,z=geo(*p);x+=3
 for yy,dd in [(.48,.42),(.93,.08)]:g.box('timber_bench',x,yy,z,1.8,.12,dd,'#987048',True)
 for dx in [-.7,.7]:g.box('bench_foot',x+dx,.24,z,.08,.48,.36,'#394b42',True)
# Memorial position is OSM; shape comes from the 2025 press photo.
mem=next(n for n in D['pois'] if n['tags'].get('historic')=='memorial');mx,mz=geo(*mem['point'])
g.box('song_monument_base',mx,.13,mz,2.7,.26,1.4,'#aaa28d',True)
g.box('song_monument_stone',mx,1.35,mz,1.65,2.45,.30,'#b3a38c',True)
g.box('song_monument_plaque',mx+.44,1.62,mz+.162,.27,1.8,.025,'#343e3c')
g.label('엄마야 누나야',mx-.03,1.6,mz+.19,1.2,.20,color='#eee7d5')
g.box('memorial_black_inlay',mx, .72,mz+.17,1.67,.36,.025,'#464a46')
# Mapped toilets: simple, visually subordinate public facilities, dimensions estimated.
for n in D['pois']:
 if n['tags'].get('amenity')=='toilets':
  x,z=geo(*n['point']);g.box('mapped_toilet_walls',x,1.5,z,6,3,4,'#d6c7a9',True);g.box('toilet_roof',x,3.12,z,6.5,.3,4.5,'#526d64')
  for dx in [-1.4,1.4]:g.box('toilet_door',x+dx,1.15,z+2.025,1,2.25,.06,'#4a665f')
# Rest shelters at mapped points, with timber posts and layered traditional roof silhouette.
for n in D['pois']:
 if n['tags'].get('shelter_type')!='gazebo':continue
 x,z=geo(*n['point']);g.box('shelter_platform',x,.12,z,5,.24,4,'#ad9b7e')
 for dx in [-1.9,1.9]:
  for dz in [-1.4,1.4]:g.tube('shelter_pillar',(x+dx,.2,z+dz),(x+dx,2.6,z+dz),.13,'#795136');g.box('shelter_post_collider',x+dx,1,z+dz,.3,2,.3,'#795136',True).hide_render=True
 for i in range(8):
  t=i/8;g.box('shelter_tiled_roof',x,2.6+t*.9,z,6.2-t*3.4,.13,5.2-t*3.8,'#4d5b5a',record=False)
 g.box('shelter_ridge',x,3.55,z,3,.16,.24,'#6e7871',record=False)
# Simple river ripples stay inside the mapped bank.
for i in range(210):
 x=rng.uniform(-210,40);z=rng.uniform(-200,320)
 if inside((x,z),river) and inside((x+4,z),river):g.segment('water_glint',(x,z),(x+rng.uniform(1,4),z+.13),.06,.003,'#749b8d',base=-.026,record=False)
# Background hillside silhouettes match the west-bank wooded slope; height is estimated.
for i in range(5):
 x=-300-i%2*90;z=-270+i*155
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=g.bp(x,-12,z));o=bpy.context.object;o.name='estimated_west_hills';o.scale=(170,130,68+i%3*11);o.data.materials.append(g.mat(['#486d48','#55774c'][i%2]))
 for p in o.data.polygons:p.use_smooth=True
entrance=geo(126.85513,35.01958);south=geo(126.854724,35.0178871)
places=[dict(id='entrance',name='솔밭 입구',description='큰 소나무 아래로 이어지는 흙길을 걸어보세요.',position=list(entrance),arrival=list(entrance),radius=20),dict(id='song-stone',name='엄마야 누나야 노래비',description='지도 위치와 현장 사진을 참고해 만든 노래비입니다.',position=[mx,mz+3.5],arrival=[mx,mz+3.5],radius=8),dict(id='pine-path',name='노송 숲길',description='높이 뻗은 줄기와 퍼지는 가지 사이로 강을 바라보세요.',position=list(geo(126.8548165,35.0185483)),arrival=list(geo(126.8548165,35.0185483)),radius=32),dict(id='riverside',name='강변 솔숲',description='드들강과 왕버들, 물가의 풀밭이 이어지는 곳입니다.',position=list(edge[4]),arrival=list(edge[4]),radius=17),dict(id='south',name='남쪽 쉼터',description='솔밭 끝까지 천천히 둘러보세요.',position=list(south),arrival=list(south),radius=22)]
world=dict(title='나주 산책',subtitle='드들강 솔밭유원지',source='© OpenStreetMap contributors · ODbL 1.0; Esri World Imagery (acquired 2026-09-20, imagery date unknown); Ohmynews 2025-08; field blog 2025-06.',bounds=[-240,260,-240,310],spawn=dict(x=entrance[0],z=entrance[1],yaw=math.pi),solids=g.solids,signs=g.signs,places=places,arrivals={p['id']:dict(x=p['arrival'][0],z=p['arrival'][1],yaw=math.pi) for p in places},sceneLinks=[dict(label='나주수목원으로',target='naju-arboretum'),dict(label='빛가람 안내 지도',target='bitgaram')],lighting=dict(exposure=1.06,ambient=1.6,sun=2.3))
(R/'public/deudeulgang-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.3;sun.rotation_euler=(.48,-.55,-.6);sun.data.angle=.09
scene.world=bpy.data.worlds.new('Riverside daylight');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.70,.83,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
bpy.ops.object.camera_add(location=g.bp(-280,280,410));cam=bpy.context.object;scene.camera=cam;cam.rotation_euler=(Vector(g.bp(0,0,35))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=38;cam.data.clip_end=3000
scene.render.engine='BLENDER_EEVEE_NEXT';scene.render.resolution_x=1440;scene.render.resolution_y=960;scene.render.resolution_percentage=100;scene.eevee.taa_render_samples=32;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.6
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
out=R/'public/models/deudeulgang.glb';bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False)
# Blender 4.5 dithering exports as BLEND; these binary-alpha needles use MASK so
# depth writes and the existing vegetation instancing work correctly in glTF viewers.
blob=out.read_bytes();length=struct.unpack_from('<I',blob,12)[0];doc=json.loads(blob[20:20+length]);tail=blob[20+length:]
for material in doc['materials']:
 if material.get('name')=='Pine_needles_alpha_clip':material['alphaMode']='MASK';material['alphaCutoff']=.48;material['doubleSided']=True
encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);out.write_bytes(struct.pack('<III',0x46546c67,2,20+len(encoded)+len(tail))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+tail)
with gzip.open(str(out)+'.gz','wb',compresslevel=9) as f:f.write(out.read_bytes())
scene.render.filepath=str(O/'overview-v2.png');bpy.ops.render.render(write_still=True)
cam.location=g.bp(entrance[0],1.72,entrance[1]);cam.rotation_euler=(Vector(g.bp(-5,6,25))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=24
scene.render.filepath=str(O/'pine-walk-v2.png');bpy.ops.render.render(write_still=True)
(S/'metrics.json').write_text(json.dumps(dict(pines=len(points),willow_placements=36,shared_pine_variants=4,near_distance_m=60,glb_bytes=out.stat().st_size,gzip_bytes=Path(str(out)+'.gz').stat().st_size,source_center=[126.85475,35.0185],grove_polygon=grove,river_polygon=river),indent=2),encoding='utf-8')
print('DEUDEULGANG COMPLETE',len(points),'pines',out.stat().st_size,flush=True)
