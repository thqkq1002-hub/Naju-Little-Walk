"""Editorial far-water crop; preserve the v81 artist file and all grove meshes."""
import bpy, bmesh, json, gzip, struct, hashlib
from pathlib import Path

R = Path(__file__).resolve().parents[1]
O = R / 'outputs/deudeulgang-v82'
O.mkdir(parents=True, exist_ok=True)
source = R / 'outputs/deudeulgang-v81/deudeulgang-grove-river-v81-finished.blend'
target = O / 'deudeulgang-river-trim-v82.blend'
if target.exists():
    raise RuntimeError('Existing editable revision preserved')
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
world_path = R / 'public/deudeulgang-world.json'
before = json.loads(world_path.read_text(encoding='utf8'))
(O / 'world-before.json').write_text(json.dumps(before, ensure_ascii=False), encoding='utf8')
cut = -125.0
old_poly = next(s['footprint'] for s in before['solids'] if s['name'] == 'mapped_river_water')
poly = []
for a, b in zip(old_poly, old_poly[1:] + old_poly[:1]):
    ina, inb = a[0] >= cut, b[0] >= cut
    if ina:
        poly.append(a)
    if ina != inb:
        t = (cut - a[0]) / (b[0] - a[0])
        poly.append([cut, a[1] + t * (b[1] - a[1])])
def area(p):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1]))) / 2
def fingerprint(o):
    h = hashlib.sha256()
    h.update(str(tuple(tuple(row) for row in o.matrix_world)).encode())
    for v in o.data.vertices:
        h.update(struct.pack('<3f', *v.co))
    for p in o.data.polygons:
        h.update(str(tuple(p.vertices)).encode())
    h.update(str(tuple(m.name for m in o.data.materials)).encode())
    return h.hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(source))
bpy.context.view_layer.update()
scene = bpy.context.scene
protected = {o.name: fingerprint(o) for o in scene.objects if o.type == 'MESH' and o.name != 'mapped_river_water'}
water = bpy.data.objects['mapped_river_water']
water.data = water.data.copy()
water.data.transform(water.matrix_world)
water.matrix_world.identity()
bm = bmesh.new()
bm.from_mesh(water.data)
result = bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
    dist=.00001, plane_co=(cut,0,0), plane_no=(1,0,0), clear_inner=True, clear_outer=False)
boundary = [e for e in result['geom_cut'] if isinstance(e, bmesh.types.BMEdge) and e.is_boundary]
if boundary:
    bmesh.ops.holes_fill(bm, edges=boundary, sides=0)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(water.data)
bm.free()
water.data.update()
assert min(v.co.x for v in water.data.vertices) >= cut-.001
assert all(fingerprint(bpy.data.objects[n]) == h for n,h in protected.items())
world = before
for s in world['solids']:
    if s['name'] in ('mapped_river_water','river_no_walking'):
        s['footprint'] = poly
world['bounds'][0] = cut
world['riverTrimRevision'] = {'revision':'v82','date':'2026-10-03','minimumX':cut,
    'scope':'Remove far half of water behind the pine grove; original near bank unchanged',
    'limitation':'User-requested display crop, not the actual river width or a new survey'}
world['cropRevision']['displayExtent'] = world['bounds']
scene['river_trim_revision'] = 'v82: far water removed, all non-water meshes unchanged'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(target))
out = O / 'deudeulgang-v82.glb'
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,
    export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
raw = out.read_bytes()
n = struct.unpack_from('<I',raw,12)[0]
d = json.loads(raw[20:20+n])
tail = raw[20+n:]
for m in d.get('materials',[]):
    if m.get('name') == 'Pine_needles_alpha_clip':
        m.update(alphaMode='MASK',alphaCutoff=.48,doubleSided=True)
j = json.dumps(d,separators=(',',':')).encode()
j += b' '*((-len(j))%4)
raw = struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail
packed = gzip.compress(raw,9,mtime=0)
assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
world_path.write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf8')
(R/'public/models/deudeulgang.glb').write_bytes(raw)
(R/'public/models/deudeulgang.glb.gz').write_bytes(packed)
report = dict(source=str(source.relative_to(R)),sourceSha256=source_hash,sourceUnchanged=True,
    editable=str(target.relative_to(R)),protectedMeshObjects=len(protected),allNonWaterMeshesUnchanged=True,
    cutMinimumX=cut,riverAreaBefore=area(old_poly),riverAreaAfter=area(poly),
    removedPercent=round(100*(1-area(poly)/area(old_poly)),2),riverFootprint=poly,
    displayExtent=world['bounds'],glbBytes=len(raw),gzipBytes=len(packed))
(R/'knowledge/sources/deudeulgang/river-trim-v82.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('RIVER_TRIM_V82',json.dumps({k:v for k,v in report.items() if k!='riverFootprint'}),flush=True)
