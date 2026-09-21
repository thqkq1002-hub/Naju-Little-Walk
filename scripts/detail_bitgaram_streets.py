"""Author close-up district detail in Blender; preserve V47 editable geometry."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
source=(R/'scripts/finish_bitgaram_district.py').read_text(encoding='utf-8').split('# Mapped ground categories')[0]
source=source.replace("bitgaram-district-complete-v5.blend'","bitgaram-street-detail-v7.blend'").replace("bitgaram-drone-detail.blend'","bitgaram-district-blocks-v6.blend'")
exec(compile(source,str(R/'scripts/finish_bitgaram_district.py'),'exec'))
v46=json.loads((S/'district-completion-metrics.json').read_text(encoding='utf-8'));v47=json.loads((S/'district-block-infill-metrics.json').read_text(encoding='utf-8'))
added46={str(b['id']):b for b in v46['buildings']};detailed=[]
for i,c in enumerate(json.loads((S/'district-roof-candidates.json').read_text())['candidates']):
 if str(900000+i) not in added46:continue
 x,z=c['center'];ww,dd=c['size'];a,b,_=min(roads,key=lambda r:dist((x,z),r[0],r[1]));an=math.atan2(b[1]-a[1],b[0]-a[0]);co,si=math.cos(an),math.sin(an)
 p=[(x+dx*co-dz*si,z+dx*si+dz*co) for dx,dz in [(-ww/2,-dd/2),(ww/2,-dd/2),(ww/2,dd/2),(-ww/2,dd/2)]];register_block(p)
for b in v47['buildings']:register_block(b['polygon'])
# Detail only known model envelopes; custom landmark meshes have their own authored facades.
for w in ways:
 if not w['tags'].get('building'):continue
 p=w['points'][:-1] if w['points'][0]==w['points'][-1] else w['points'];x,z=center(p)
 if not (-1600<x<1650 and -1500<z<1400):continue
 obj=bpy.data.objects.get('building_'+w['id']);m=added46.get(w['id'])
 if obj:h=max((obj.matrix_world@v.co).z for v in obj.data.vertices)
 elif m:h=m['height']
 else:continue
 if 5<h<110:detailed.append(dict(id=w['id'],polygon=p,height=h,kind=w['tags']['building']))
detailed+=v47['buildings']
detail_counts=dict(facades=0,window_panels=0,roof_units=0,entrances=0,courtyard_gardens=0,benches=0,parked_cars=0,crosswalks=0,streetlights=0,parking_lots=0)
placements=[]

def groundfree(p,margin=1):return all(free(*pt,margin) and not roadnear(*pt,1) for pt in p+[center(p)])
def rectangle(x,z,w,d,angle=0):
 co,si=math.cos(angle),math.sin(angle)
 return [(x+xx*co-zz*si,z+xx*si+zz*co) for xx,zz in [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)]]
def bench(x,z,angle):
 g.box('timber_seat',x,.55,z,1.8,.16,.55,'#997c59',rotation=angle,record=False)
 for dx in [-.65,.65]:g.box('bench_leg',x+math.cos(angle)*dx,.27,z+math.sin(angle)*dx,.12,.48,.4,'#555e5e',rotation=angle,record=False)
 detail_counts['benches']+=1

for idx,b in enumerate(detailed):
 p=b['polygon'];h=b['height'];cx,cz=center(p);apt='apartment' in b['kind'];tall=h>20
 area=sum(a[0]*bb[1]-bb[0]*a[1] for a,bb in zip(p,p[1:]+p[:1]));edges=[]
 for a,bb in zip(p,p[1:]+p[:1]):
  ll=math.dist(a,bb)
  if ll<6:continue
  ux,uz=(bb[0]-a[0])/ll,(bb[1]-a[1])/ll;nx,nz=(uz,-ux) if area>0 else (-uz,ux)
  edges.append((a,bb,ll,ux,uz,nx,nz))
  if tall and ll>17:
   for y in range(4,int(h)-1,4):
    for j,d in enumerate(range(3,int(ll)-2,5)):
     x,z=a[0]+ux*d+nx*.26,a[1]+uz*d+nz*.26;ww=2.15 if apt else 2.8
     # Flat inset panes and occasional pale sill, rather than costly box windows.
     vs=[(x-ux*ww/2,y,z-uz*ww/2),(x+ux*ww/2,y,z+uz*ww/2),(x+ux*ww/2,y+1.6,z+uz*ww/2),(x-ux*ww/2,y+1.6,z-uz*ww/2)]
     g.mesh('facade_window',vs,[(0,1,2,3)],['#63828d','#96aeb2','#758e98'][(j+y//4+idx)%3]);detail_counts['window_panels']+=1
     if apt and y%8==4:g.segment('window_sill',(x-ux*1.25,z-uz*1.25),(x+ux*1.25,z+uz*1.25),.5,.12,'#dce0d7',base=y-.13,record=False)
 if not edges:continue
 detail_counts['facades']+=1
 # Street-facing canopy selected from the nearest road, not arbitrary business signage.
 a,bb,ll,ux,uz,nx,nz=min(edges,key=lambda edge:min(dist(center([edge[0],edge[1]]),r[0],r[1]) for r in roads))
 x,z=center([a,bb]);angle=math.atan2(uz,ux);x+=nx*1.5;z+=nz*1.5
 if free(x,z,.3) and not roadnear(x,z,0):
  g.box('entrance_canopy',x,3.1,z,min(5,ll*.55),.22,2.1,'#64868a' if tall else '#a1a696',rotation=angle,record=False)
  g.box('entry_paving',x,.145,z,min(5,ll*.55),.08,3.1,'#c5c5b6',rotation=angle,record=False);detail_counts['entrances']+=1
 if h>12 and inside((cx,cz),p) and min(dist((cx,cz),a,bb) for a,bb in zip(p,p[1:]+p[:1]))>5:
  g.box('roof_service_plinth',cx,h+.18,cz,6,.36,4,'#a6aeaa',record=False)
  for dx in [-1.6,1.6]:
   g.box('roof_service_unit',cx+dx,h+.9,cz,2.1,1.1,2.3,'#c1c8c4',record=False)
   for dz in [-.6,0,.6]:g.box('vent_grille',cx+dx,h+1.47,cz+dz,1.8,.035,.13,'#697977',record=False)
  detail_counts['roof_units']+=2
 # Small planted courtyard on the long apartment frontage, only in open space.
 if apt and ll>25:
  x,z=center([a,bb]);x+=nx*11;z+=nz*11;pocket=rectangle(x,z,min(22,ll*.6),8,angle)
  if groundfree(pocket,2):
   g.polygon('courtyard_walk',pocket,.13,.04,'#c9c6b2')
   garden=rectangle(x,z,min(18,ll*.5),4.5,angle);g.polygon('courtyard_planting',garden,.18,.16,'#8fa173')
   for offset in [-5,0,5]:
    xx,zz=x+ux*offset,z+uz*offset
    g.box('low_shrub_bed',xx,.63,zz,2.2,.55,2.1,'#72875a',rotation=angle,record=False)
   bench(x+nx*3.2,z+nz*3.2,angle);bench(x-nx*3.2,z-nz*3.2,angle)
   detail_counts['courtyard_gardens']+=1
   placements.append(dict(type='courtyard',polygon=pocket))

# Parked vehicles and stall end-markers inside mapped parking polygons only.
for w in ways:
 p=w['points'];cx,cz=center(p)
 if w['tags'].get('amenity')!='parking' or p[0]!=p[-1] or not inframe(cx,cz):continue
 x0,x1,z0,z1=bounds(p);n=0
 for x in range(math.ceil(x0+4),int(x1-4),6):
  for z in range(math.ceil(z0+5),int(z1-5),13):
   if n>=22:break
   poly=rectangle(x,z,2.1,4.5)
   if not all(inside(q,p) for q in poly) or not groundfree(poly,1):continue
   if (x+z)%5==0:continue
   col=['#e3e4da','#788b94','#b1b6b2','#657174','#b69b89'][(x+z)%5]
   g.box('parked_car_body',x,.65,z,1.85,.8,4.2,col,record=False)
   g.box('parked_car_glass',x,1.15,z,1.6,.6,2.25,'#587079',record=False)
   g.box('parked_car_roof',x,1.47,z,1.5,.08,1.6,col,record=False)
   for side in [-1,1]:g.box('car_tire_shadow',x+side*.89,.3,z,.12,.35,3.1,'#495653',record=False)
   g.box('parking_stop',x,.2,z+2.6,1.4,.22,.16,'#d9d7b9',record=False)
   n+=1;detail_counts['parked_cars']+=1;placements.append(dict(type='car',polygon=poly,source_id=w['id']))
 if n:detail_counts['parking_lots']+=1

# Junction-derived crosswalks: measured road positions, schematic stripe layout.
nodes={}
for a,b,ww in roads:
 for pt in [a,b]:
  key=tuple(round(c,1) for c in pt);nodes[key]=nodes.get(key,0)+1
walkkeys=set();lightkeys=set()
for a,b,ww in roads:
 ll=math.dist(a,b)
 if ww<8 or ll<45:continue
 ux,uz=(b[0]-a[0])/ll,(b[1]-a[1])/ll;angle=math.atan2(uz,ux)
 for start,sign in [(a,1),(b,-1)]:
  if nodes.get(tuple(round(c,1) for c in start),0)<3:continue
  x,z=start[0]+ux*sign*(ww/2+10),start[1]+uz*sign*(ww/2+10);key=(round(x/15),round(z/15))
  if key in walkkeys or not inframe(x,z) or not free(x,z,0):continue
  walkkeys.add(key)
  for off in range(-int(ww/2)+2,int(ww/2)-1,2):g.box('zebra_crossing',x-uz*off,.117,z+ux*off,4,.013,.75,'#dedfcf',rotation=angle,record=False)
  detail_counts['crosswalks']+=1
 for d in range(30,int(ll)-10,95):
  for side in [-1,1]:
   x,z=a[0]+ux*d-uz*(ww/2+2.8)*side,a[1]+uz*d+ux*(ww/2+2.8)*side;key=(round(x/12),round(z/12))
   if key in lightkeys or not inframe(x,z) or not free(x,z,2) or roadnear(x,z,.5):continue
   lightkeys.add(key)
   g.box('streetlight_column',x,3.6,z,.2,7.2,.2,'#657879',record=False)
   g.box('streetlight_head',x+uz*side*.5,7.2,z-ux*side*.5,1.4,.16,.45,'#d1d7c3',rotation=angle+math.pi/2,record=False)
   detail_counts['streetlights']+=1

# Slightly darker asphalt improves legibility without changing the ground footprint.
for name in ['Museum_8e9a97','Museum_939f99']:
 for mat in bpy.data.materials:
  if mat.name==name or mat.name.startswith(name+'.'):
   rgb=[.435,.49,.485];linear=[((v+.055)/1.055)**2.4 for v in rgb];mat.diffuse_color=(*linear,1)
   if mat.use_nodes:mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*linear,1)
g.finish();scene=bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=str(target))
from blender_static_batch import batch
batch(scene)
out=R/'public/models/bitgaram-overview.glb';bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
(S/'district-street-detail-metrics.json').write_text(json.dumps(dict(counts=detail_counts,placements=placements,detail_basis='Mapped building/parking/road envelopes; all facade fixtures, vehicles, plants and street furniture are schematic estimates.'),ensure_ascii=False,indent=2),encoding='utf-8')
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.eevee.taa_render_samples=32
for name,position,aim,scale in [('district-detail',(1400,2450,2600),(100,0,0),4100),('district-detail-close',(-650,650,450),(-420,0,190),1050)]:
 scene.camera.location=g.bp(*position);scene.camera.rotation_euler=(Vector(g.bp(*aim))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=scale
 scene.render.filepath=str(O/(name+'-v7.png'));bpy.ops.render.render(write_still=True)
print('STREET DETAIL',detail_counts,flush=True)
