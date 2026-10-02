"""Build the editable Blender scene and browser GLB from the downloaded OSM extract.
Run with Blender --background --python scripts/build_city.py. No add-ons required.
Existing scenes are preserved: this script creates a separate scene and refuses to
overwrite the deliverable unless --replace is explicitly supplied after --.
"""
import bpy
import json
import gzip
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'outputs' / 'geumseonggwan.blend'
if '--output-blend' in sys.argv:
    OUTPUT=ROOT/Path(sys.argv[sys.argv.index('--output-blend')+1])
if OUTPUT.exists() and '--replace' not in sys.argv:
    raise RuntimeError('Output exists. Use -- --replace to rebuild the generated deliverable.')
OUTPUT.parent.mkdir(exist_ok=True)
(ROOT / 'public' / 'models').mkdir(exist_ok=True)

scene = bpy.data.scenes.new('Naju_Geumseonggwan_MVP')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
groups = {}
for name in ('01_Actual_Map', '02_Estimated_Architecture', '03_Illustrative_Interior', '04_Presentation'):
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    groups[name] = collection

LAT, LON = 35.0327357, 126.7167886
MX = 111320 * math.cos(math.radians(LAT))
MZ = 111320
def project(lon, lat):
    return [(float(lon) - LON) * MX, -(float(lat) - LAT) * MZ]
def blender_point(x, y, z):
    return (x, -z, y)

xml = ET.parse(ROOT / 'knowledge' / 'sources' / 'geumseonggwan.osm').getroot()
nodes = {n.attrib['id']: project(n.attrib['lon'], n.attrib['lat']) for n in xml.findall('node')}
ways = []
for w in xml.findall('way'):
    tags = {t.attrib['k']: t.attrib['v'] for t in w.findall('tag')}
    points = [nodes[n.attrib['ref']] for n in w.findall('nd') if n.attrib['ref'] in nodes]
    ways.append({'id': w.attrib['id'], 'tags': tags, 'points': points})

low = project(126.71505, 35.0316)
high = project(126.71845, 35.03425)
bounds = [low[0], high[0], high[1], low[1]]
solids, signs, places, buildings = [], [], [], []
materials = {}
def material(color):
    if color not in materials:
        m = bpy.data.materials.new('mat_' + color.lstrip('#'))
        rgb = [int(color.lstrip('#')[i:i+2], 16) / 255 for i in (0, 2, 4)]
        # Convert authored sRGB colors to linear for Blender/glTF material factors.
        rgb = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb]
        m.diffuse_color = (*rgb, 1)
        m.use_nodes = True
        shader = m.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (*rgb, 1)
        shader.inputs['Roughness'].default_value = .83
        materials[color] = m
    return materials[color]

def finish(obj, s, group):
    obj.name = s['name']
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    groups[group].objects.link(obj)
    obj.data.materials.append(material(s['color']))
    obj['source_class'] = group
    obj['collision'] = s.get('collision', False)
    solids.append(s)
    return obj

def box(name, x, y, z, w, h, d, color, collision=False, rotation=0, group='02_Estimated_Architecture'):
    s = dict(name=name, kind='box', position=[x,y,z], size=[w,h,d], color=color, collision=collision, rotation=rotation)
    bpy.ops.mesh.primitive_cube_add(size=1, location=blender_point(x,y,z))
    o = bpy.context.object; o.scale = (w,d,h); o.rotation_euler.z = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o,s,group)

