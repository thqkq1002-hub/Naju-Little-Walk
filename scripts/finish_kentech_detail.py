"""Final visual corrections and foliage reduction; preserves both earlier revisions."""
import bpy,sys,gzip,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from museum_geometry import MuseumGeometry
from kentech_export import batch_and_export
O=R/'outputs/kentech';target=O/'kentech-campus-v53-final.blend'
if target.exists():raise RuntimeError('Existing artist revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(O/'kentech-campus-v53.blend'));scene=bpy.context.scene
g=MuseumGeometry(scene,(0,0),0)
for m in bpy.data.materials:
    if len(m.name)==13 and m.name.startswith('Museum_'):g.materials['#'+m.name[7:]]=m
# Keep the irregular crown silhouette with one third of the leaf cards.
for mesh in list(bpy.data.meshes):
    if not mesh.name.startswith('Detail_crown_'):continue
    vbase=len(mesh.vertices)-82*4;fbase=len(mesh.polygons)-82*2
    vs=[tuple(v.co) for v in mesh.vertices[:vbase]];fs=[tuple(p.vertices) for p in mesh.polygons[:fbase]]
    for i in range(0,82,3):
        offset=len(vs);vs.extend(tuple(v.co) for v in mesh.vertices[vbase+i*4:vbase+i*4+4]);fs.extend([(offset,offset+1,offset+2),(offset,offset+2,offset+3)])
    mesh.clear_geometry();mesh.from_pydata(vs,[],fs);mesh.update()
    for p in mesh.polygons:p.use_smooth=p.index<fbase
for o in scene.objects:
    if o.type=='FONT' and o.name.startswith('label_KENTECH') and 3<o.location.z<3.3:
        o.location.z=3.38;o.location.y-=.28;o.scale*=.75
    if o.name.startswith(('detail_atrium_glazing','detail_atrium_pane','detail_atrium_transom')):o.location.y-=.55
# Avoid an unarticulated dark wall at the glazed connection between lecture wings.
for x in [28.1,29.7,31.3,32.9,34.5,35.7]:
    for y in [6.25,8.4,10.55,12.7,14.85,17,19.15]:
        g.box('detail_link_glazing',x,y,12.12,1.42,2.02,.14,'#4c7279',record=False)
    g.box('detail_link_mullion',x-.77,13,12.24,.06,15.6,.08,'#455e63',record=False)
for y in [5.2,7.3,9.45,11.6,13.75,15.9,18.05,20.2]:
    g.box('detail_link_transom',32,y,12.24,8,.06,.08,'#455e63',record=False)
scene.eevee.taa_render_samples=40
bpy.ops.wm.save_as_mainfile(filepath=str(target));editable=len(scene.objects)
batch_and_export(scene,R/'public/models/bitgaram-kentech.glb')
raw=(R/'public/models/bitgaram-kentech.glb').read_bytes();packed=gzip.compress(raw,compresslevel=9,mtime=0)
(R/'public/models/bitgaram-kentech.glb.gz').write_bytes(packed)
metrics=dict(editableObjects=editable,exportMeshes=sum(o.type=='MESH' for o in scene.objects),glbBytes=len(raw),gzipBytes=len(packed),foliageReduction='82 to 28 leaf cards per canopy; smooth core')
(R/'knowledge/sources/kentech-v52/detail-v53-metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf8')
print('FINAL DETAIL',metrics,flush=True)
cam=scene.camera
for name,pos,aim,lens in [('main-building',(-64,36,118),(44,9,-4),35),('entrance',(-16,1.72,26),(-3,5.5,10),23)]:
    cam.location=g.bp(*pos);cam.rotation_euler=(Vector(g.bp(*aim))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
    scene.render.filepath=str(O/(name+'-v53-final.png'));bpy.ops.render.render(write_still=True)
print('FINAL REVIEW COMPLETE',flush=True)
