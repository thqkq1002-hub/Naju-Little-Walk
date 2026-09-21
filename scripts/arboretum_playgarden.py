"""Photo-informed play equipment and flowering gardens; layout is explicitly estimated."""
import bpy,sys,math,json,random,gzip
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
R=Path(__file__).resolve().parents[1];O=R/'outputs/arboretum'
target=O/'naju-arboretum-playgarden-v10.blend'
if target.exists():raise RuntimeError('Preserving existing Blender revision')
bpy.ops.wm.open_mainfile(filepath=str(O/'naju-arboretum-groves-v7.blend'))
scene=bpy.context.scene;g=MuseumGeometry(scene,(0,0),0);rng=random.Random(920)
world=json.loads((R/'public/naju-arboretum-world.json').read_text(encoding='utf-8'))
g.solids=list(world['solids']);g.signs=list(world['signs'])
angle=math.atan2(.2,.98)
def local(s,t):return (-475+.98*s-.2*t,-50+.2*s+.98*t)
def inv(x,z):return (((x+475)*.98+(z+50)*.2)/1.0004,(-(x+475)*.2+(z+50)*.98)/1.0004)
def pt(s,y,t):
 x,z=local(s,t);return (x,y,z)
def box(n,s,y,t,w,h,d,c,collision=False):
 x,z=local(s,t);return g.box(n,x,y,z,w,h,d,c,collision,rotation=angle,record=collision)
def tube(n,a,b,r,c):return g.tube(n,pt(*a),pt(*b),r,c,n=8)
def path(n,points,width=2.4,c='#c2b69c'):
 for a,b in zip(points,points[1:]):g.segment(n,local(*a),local(*b),width,.035,c,base=.12,record=False)
def patch(n,points,c):return g.polygon(n,[local(*p) for p in points],.042 if n=='flower_bed_soil' else .014,.012,c)
def sign(text,s,t):
 box('garden_sign',s,1.28,t,2.8,.8,.13,'#315242',True)
 for d in [-1.05,1.05]:tube('garden_sign_post',(s+d,0,t),(s+d,1.75,t),.075,'#766148')
 x,z=local(s,t+.08);g.label(text,x,1.28,z,2.6,.3,rotation=-angle,color='#f3e8cc')
def bench(s,t):
 for d in [-.2,0,.2]:box('play_bench_seat',s,.48,t+d,2.1,.07,.17,'#88643f')
 for h in [.74,.96]:box('play_bench_back',s,h,t-.30,2.1,.16,.06,'#88643f')
 for d in [-.8,.8]:box('play_bench_support',s+d,.24,t,.08,.48,.48,'#3b4640',True)

# Open the indicated grove for the play clearing, preserving the avenue tree rows.
# Second region is interpreted from the user's greenhouse-side image: botanical flower beds.
removed=0
for o in list(bpy.data.objects):
 if o.name.startswith(('estimated_broadleaf','satellite_grove','estimated_juniper')):
  s,t=inv(o.location.x,-o.location.y)
  if ((s-233)/22)**2+((t+62)/22)**2<1 or (142<s<224 and 25<t<100):
   bpy.data.objects.remove(o,do_unlink=True);removed+=1
patch('play_clearing',[(213,-45),(214,-70),(225,-81),(246,-81),(253,-68),(251,-46),(236,-40)],'#a99470')
path('play_access',[(220,-9),(220,-28),(217,-43),(220,-52)],2.8)
path('play_clearing_walk',[(220,-52),(220,-73),(245,-73),(248,-52),(220,-52)],2.0)
sign('유아숲 · 어린이 놀이터',224,-32)
for p in [(217,-68),(247,-70),(246,-46)]:bench(*p)

# The 2021 field photograph shows two timber decks, green open slide, cream curved tube,
# rope-climbing panel and a short stair flight. Dimensions and placement are estimates.
S,T=234,-60
wood='#684b34';rail='#947456';cream='#d4cfb6';green='#78a944';rope='#47717b'
for ds,dt,h in [(0,0,1.55),(0,-3.1,2.2)]:
 s,t=S+ds,T+dt
 box('play_platform',s,h,t,2.2,.17,2.3,wood,True)
 for x in [-1,1]:
  for z in [-1,1]:
   tube('play_timber_post',(s+x,0,t+z),(s+x,h+1.3,t+z),.105,wood)
 for side in [-1,1]:
  for j in range(8):box('play_guard_baluster',s+side*1.03,h+.48,t-.95+j*.27,.07,.88,.07,rail)
  box('play_guard_cap',s+side*1.03,h+.95,t,.12,.1,2.3,rail)
 # Low faceted canopy evokes the asymmetric open roof in the photograph.
 if dt<0:
  for side in [-1,1]:
   v=[pt(s-1.25,h+1.65,t+side*1.35),pt(s+1.25,h+1.65,t+side*1.35),pt(s+1.25,h+2.05,t),pt(s-1.25,h+2.05,t)]
   g.mesh('play_canopy',v,[(0,1,2,3)],'#8c7860')
 for j in range(11):box('play_deck_board',s-1+j*.2,h+.095,t,.18,.025,2.3,'#a1825d')
