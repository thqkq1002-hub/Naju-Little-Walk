"""Preserve the first campus revision, move five lamps off the walking line and export."""
import bpy,sys,json,gzip
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from kentech_export import batch_and_export
O=R/'outputs/kentech';target=O/'kentech-campus-v52-final.blend'
if target.exists():raise RuntimeError('Existing artist revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(O/'kentech-campus-v52.blend'));scene=bpy.context.scene
for o in scene.objects:
    if o.type=='MESH' and o.name.startswith('campus_lamp_'):
        center=sum((o.matrix_world@v.co for v in o.data.vertices),Vector())/len(o.data.vertices)
        if abs(center.y+22)<.01:o.location.y+=4
world=json.loads((R/'public/bitgaram-kentech-world.json').read_text(encoding='utf8'))
for solid in world['solids']:
    if solid['name']=='lamp_obstacle' and abs(sum(p[1] for p in solid['footprint'])/4-22)<.01:
        for p in solid['footprint']:p[1]-=4
(R/'public/bitgaram-kentech-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf8')
scene.camera.location=(-410,-560,420);scene.camera.rotation_euler=(Vector((30,-20,0))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.lens=34
bpy.ops.wm.save_as_mainfile(filepath=str(target));print('FINAL editable scene saved',flush=True)
batch_and_export(scene,R/'public/models/bitgaram-kentech.glb')
raw=(R/'public/models/bitgaram-kentech.glb').read_bytes();(R/'public/models/bitgaram-kentech.glb.gz').write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
cam=scene.camera
for name,pos,aim,lens in [('campus-overview',(-410,420,560),(30,0,20),34),('main-building',(-64,36,118),(44,9,-4),35),('first-floor',(-5,1.7,5),(7,2,-5),22)]:
    cam.location=(pos[0],-pos[2],pos[1]);cam.rotation_euler=(Vector((aim[0],-aim[2],aim[1]))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;scene.render.filepath=str(O/(name+'-v52.png'));bpy.ops.render.render(write_still=True)
print('FINAL COMPLETE',len(raw),'bytes',len(scene.objects),'objects',flush=True)
