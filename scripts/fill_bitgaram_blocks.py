"""Add reviewed satellite-derived blocks to the preserved V46 Blender scene."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
# Reuse the same coordinate conversion, spatial exclusion and batching implementation.
source=(R/'scripts/finish_bitgaram_district.py').read_text(encoding='utf-8').split('# Mapped ground categories')[0]
source=source.replace("bitgaram-district-complete-v5.blend'","bitgaram-district-blocks-v6.blend'").replace("bitgaram-drone-detail.blend'","bitgaram-district-complete-v5.blend'")
exec(compile(source,str(R/'scripts/finish_bitgaram_district.py'),'exec'))
previous=json.loads((S/'district-completion-metrics.json').read_text(encoding='utf-8'))
previousids={str(b['id']) for b in previous['buildings'] if b['estimated_footprint']}
for i,c in enumerate(json.loads((S/'district-roof-candidates.json').read_text())['candidates']):
 if str(900000+i) not in previousids:continue
 x,z=c['center'];ww,dd=c['size'];a,b,_=min(roads,key=lambda r:dist((x,z),r[0],r[1]));angle=math.atan2(b[1]-a[1],b[0]-a[0]);co,si=math.cos(angle),math.sin(angle)
 register_block([(x+dx*co-dz*si,z+dx*si+dz*co) for dx,dz in [(-ww/2,-dd/2),(ww/2,-dd/2),(ww/2,dd/2),(-ww/2,dd/2)]])
added=[];rejected=0
for i,c in enumerate(json.loads((S/'district-block-infill.json').read_text(encoding='utf-8'))['candidates']):
 kind=c['kind'];manual='polygon' in c
 if manual:p=c['polygon'];x,z=center(p);h=c['height']
 else:
  x,z=c['center'];ww,dd=c['size'];a,b,_=min(roads,key=lambda r:dist((x,z),r[0],r[1]));angle=math.atan2(b[1]-a[1],b[0]-a[0]);co,si=math.cos(angle),math.sin(angle)
  p=[(x+dx*co-dz*si,z+dx*si+dz*co) for dx,dz in [(-ww/2,-dd/2),(ww/2,-dd/2),(ww/2,dd/2),(-ww/2,dd/2)]]
  h=[14,18,22][i%3] if kind=='satellite_shop' else [7,9.5,11][i%3]
 samples=[(x,z)]+p+[((a[0]+b[0])/2,(a[1]+b[1])/2) for a,b in zip(p,p[1:]+p[:1])]
 if not inframe(x,z) or any(not free(*pt,2) or roadnear(*pt,1) for pt in samples):rejected+=1;continue
 ident=950000+i;building(p,h,kind,str(ident),True);register_block(p)
 # Individual apartment bays, lift cores and entrances are schematic detailing.
 if manual:
  a,b=p[0],p[1];ll=math.dist(a,b);ux,uz=(b[0]-a[0])/ll,(b[1]-a[1])/ll
  for d in range(4,int(ll)-2,6):
   for side in [0,2]:
    aa,bb=p[side],p[(side+1)%4];length=math.dist(aa,bb)
    if length<20:continue
    xx,zz=aa[0]+(bb[0]-aa[0])*d/length,aa[1]+(bb[1]-aa[1])*d/length
    g.box('apartment_bay',xx,h/2,zz,.65,h,.65,'#f0ecdf',record=False)
  g.box('lift_head',x,h+1.6,z,6,3.2,5,'#d2d7cc',record=False)
 else:
  a,b=p[0],p[1]
  g.segment('shopfront' if kind=='satellite_shop' else 'house_entry',a,b,.35,2,'#57767e',base=.4,record=False)
  # Neutral courtyard apron follows each roof instead of large empty monochrome plots.
  apron=[(x+(px-x)*1.14,z+(pz-z)*1.14) for px,pz in p]
  if all(not roadnear(*pt,0) for pt in apron):g.polygon('parcel_apron',apron,.095,.012,'#babbb0')
 added.append(dict(id=str(ident),kind=kind,height=h,polygon=p,source=c['source'],estimated_footprint=True,zone=c.get('zone')))
g.finish();scene=bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=str(target))
from blender_static_batch import batch
batch(scene)
out=R/'public/models/bitgaram-overview.glb';bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
metrics=dict(reference='district-block-infill.json',added=len(added),apartments=sum(b['kind']=='satellite_apartment' for b in added),shops=sum(b['kind']=='satellite_shop' for b in added),houses=sum(b['kind'] in ['satellite_house','satellite_parcel_house'] for b in added),rejected=rejected,buildings=added)
(S/'district-block-infill-metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.eevee.taa_render_samples=32
for name,position,aim,scale in [('district-blocks',(1400,2450,2600),(100,0,0),4100),('district-blocks-west',(-800,1250,1550),(-450,0,350),2100),('district-blocks-north',(-900,1500,-1800),(-350,0,-700),2300)]:
 scene.camera.location=g.bp(*position);scene.camera.rotation_euler=(Vector(g.bp(*aim))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=scale
 scene.render.filepath=str(O/(name+'-v6.png'));bpy.ops.render.render(write_still=True)
print('BLOCK INFILL', {k:v for k,v in metrics.items() if k!='buildings'},flush=True)
