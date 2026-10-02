"""Blender palette pass with separate wall/roof assignments and court detailing."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
source=(R/'scripts/finish_bitgaram_district.py').read_text(encoding='utf-8').split('# Mapped ground categories')[0]
source=source.replace("bitgaram-district-complete-v5.blend'","bitgaram-color-detail-v9.blend'").replace("bitgaram-drone-detail.blend'","bitgaram-street-detail-v7.blend'")
exec(compile(source,str(R/'scripts/finish_bitgaram_district.py'),'exec'))
palette=json.loads((S/'district-palette.json').read_text())
stats=dict(recolored_materials=0,building_meshes=0,building_shells=0,roof_faces=0,sports_courts=0,paving_inlays=0)
def linear(hex):
 rgb=[int(hex.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
 return [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
def setcolor(m,col,rough=.85,metal=0):
 c=(*linear(col),1);m.diffuse_color=c
 if m.use_nodes:
  p=m.node_tree.nodes.get('Principled BSDF')
  if p:p.inputs['Base Color'].default_value=c;p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
mapping={
 '8e9a97':palette['asphalt'],'939f99':palette['asphalt'],'9ba5a0':'#7e8787',
 'c8c6b4':palette['pavement'],'d3d0bc':'#c6baa7','d9ccad':'#c3ae89','babbb0':'#c6bfb1',
 '447b83':palette['water'],'467f87':palette['water'],'547e82':palette['water'],'a8b886':palette['lawns'][0],'9eaf79':palette['lawns'][1],
 '9db580':palette['lawns'][1],'93aa79':palette['lawns'][1],'b6bda5':'#b2ba9e',
 '638455':palette['woodland'][0],'76935f':palette['woodland'][2],'52794c':palette['woodland'][1],
 '54744d':palette['woodland'][0],'6e8754':palette['woodland'][1],'82935f':palette['woodland'][2],
 '6b8551':'#537847','7a915b':'#799856','60815b':'#456d48',
 '4b6941':'#416844','6c874d':'#5d854d','789554':'#809d59',
 '66838b':palette['glass'][0],'78959a':palette['glass'][1],'63828d':palette['glass'][0],
 '96aeb2':palette['glass'][2],'758e98':palette['glass'][1],
 '689776':palette['sports_green'],'88a388':palette['sports_green'],'b68e73':palette['sports_clay'],
 'dedfcf':'#f0eee0','e7e5d4':'#e5e2cd','eee2b4':'#e4c979','c5c5b6':'#c4bbaa'
}
for m in bpy.data.materials:
 key=m.name.removeprefix('Museum_').split('.')[0]
 if key in mapping:
  glass=key in ['66838b','78959a','63828d','96aeb2','758e98']
  setcolor(m,mapping[key],.34 if glass else .88,.10 if glass else 0);stats['recolored_materials']+=1
for name in ['ground','context_ground']:
 o=bpy.data.objects.get(name)
 if o and o.type=='MESH':
  for m in o.data.materials:setcolor(m,'#b0b59b')
# Keep terrain surface topology. Recolor existing transition/grass vertex materials.
for m in bpy.data.materials:
 if m.name=='OSM_Woodland_Transition':setcolor(m,'#81975e')

bodycols={'d4d0c0','c8c9c1','d8d9cf','b9c5c5'}
wallmats=[g.mat(c) for c in palette['walls']];roofmats=[g.mat(c) for c in palette['roofs']];aptroofs=[g.mat(c) for c in palette['apartment_roofs']]
for m in roofmats+aptroofs:setcolor(m,'#'+m.name.split('_')[-1].split('.')[0],.92)
for o in list(bpy.context.scene.objects):
 if o.type!='MESH':continue
 isbody=o.name.startswith('building_') or (o.name.startswith('district_#') and o.name.split('#')[1].split('.')[0] in bodycols)
 if not isbody:continue
 # Each disconnected shell has one stable palette choice; adjacent faces never get random colors.
 mesh=o.data.copy();o.data=mesh;parent=list(range(len(mesh.vertices)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for face in mesh.polygons:
  ids=list(face.vertices);r=find(ids[0])
  for vi in ids[1:]:parent[find(vi)]=r
 groups={}
 for i,v in enumerate(mesh.vertices):groups.setdefault(find(i),[]).append(i)
 choices={}
 for root,ids in groups.items():
  coords=[o.matrix_world@mesh.vertices[i].co for i in ids];cx=sum(v.x for v in coords)/len(coords);cy=sum(v.y for v in coords)/len(coords);height=max(v.z for v in coords)-min(v.z for v in coords)
  seed=abs(round(cx/13)*73856093+round(cy/13)*19349663);choices[root]=(seed,height);stats['building_shells']+=1
 mesh.materials.clear()
 for m in wallmats+roofmats+aptroofs:mesh.materials.append(m)
 for face in mesh.polygons:
  seed,height=choices[find(face.vertices[0])];coords=[o.matrix_world@mesh.vertices[i].co for i in face.vertices]
  top=min(v.z for v in coords)>3 and max(v.z for v in coords)-min(v.z for v in coords)<.015
  if top:face.material_index=len(wallmats)+(len(roofmats)+seed%len(aptroofs) if height>25 else seed%len(roofmats));stats['roof_faces']+=1
  else:face.material_index=seed%len(wallmats)
 mesh.update();stats['building_meshes']+=1

# Sports surfaces: existing mapped footprints, simplified painted markings inside.
for w in ways:
 p=w['points'];t=w['tags'];cx,cz=center(p)
 if t.get('leisure')!='pitch' or p[0]!=p[-1] or not inframe(cx,cz):continue
 p=p[:-1];cx,cz=center(p)
 if len(p)!=4:continue
 a,b=p[0],p[1];length=math.dist(a,b);depth=math.dist(p[1],p[2])
 if min(length,depth)<10 or max(length,depth)>130:continue
 ux,uz=(b[0]-a[0])/length,(b[1]-a[1])/length
 def local(x,z):return (cx+ux*x-uz*z,cz+uz*x+ux*z)
 corners=[local(x,z) for x,z in [(-length*.43,-depth*.43),(length*.43,-depth*.43),(length*.43,depth*.43),(-length*.43,depth*.43)]]
 if not all(inside(q,p) for q in corners):continue
 sport=t.get('sport','');color=palette['sports_clay'] if sport in ['basketball','tennis'] else palette['sports_green']
 g.polygon('painted_court',corners,.151,.012,color)
 for aa,bb in zip(corners,corners[1:]+corners[:1]):g.segment('court_boundary',aa,bb,.16,.012,'#eee9d5',base=.171,record=False)
 g.segment('court_halfway',local(0,-depth*.43),local(0,depth*.43),.16,.012,'#eee9d5',base=.171,record=False)
 radius=min(length,depth)*.13
 ring=[local(math.cos(i*math.tau/24)*radius,math.sin(i*math.tau/24)*radius) for i in range(24)]
 for aa,bb in zip(ring,ring[1:]+ring[:1]):g.segment('court_circle',aa,bb,.14,.012,'#eee9d5',base=.171,record=False)
 stats['sports_courts']+=1
# Small paving accents stay in already-authored courtyard pockets.
detail=json.loads((S/'district-street-detail-metrics.json').read_text(encoding='utf-8'))
for row in detail['placements']:
 if row['type']!='courtyard':continue
 p=row['polygon'];cx,cz=center(p)
 for aa,bb in zip(p,p[1:]+p[:1]):
  # Narrow paving border, no new walls or walk obstacles.
  a=(cx+(aa[0]-cx)*.95,cz+(aa[1]-cz)*.95);b=(cx+(bb[0]-cx)*.95,cz+(bb[1]-cz)*.95)
  g.segment('paving_inlay',a,b,.3,.014,'#af8f73',base=.181,record=False);stats['paving_inlays']+=1
g.finish();scene=bpy.context.scene
# Neutral daylight preview, with softer shadows for judging the actual palette.
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.7
bpy.ops.wm.save_as_mainfile(filepath=str(target))
from blender_static_batch import batch
batch(scene)
out=R/'public/models/bitgaram-overview.glb';bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
(S/'district-color-metrics.json').write_text(json.dumps(dict(counts=stats,palette_file='district-palette.json',reference='User drone and Esri imagery color families; per-building paint and roof colors are estimates.'),ensure_ascii=False,indent=2),encoding='utf-8')
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.eevee.taa_render_samples=32
for name,position,aim,scale in [('district-color',(1400,2450,2600),(100,0,0),4100),('district-color-close',(-650,650,450),(-420,0,190),1050)]:
 scene.camera.location=g.bp(*position);scene.camera.rotation_euler=(Vector(g.bp(*aim))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=scale
 scene.render.filepath=str(O/(name+'-v9.png'));bpy.ops.render.render(write_still=True)
print('COLOR DETAIL',stats,flush=True)
