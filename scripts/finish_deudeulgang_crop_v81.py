"""Finish the v81 draft by trimming the off-grove path loop, in Blender."""
import bpy, bmesh, json, gzip, struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'outputs/deudeulgang-v81'
source=O/'deudeulgang-grove-river-v81.blend';target=O/'deudeulgang-grove-river-v81-finished.blend'
if target.exists():raise RuntimeError('Existing finished edit preserved')
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.view_layer.update()
removed=[]
for o in list(bpy.context.scene.objects):
    if o.type!='MESH' or not o.name.startswith(('path_','grove_trail_surface_v81')):continue
    points=[o.matrix_world@v.co for v in o.data.vertices]
    if max(-v.y for v in points)<=240:continue
    if min(-v.y for v in points)>=240:
        removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True);continue
    o.data=o.data.copy();o.data.transform(o.matrix_world);o.matrix_world.identity()
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,-240,0),plane_no=(0,-1,0),clear_outer=True,clear_inner=False)
    bm.to_mesh(o.data);bm.free();o.data.update()

def clip(poly):
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        ina=a[1]<=240;inb=b[1]<=240
        if ina:out.append(a)
        if ina!=inb:
            t=(240-a[1])/(b[1]-a[1]);out.append([a[0]+t*(b[0]-a[0]),240])
    return out
p=R/'public/deudeulgang-world.json';w=json.loads(p.read_text(encoding='utf8'));kept=[]
for s in w['solids']:
    if s['name'].startswith(('path_','walk-floor_grove_trail_v81')):
        s['footprint']=clip(s['footprint'])
        if len(s['footprint'])<3:continue
    kept.append(s)
w['solids']=kept;w['cropRevision']['trailEnd']=240
p.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':')),encoding='utf8')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
out=O/'deudeulgang-v81-finished.glb'
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
raw=out.read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);tail=raw[20+n:]
for m in d.get('materials',[]):
    if m.get('name')=='Pine_needles_alpha_clip':m.update(alphaMode='MASK',alphaCutoff=.48,doubleSided=True)
j=json.dumps(d,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
raw=struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail;packed=gzip.compress(raw,9,mtime=0)
(R/'public/models/deudeulgang.glb').write_bytes(raw);(R/'public/models/deudeulgang.glb.gz').write_bytes(packed)
p=R/'knowledge/sources/deudeulgang/crop-v81.json';report=json.loads(p.read_text(encoding='utf8'))
report.update(editable=str(target.relative_to(R)),trailEnd=240,glbBytes=len(raw),gzipBytes=len(packed),meshObjects=sum(o.type=='MESH' for o in bpy.context.scene.objects))
report['removedNames']+=removed;report['removedObjects']=len(report['removedNames'])
p.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('FINISHED_V81',len(raw),len(packed),flush=True)