# Short connecting bridge.
for j in range(8):box('play_bridge_plank',S,1.86,T-1.25-j*.1,1.5,.10,.085,rail)
for side in [-1,1]:tube('play_bridge_rail',(S+side*.85,2.65,T-1.1),(S+side*.85,2.95,T-2),.055,rail)
# Stair flight behind tall deck.
for j in range(9):
 box('play_stair',S,.12+j*.245,T-6.7+j*.29,1.1,.18,.32,wood,True)
for side in [-1,1]:tube('play_stair_handrail',(S+side*.68,.8,T-6.8),(S+side*.68,3.0,T-4.15),.055,rail)
# Sloping green chute with raised sides, including a flattened runout.
slide=[(T+1.1,1.57),(T+1.6,1.55),(T+4.65,.20),(T+5.5,.15)]
vs=[]
for t,h in slide:
 for x,y in [(-.64,h+.24),(-.52,h),(.52,h),(.64,h+.24)]:vs.append(pt(S+x,y,t))
faces=[(j*4+k,j*4+k+1,(j+1)*4+k+1,(j+1)*4+k) for j in range(3) for k in range(3)]
g.mesh('play_green_slide',vs,faces,green,smooth=True)
g.collider('play_slide_collision',[local(S-.7,T+1),local(S+.7,T+1),local(S+.7,T+5.6),local(S-.7,T+5.6)],0,1.6)
# Hollow cream slide follows a descending curve; actual rings, not a solid sausage.
centers=[]
for j in range(35):
 a=math.pi*.1+j/34*math.pi*1.35
 centers.append(Vector(pt(S-1.8-1.15*math.sin(a),2.1-j/34*1.5,T-2.8+1.15*math.cos(a))))
verts=[]
for j,c in enumerate(centers):
 tangent=(centers[min(j+1,34)]-centers[max(j-1,0)]).normalized();u=tangent.cross(Vector((0,1,0))).normalized();v=tangent.cross(u).normalized()
 for radius in [.58,.53]:
  for k in range(16):verts.append(tuple(c+radius*(math.cos(k*math.tau/16)*u+math.sin(k*math.tau/16)*v)))
faces=[]
for j in range(34):
 for h in [0,16]:
  for k in range(16):faces.append((j*32+h+k,j*32+h+(k+1)%16,(j+1)*32+h+(k+1)%16,(j+1)*32+h+k))
for end in [0,34]:
 for k in range(16):faces.append((end*32+k,end*32+(k+1)%16,end*32+16+(k+1)%16,end*32+16+k))
g.mesh('play_cream_tube_slide',verts,faces,cream,smooth=True)
box('play_tube_support',S-2.6,.36,T-2,1.4,.7,1.3,wood,True)
# Rope mesh sloping toward the first deck.
for k in range(6):
 x=S-1.6+k*.32;tube('play_rope_vertical',(x,.1,T+2.4),(x,1.55,T+.8),.021,rope)
for j in range(7):
 f=j/6;tube('play_rope_horizontal',(S-1.6,.1+1.45*f,T+2.4-1.6*f),(S,.1+1.45*f,T+2.4-1.6*f),.021,rope)
for x in [S-1.8,S+.1]:tube('play_net_post',(x,0,T+2.6),(x,2.2,T+2.6),.09,wood)
box('play_climbing_wall',S+1.16,.85,T, .14,1.65,1.6,wood,True)
for j in range(8):
 t=T-.6+(j%3)*.5;y=.35+(j//3)*.4
 x,z=local(S+1.28,t);bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.11,location=g.bp(x,y,z));bpy.context.object.name='play_climb_hold';bpy.context.object.data.materials.append(g.mat(['#b9864c','#b66546','#9f9760'][j%3]))