def polygon(name, points, height, color, collision=False, base=0, group='01_Actual_Map'):
    pts = points[:-1] if points[0] == points[-1] else points
    n = len(pts)
    verts = [blender_point(x,base,z) for x,z in pts] + [blender_point(x,base+height,z) for x,z in pts]
    faces = [tuple(reversed(range(n))), tuple(range(n, n*2))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh = bpy.data.meshes.new(name); mesh.from_pydata(verts, [], faces); mesh.update()
    o = bpy.data.objects.new(name,mesh); scene.collection.objects.link(o)
    s = dict(name=name,kind='building',position=[0,base,0],size=[1,height,1],color=color,collision=collision,footprint=pts)
    finish(o,s,group)
    # Imported polygons may have either winding direction.
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT'); o.select_set(False)
    return o

def segment(name,a,b,width,height,color,collision=False,base=0,group='02_Estimated_Architecture'):
    dx,dz = b[0]-a[0], b[1]-a[1]
    return box(name,(a[0]+b[0])/2,base+height/2,(a[1]+b[1])/2,math.hypot(dx,dz),height,width,color,collision,math.atan2(-dz,dx),group)

def roof(name, points, base, height=2.6):
    # A simplified hipped roof. Dimensions follow the first four mapped corners;
    # pitch, eaves and roof style are illustrative, not a survey reconstruction.
    a,b,c,d = points[:4]
    ux,uz = c[0]-b[0],c[1]-b[1]; width=math.hypot(ux,uz)+2.5
    depth=math.dist(a,b)+2.5; theta=math.atan2(-uz,ux)
    cx,cz=sum(p[0] for p in points[:4])/4,sum(p[1] for p in points[:4])/4
    vertices=[(-width/2,0,-depth/2),(width/2,0,-depth/2),(width/2,0,depth/2),(-width/2,0,depth/2),(-width*.37,height,0),(width*.37,height,0)]
    verts=[]
    for x,y,z in vertices:
        wx=cx+x*math.cos(theta)+z*math.sin(theta); wz=cz-x*math.sin(theta)+z*math.cos(theta)
        verts.append(blender_point(wx,base+y,wz))
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4),(3,2,1,0)]); mesh.update()
    o=bpy.data.objects.new(name,mesh); scene.collection.objects.link(o)
    finish(o,dict(name=name,kind='roof',position=[cx,base,cz],size=[width,height,depth],color='#3d5050',rotation=theta),'02_Estimated_Architecture')
    box(name+'_eaves',cx,base-.12,cz,width,.23,depth,'#394d4b',False,theta)
    box(name+'_ridge',cx,base+height,cz,width*.75,.23,.30,'#53675e',False,theta)

font_path=Path('C:/Windows/Fonts/malgun.ttf')
font=bpy.data.fonts.load(str(font_path)) if font_path.exists() else None
def label(text,x,y,z,width=5,rotation=0,color='#f4e7c9'):
    curve=bpy.data.curves.new('text_'+text,'FONT'); curve.body=text; curve.align_x='CENTER'; curve.align_y='CENTER'; curve.size=1
    if font: curve.font=font
    curve.extrude=.002
    o=bpy.data.objects.new('label_'+text,curve); groups['04_Presentation'].objects.link(o)
    o.location=blender_point(x,y,z); o.rotation_euler=(math.pi/2,0,rotation)
    o.data.materials.append(material(color))
    bpy.context.view_layer.update()
    scale=min(width/max(o.dimensions.x,.01),.7); o.scale=(scale,scale,scale)
    signs.append(dict(text=text,position=[x,y,z],width=width,rotation=rotation,color=color))

def clip_segment(a,b):
    dx,dz=b[0]-a[0],b[1]-a[1]; t0,t1=0.,1.
    for p,q in [(-dx,a[0]-bounds[0]),(dx,bounds[1]-a[0]),(-dz,a[1]-bounds[2]),(dz,bounds[3]-a[1])]:
        if abs(p)<1e-9:
            if q<0:return None
        else:
            r=q/p
            if p<0:t0=max(t0,r)
            else:t1=min(t1,r)
    if t0>t1:return None
    return ([a[0]+t0*dx,a[1]+t0*dz],[a[0]+t1*dx,a[1]+t1*dz])

# Map base; the separate surroundings pass adds explicitly attributed roof observations.
box('ground_base',(bounds[0]+bounds[1])/2,-1.5,(bounds[2]+bounds[3])/2,bounds[1]-bounds[0],3,bounds[3]-bounds[2],'#adbcb0',group='04_Presentation')
for w in ways:
    tags=w['tags']; pts=w['points']
    if w['id']=='540205109':
        polygon('ground_geumseonggwan_boundary',pts,.028,'#d1cbb3')
    if tags.get('highway'):
        hw=tags['highway']; width=2.2 if hw in ('footway','path','steps') else 4 if hw=='service' else 6.5
        for i,(a,b) in enumerate(zip(pts,pts[1:])):
            clipped=clip_segment(a,b)
            if not clipped:continue
            a,b=clipped
            if math.dist(a,b)<.1:continue
            segment('road-edge_'+w['id']+'_'+str(i),a,b,width+1.0,.04,'#d5dace',group='01_Actual_Map')
            segment('road_'+w['id']+'_'+str(i),a,b,width,.052,'#7d8c89',group='01_Actual_Map')

