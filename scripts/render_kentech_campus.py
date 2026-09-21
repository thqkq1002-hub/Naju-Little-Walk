"""Export and review the final editable campus without modifying that revision."""
import bpy,sys,gzip
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from kentech_export import batch_and_export
O=R/'outputs/kentech';bpy.ops.wm.open_mainfile(filepath=str(O/'kentech-campus-v52-final.blend'));scene=bpy.context.scene
batch_and_export(scene,R/'public/models/bitgaram-kentech.glb')
raw=(R/'public/models/bitgaram-kentech.glb').read_bytes();(R/'public/models/bitgaram-kentech.glb.gz').write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
print('EXPORT complete',len(raw),'bytes',len(scene.objects),'objects',flush=True)
cam=scene.camera
for name,pos,aim,lens in [('campus-overview',(-410,420,560),(30,0,20),34),('main-building',(-64,36,118),(44,9,-4),35),('first-floor',(-5,1.7,5),(7,2,-5),22)]:
    cam.location=(pos[0],-pos[2],pos[1]);cam.rotation_euler=(Vector((aim[0],-aim[2],aim[1]))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;scene.render.filepath=str(O/(name+'-v52.png'));bpy.ops.render.render(write_still=True)
print('REVIEW COMPLETE',flush=True)