# Timber gathering platform observed in the adjacent field photograph.
box('play_rest_deck',243,.23,-76,5,.4,2.8,wood,True)
for j in range(18):box('play_rest_boards',240.6+j*.28,.45,-76,.25,.04,2.8,rail)
for s in [240.6,245.4]:tube('play_rest_post',(s,0,-77.2),(s,1.2,-77.2),.09,wood)
tube('play_rest_back',(240.6,1.1,-77.2),(245.4,1.1,-77.2),.07,rail)

# Photo-informed rose/flower garden: hedge compartments and cone-shaped supports.
# Perennial forms and colours are interpretive, not a claimed botanical inventory.
patch('flower_garden_ground',[(145,28),(218,28),(222,96),(145,96)],'#879765')
path('flower_garden_axis',[(181,10),(181,100)],3.0)
for t in [31,52,74,96]:path('flower_garden_cross',[(144,t),(221,t)],2.3)
path('flower_garden_outer',[(145,31),(145,96),(220,96),(220,31),(145,31)],2.3)
for t in [45,88]:bench(184,t)
sign('꽃정원 · 약용식물 구역',187,21)

# Build all plant detail into a few material meshes to control object and draw-call counts.
buffers={}
def face(color,points):
 v,f=buffers.setdefault(color,([],[]));n=len(v);v.extend(points);f.append(tuple(range(n,n+len(points))))
def blossom(s,t,h,r,color,rose=False):
 x,z=local(s,t)
 face('#466331',[(x-.012,.05,z),(x+.012,.05,z),(x+.01,h,z),(x-.01,h,z)])
 for k in range(3):
  a=k*2.4;dy=h*(.25+k*.15);dx=.17*math.cos(a);dz=.17*math.sin(a)
  face('#577638',[(x,dy,z),(x+dx*.5-dz*.25,dy+.10,z+dz*.5+dx*.25),(x+dx,dy+.14,z+dz),(x+dx*.5+dz*.25,dy+.03,z+dz*.5-dx*.25)])
 for ring in range(2 if rose else 1):
  for j in range(7 if rose else 5):
   a=j*math.tau/(7 if rose else 5)+ring*.4;rr=r*(1-ring*.4);c=math.cos(a);q=math.sin(a)
   face(color,[(x,h+ring*.035,z),(x+rr*.62*c-rr*.4*q,h+.035,z+rr*.62*q+rr*.4*c),(x+rr*c,h+.09,z+rr*q),(x+rr*.62*c+rr*.4*q,h+.035,z+rr*.62*q-rr*.4*c)])
 face('#d5ac49',[(x-.025,h+.10,z-.025),(x+.025,h+.10,z-.025),(x+.025,h+.10,z+.025),(x-.025,h+.10,z+.025)])
for col,(a,b) in enumerate([(148,178),(184,217)]):
 for row,(c,d) in enumerate([(34,49),(55,71),(77,93)]):
  # Gravel beds, narrow brown soil margins, clipped but slightly irregular hedges.
  patch('flower_bed_soil',[(a,c),(b,c),(b,d),(a,d)],'#675b3b')
  for aa,bb in [((a,c),(b,c)),((a,d),(b,d)),((a,c),(a,d)),((b,c),(b,d))]:
   g.segment('flower_hedge',local(*aa),local(*bb),.65,.54,'#4b7138',base=.04,record=False)
  # A narrow internal gravel aisle allows a close look at the flower clumps.
  path('flower_bed_aisle',[((a+b)/2,c),((a+b)/2,d)],1.4,'#c4bfb0')
  for j in range(580):
   s=rng.uniform(a+1,b-1);t=rng.uniform(c+1,d-1)
   if abs(s-(a+b)/2)<1.0:continue
   palette=[['#c74473','#e0a1b4','#eee5d3'],['#bca5d1','#9477b4','#eee7d5'],['#d8ba55','#e4d694','#e6ac72']][row]
   blossom(s,t,rng.uniform(.4,.85),rng.uniform(.12,.21),rng.choice(palette),row==0)
   for q in range(4):
    a1=rng.random()*math.tau;rr=rng.uniform(.09,.25);hh=rng.uniform(.16,.42);x,z=local(s,t)
    dx,dz=rr*math.cos(a1),rr*math.sin(a1)
    face(rng.choice(['#49682f','#587a39','#64833f']),[(x,.06,z),(x+dx*.5-dz*.35,hh,z+dz*.5+dx*.35),(x+dx,hh+.06,z+dz),(x+dx*.5+dz*.35,hh-.03,z+dz*.5-dx*.35)])
  # Short botanical interpretation label; no invented cultivar names.
  box('flower_label',a+1.6,.7,c-1.1,1.8,.4,.08,'#486247')
  x,z=local(a+1.6,c-1);g.label(['장미 · 꽃 관목','초화 식재','향기 식물'][row],x,.7,z,1.65,.20,rotation=-angle)
  if row==0:
   s=(a+b)/2+5;t=(c+d)/2
   for k in range(10):
    ang=k*math.tau/10
    tube('rose_conical_trellis',(s+1.2*math.cos(ang),0,t+1.2*math.sin(ang)),(s+.15*math.cos(ang),2.65,t+.15*math.sin(ang)),.019,'#84968a')
   for h in [.4,.8,1.2,1.6,2,2.4]:
    rad=1.2-h/2.65*1.05
    for k in range(16):
     aa=k*math.tau/16;bb=(k+1)*math.tau/16
     tube('rose_trellis_ring',(s+rad*math.cos(aa),h,t+rad*math.sin(aa)),(s+rad*math.cos(bb),h,t+rad*math.sin(bb)),.015,'#84968a')
   for k in range(95):
    h=rng.uniform(.4,2.35);a0=rng.random()*math.tau;rad=1.1-h*.35
    blossom(s+rad*math.cos(a0),t+rad*math.sin(a0),h,.12,rng.choice(['#c74473','#e0a1b4','#eee5d3']),True)