exec((ROOT / 'scripts' / 'photo_architecture.py').read_text(encoding='utf-8'))
exec((ROOT / 'scripts' / 'geumseonggwan_detail.py').read_text(encoding='utf-8'))
exec((ROOT / 'scripts' / 'geumseonggwan_surroundings.py').read_text(encoding='utf-8'))
hall_entry=None
for w in ways:
    tags=w['tags']
    if not tags.get('building'):continue
    pts=w['points'][:-1]; name=tags.get('name','건물')
    buildings.append({'osm_id':w['id'],'name':name,'footprint':pts,'height_source':'MVP estimate'})
    if w['id']=='832423358':
        print('Building photo-referenced hall',flush=True)
        hall_entry=photo_hall(w)
        continue
    center=[sum(p[0] for p in pts)/len(pts),sum(p[1] for p in pts)/len(pts)]
    special=w['id'] in ('832423356','832423357')
    if special:
        photo_gate(w)
        continue
    height=3.5
    if not special:
        polygon('osm-building_'+w['id'],pts,height,'#d8d0b8',True)
        polygon('roof-cap_'+w['id'],pts,.24,'#596b64',False,height,'02_Estimated_Architecture')
        places.append(dict(id=w['id'],name=name,position=center,radius=22,description='지도에 등록된 건물 윤곽입니다. 이 건물은 외부만 둘러볼 수 있어요.'))
        continue
    polygon('ground_floor_'+w['id'],pts,.065,'#bfb092')
    edges=list(zip(pts,pts[1:]+pts[:1]))
    places.append(dict(id=w['id'],name=name,position=center,radius=9,description='가운데 통로를 따라 마당으로 걸어가 보세요.'))
    for i,(a,b) in enumerate(edges):
        length=math.dist(a,b); ux,uz=(b[0]-a[0])/length,(b[1]-a[1])/length
        opening=length>max(math.dist(*e) for e in edges)*.88
        wall_name='hall-wall_'+w['id']+'_'+str(i)
        if opening:
            gap=4.5
            mid=[(a[0]+b[0])/2,(a[1]+b[1])/2]
            left=[mid[0]-ux*gap/2,mid[1]-uz*gap/2]; right=[mid[0]+ux*gap/2,mid[1]+uz*gap/2]
            segment(wall_name+'_L',a,left,.36,height,'#e2d5b8',True)
            segment(wall_name+'_R',right,b,.36,height,'#e2d5b8',True)
            segment(wall_name+'_lintel',left,right,.4,height-3.0,'#875a43',False,3.0)
            for p in (left,right):box('post_entry',p[0],height/2,p[1],.38,height,.38,'#76503b',True)
        else:segment(wall_name,a,b,.36,height,'#e2d5b8',True)
        # Timber posts and a continuous green-red beam give the massing a hanok character.
        for n in range(max(1,int(length/4))+1):
            t=n/max(1,int(length/4)); p=[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t]
            if opening and abs((t-.5)*length)<2.5:continue
            box('timber_post',p[0],height/2,p[1],.25,height,.25,'#86604a',False)
        segment('dancheong_beam',a,b,.5,.22,'#4b7967',False,height-.35)
    roof('roof_'+w['id'],pts,height)

