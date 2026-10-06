"""Keep the authored pine recreation grove and its adjacent river only.

Reads the preserved v72 Blender revision, never overwrites that artist source.
The clipped display extent is editorial; existing OSM paths and pine transforms
remain in their original geographic coordinates. No new survey is implied.
"""
import bpy, bmesh, sys, json, math, gzip, struct, hashlib
from pathlib import Path
from mathutils import Vector

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from museum_geometry import MuseumGeometry
O=R/'outputs/deudeulgang-v81';O.mkdir(parents=True,exist_ok=True)
source=R/'outputs/quality-v72/deudeulgang-surfaces-v72.blend'
target=O/'deudeulgang-grove-river-v81.blend'
if target.exists():raise RuntimeError('Existing editable revision preserved')
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
world_path=R/'public/deudeulgang-world.json'
before_path=O/'world-before.json'
before=json.loads((before_path if before_path.exists() else world_path).read_text(encoding='utf8'))
if not before_path.exists():before_path.write_text(json.dumps(before,ensure_ascii=False),encoding='utf8')
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
bpy.context.view_layer.update()
g=MuseumGeometry(scene,(0,0),0)
for m in bpy.data.materials:
    if len(m.name)==13 and m.name.startswith('Museum_'):g.materials['#'+m.name[7:]]=m
meta=json.loads((R/'knowledge/sources/deudeulgang/metrics.json').read_text())
grove=meta['grove_polygon'];river=meta['river_polygon']
extent=[-235,88,-198,290]

def clip(poly,axis,limit,greater):
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        ina=(a[axis]>=limit) if greater else (a[axis]<=limit)
        inb=(b[axis]>=limit) if greater else (b[axis]<=limit)
        if ina:out.append(a)
        if ina!=inb:
            t=(limit-a[axis])/(b[axis]-a[axis]);out.append([a[k]+t*(b[k]-a[k]) for k in range(2)])
    return out
river_clip=river
for axis,limit,greater in [(0,extent[0],True),(0,extent[1],False),(1,extent[2],True),(1,extent[3],False)]:river_clip=clip(river_clip,axis,limit,greater)

def footprint_solid(name,poly,height=0,color='#7b8057',collision=False):
    return dict(name=name,kind='building',position=[0,height-.04,0],size=[1,.04,1],footprint=poly,color=color,collision=collision)

# A narrow apron follows the existing grove outline, rather than a giant plate.
apron=[]
for i,p in enumerate(grove):
    a=Vector(grove[i-1]);b=Vector(p);c=Vector(grove[(i+1)%len(grove)])
    tangent=(c-a).normalized();normal=Vector((tangent.y,-tangent.x))
    # Original polygon is clockwise in world x/z; choose outward by centroid.
    centroid=Vector((sum(q[0] for q in grove)/len(grove),sum(q[1] for q in grove)/len(grove)))
    if normal.dot(b-centroid)<0:normal=-normal
    apron.append(list(b+normal*9))

keep_path=lambda name:name.startswith(('path_osm_1306096510','path_osm_1306096511','path_satellite_riverside','path_link_south','path_link_middle'))
def fingerprint(o):
    h=hashlib.sha256();h.update(str(tuple(tuple(row) for row in o.matrix_world)).encode())
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    for p in o.data.polygons:h.update(str(tuple(p.vertices)).encode())
    return h.hexdigest()
protected={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o.name.startswith(('old_pine_','distant_pine_'))}
remove=[]
for o in list(scene.objects):
    n=o.name
    unwanted=n.startswith(('background_','estimated_','west_bank_','satellite_field','crop_row','bridge_','road_parking','ground_floor_landscape','detail_soft_trail','mapped_river_water'))
    unwanted|=n.startswith('path_') and not keep_path(n)
    # The northern toilet lies outside the grove; its separate pieces share x>70.
    if o.type=='MESH' and n.startswith(('mapped_toilet','toilet_')):
        x=sum((o.matrix_world@v.co).x for v in o.data.vertices)/len(o.data.vertices)
        unwanted|=x>70
    if unwanted:remove.append(o)
removed_names=[o.name for o in remove];bpy.data.batch_remove(ids=remove)
# Only the trail portion within the recreation-grove end remains. The mapped
# loop continues beyond the satellite grove outline and would float in empty sky.
trail_end=240
for o in list(scene.objects):
    if o.type!='MESH' or not keep_path(o.name):continue
    points=[o.matrix_world@v.co for v in o.data.vertices]
    if not points or max(-v.y for v in points)<=trail_end:continue
    if min(-v.y for v in points)>=trail_end:
        removed_names.append(o.name);bpy.data.objects.remove(o,do_unlink=True);continue
    o.data=o.data.copy();o.data.transform(o.matrix_world);o.matrix_world.identity()
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,-trail_end,0),plane_no=(0,-1,0),clear_outer=True,clear_inner=False)
    bm.to_mesh(o.data);bm.free();o.data.update()