# Break up the straight hedge surfaces with small overlapping leafy sprays.
for col,(a,b) in enumerate([(148,178),(184,217)]):
 for c,d in [(34,49),(55,71),(77,93)]:
  for j in range(650):
   if j%2:s=rng.uniform(a,b);t=rng.choice([c,d])+rng.uniform(-.32,.32)
   else:s=rng.choice([a,b])+rng.uniform(-.32,.32);t=rng.uniform(c,d)
   x,z=local(s,t);h=rng.uniform(.43,.67);rr=rng.uniform(.08,.17)
   face(rng.choice(['#49682f','#587a39','#64833f']),[(x-rr,h,z),(x,h+.08,z-rr),(x+rr,h,z),(x,h+.03,z+rr)])
for color,(v,f) in buffers.items():g.mesh('flower_detail_'+color[1:],v,f,color,smooth=True)
# Reuse the authored grain/normal textures on the new timber elements.
timber=bpy.data.materials.get('Authored_timber')
if timber:
 for o in scene.objects:
  if o.type=='MESH' and o.name.startswith(('play_platform','play_timber','play_guard','play_deck','play_bridge','play_stair','play_bench','play_rest','play_climbing')):
   o.data.materials.clear();o.data.materials.append(timber)

# Include solid equipment in walking collisions; decorative beds remain approachable.
world['solids']=g.solids;world['signs']=g.signs
for ident,title,s,t,arr,desc in [
 ('playground','어린이 숲놀이터',234,-60,(221,-52),'목재 놀이대와 미끄럼틀을 둘러보세요. 방문 사진 참고 · 위치와 치수 일부 추정.'),
 ('flowers','꽃정원',181,62,(181,36),'생울타리와 꽃 사이로 걸어보세요. 사진 참고 · 품종과 세부 배치 추정.')]:
 x,z=local(s,t);ax,az=local(*arr)
 world['places'].append(dict(id=ident,name=title,description=desc,position=[x,z],radius=38,arrival=[ax,az]))
 world.setdefault('arrivals',{})[ident]=dict(x=ax,z=az,yaw=math.atan2(ax-x,az-z))
world['limitations'].append('Playground forms reference a 2021 field photo; placement and dimensions estimated. Flower garden layout and botanical composition are interpretive; not a verified current inventory.')
(R/'public/naju-arboretum-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
scene.eevee.taa_render_samples=32
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
out=R/'public/models/naju-arboretum.glb';bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
with gzip.open(str(out)+'.gz','wb',compresslevel=9) as f:f.write(out.read_bytes())
scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.render.resolution_percentage=100
for name,loc,aim,lens in [('playground',(S+13,6,T+18),(S,1.3,T-1),36),('flowers',(201,8,106),(180,.7,57),32)]:
 cam=scene.camera;cam.location=g.bp(*pt(*loc));cam.rotation_euler=(Vector(g.bp(*pt(*aim)))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
 scene.render.filepath=str(O/(name+'-v10.png'));bpy.ops.render.render(write_still=True)
print('PLAYGARDEN COMPLETE',out.stat().st_size,'bytes; cleared',removed,'estimated trees')