print('Building courtyard details',flush=True)
detailed_grounds()
print('Building entrance and neighboring blocks',flush=True)
surroundings=build_surroundings()
print('Writing collision data and Blender output',flush=True)
# Spawn just outside the main hall. The rest of the real mapped area remains walkable.
assert hall_entry is not None
spawn_point=hall_detail_frame.point(hall_detail_info['center'],hall_detail_info['front']-28)
spawn={'x':spawn_point[0],'z':spawn_point[1],'yaw':math.atan2(-hall_detail_frame.v[0],-hall_detail_frame.v[1])}
world=dict(title='나주 산책',subtitle='금성관과 주변 거리 · 사진·영상 참고',source='© OpenStreetMap contributors, ODbL 1.0 · 주변 지붕 참고: Esri, Vantor, Earthstar Geographics, GIS User Community',bounds=bounds,spawn=spawn,solids=solids,signs=signs,places=places,buildings=buildings,origin={'lat':LAT,'lon':LON},architecture=hall_detail_info,surroundings=surroundings,limitations=['Five building outlines, roads, the precinct and parking boundary are from OSM; additional roof outlines are manually interpreted from Esri World Imagery, whose capture date is unknown.','The 2009 AKS photos, 2020-02-18 official interior photos and public 2015 survey-plan thumbnails inform a pre-repair reference model; this is not a current-site scan.','OSM outlines are interpreted as roof coverage. Column grid, eave heights, joinery, painted motifs and landscape coordinates are photo-proportioned estimates, not measured dimensions. Published area figures differ.','The center door is opened for exploration. Gate upper-floor access and concealed room construction are not reconstructed.','Terrain is flat. Road centerlines are sourced; road widths, surface finishes, furniture, parked cars and surrounding building heights/windows are estimates.'],source_url='https://api.openstreetmap.org/api/0.6/map?bbox=126.7152,35.0318,126.7183,35.0341')
world['walkRoute']=[hall_detail_frame.point(hall_detail_info['center'],d) for d in (hall_detail_info['front']-28,-24.5,-11.1,hall_detail_info['front']-5.2,hall_detail_info['front'],hall_detail_info['front']+4.7)]
(ROOT/'public'/'city-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(ROOT/'knowledge'/'sources'/'model-provenance.json').write_text(json.dumps({k:world[k] for k in ('source','source_url','origin','buildings','architecture','surroundings','limitations')},ensure_ascii=False,indent=2),encoding='utf-8')

# Keep a useful camera and light in the editable file, excluding both from GLB.
bpy.ops.object.camera_add(location=(100,-150,135))
camera=bpy.context.object; camera.name='Overview_camera'
camera.rotation_euler=(Vector((0,15,0))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO'; camera.data.ortho_scale=260; scene.camera=camera
bpy.ops.object.light_add(type='SUN',location=(-70,-80,130))
sun=bpy.context.object; sun.rotation_euler=(.6,-.4,-.4); sun.data.energy=2.3; sun.data.angle=.12
scene.world=bpy.data.worlds.new('Naju_daylight'); scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.78,.85,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=1400; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(ROOT/'outputs'/'geumseonggwan-surroundings-overview.png')
scene.view_settings.view_transform='AgX'

# Only this generated scene is exported; existing user scene contents are untouched.
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public'/'models'/'geumseonggwan.glb'),export_format='GLB',use_active_scene=True,export_cameras=False,export_lights=False,export_extras=True,export_apply=True)
(ROOT/'public'/'models'/'geumseonggwan.glb.gz').write_bytes(gzip.compress((ROOT/'public'/'models'/'geumseonggwan.glb').read_bytes(),compresslevel=9,mtime=0))
print(json.dumps({'blend':str(OUTPUT),'buildings':len(buildings),'objects':len(scene.objects),'spawn':spawn,'hall_entry':hall_entry},ensure_ascii=False))
if '--render' in sys.argv:
    bpy.ops.render.render(write_still=True)
if '--render-surroundings' in sys.argv:
    camera.data.type='PERSP';camera.data.lens=27;camera.data.clip_start=.08
    for name,eye,target in [('geumseonggwan-entrance-street',(3,3.0,-122),(25,3.5,-98)),('geumseonggwan-entrance-aerial',(40,50,-143),(27,0,-82)),('geumseonggwan-parking-street',(-24,6,-116),(-16,2,-39))]:
        camera.location=hall_detail_frame.xyz(eye);camera.rotation_euler=(Vector(hall_detail_frame.xyz(target))-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(ROOT/'outputs'/f'{name}.png');bpy.ops.render.render(write_still=True)
if '--render-details' in sys.argv or '--render-front' in sys.argv:
    f=hall_detail_frame;c=hall_detail_info['center'];front=hall_detail_info['front']
    camera.data.type='PERSP';camera.data.lens=26;camera.data.clip_start=.08
    for name,eye,target in [('geumseonggwan-front-detailed',(c,7,-37),(c,4,8)),('geumseonggwan-interior-detailed',(c,2.65,front+3.5),(c,5.8,front+13)),('geumseonggwan-ceiling-detailed',(c,2.5,10),(c+.1,7.7,10.2)),('geumseonggwan-manghwaru-detailed',(22,5,-126),(22,4,-98)),('geumseonggwan-side-detailed',(73,7,-10),(36,4,9))]:
        if '--render-front' in sys.argv and '--render-details' not in sys.argv and name!='geumseonggwan-front-detailed':continue
        camera.location=f.xyz(eye);camera.rotation_euler=(Vector(f.xyz(target))-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(ROOT/'outputs'/f'{name}.png');bpy.ops.render.render(write_still=True)