apron_obj=g.polygon('ground_floor_grove_apron_v81',apron,-.12,.04,'#7b8057')
floor=bpy.data.materials.get('Authored_forest_soil_groundcover_v72')
if floor:
    apron_obj.data.materials.clear();apron_obj.data.materials.append(floor)
    uv=apron_obj.data.uv_layers.active or apron_obj.data.uv_layers.new(name='Ground_UV')
    for p in apron_obj.data.polygons:
        for j in p.loop_indices:
            v=apron_obj.matrix_world@apron_obj.data.vertices[apron_obj.data.loops[j].vertex_index].co
            uv.data[j].uv=(v.x/7,v.y/7)
water=g.polygon('mapped_river_water',river_clip,-.05,.02,'#356c70')
water['no_shadow']=True;water['no_receive_shadow']=True

# Redraw only the retained trail surface; the older batch included external roads.
paths=[]
for original in before['solids']:
    if not keep_path(original['name']):continue
    s=dict(original);s['footprint']=clip(s['footprint'],1,trail_end,False)
    if len(s['footprint'])>=3:paths.append(s)
for s in paths:
    g.polygon('grove_trail_surface_v81',s['footprint'],.06,.012,'#b4a487')['no_shadow']=True

world=dict(before)
discard=lambda s:s['name'].startswith(('background_','satellite_field','bridge_','road_parking','mapped_river_water','river_no_walking')) or (s['name'].startswith('path_') and not keep_path(s['name'])) or (s['name'].startswith(('mapped_toilet','toilet_')) and min(p[0] for p in s.get('footprint',[[s['position'][0],0]]))>70)
world['solids']=[s for s in before['solids'] if not discard(s) and not keep_path(s['name'])]+paths
world['solids']+= [footprint_solid('ground_floor_grove_apron_v81',apron,-.08),footprint_solid('mapped_river_water',river_clip,-.03,'#356c70')]
block=next(s for s in before['solids'] if s['name']=='river_no_walking').copy();block['footprint']=river_clip;world['solids'].append(block)
for s in paths:
    poly=s['footprint'];center=Vector((sum(p[0] for p in poly)/len(poly),sum(p[1] for p in poly)/len(poly)))
    # A tiny invisible joint allowance avoids floating-point gaps at path ends.
    support=[list(Vector(p)+(Vector(p)-center).normalized()*.10) for p in poly]
    world['solids'].append(footprint_solid('walk-floor_grove_trail_v81',support,.072,'#b4a487'))
world['bounds']=extent;world['verticalNavigation']=True;world['requireFloor']=True
world['cropRevision']={'revision':'v81','date':'2026-10-03','displayExtent':extent,'trailEnd':trail_end,'scope':'Original pine grove and adjacent clipped river only','removed':'Estimated hills, farmland, bridge, external roads, northern off-site toilet and off-grove trail tail','unchanged':'280 near/far pine pairs, original grove outline, retained OSM grove trail coordinates, arrivals and guide start','limitation':'Editorial model extent, not a new survey; facility dimensions and vegetation remain estimated'}
world_path.write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf8')
scene['crop_revision']='v81: grove and adjacent river, original trees and paths preserved'
bpy.context.view_layer.update()
assert all(fingerprint(bpy.data.objects[n])==h for n,h in protected.items())
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(O/'deudeulgang-v81.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
raw=(O/'deudeulgang-v81.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);tail=raw[20+n:]
for m in doc.get('materials',[]):
    if m.get('name')=='Pine_needles_alpha_clip':m.update(alphaMode='MASK',alphaCutoff=.48,doubleSided=True)
j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
raw=struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail;packed=gzip.compress(raw,9,mtime=0)
(R/'public/models/deudeulgang.glb').write_bytes(raw);(R/'public/models/deudeulgang.glb.gz').write_bytes(packed)
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
report=dict(source=str(source.relative_to(R)),sourceSha256=source_hash,sourceUnchanged=True,editable=str(target.relative_to(R)),pineObjectsPreserved=len(protected),removedObjects=len(removed_names),removedNames=removed_names,riverFootprint=river_clip,groveFootprint=grove,displayExtent=extent,trailEnd=trail_end,glbBytes=len(raw),gzipBytes=len(packed),meshObjects=sum(o.type=='MESH' for o in scene.objects),images=len(doc.get('images',[])))
(R/'knowledge/sources/deudeulgang/crop-v81.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('CROP_V81',json.dumps({k:v for k,v in report.items() if k not in ['removedNames','riverFootprint','groveFootprint']}),flush=True)
