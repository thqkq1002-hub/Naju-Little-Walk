"""Review the district, photographed street rhythm and lower landing."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/yeongsanpo-streets.blend'))
scene=bpy.context.scene;cam=scene.camera
scene.render.resolution_x=1500;scene.render.resolution_y=1000
def p(x,y,z):return (x,-z,y)
views=[('district',(-245,220,440),(-25,0,135),35),('street',(-18,1.78,109),(37,2.3,67),23),('samhwa',(-35,4.2,125),(-14,3.4,141),25),('landing',(-152,-4.65,102),(-143,-.8,130),22)]
for name,eye,target,lens in views:
    if '--only' in sys.argv and name!=sys.argv[sys.argv.index('--only')+1]:continue
    cam.data.lens=lens;cam.location=p(*eye);cam.rotation_euler=(Vector(p(*target))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(root/f'outputs/yeongsanpo-{name}-streets.png');bpy.ops.render.render(write_still=True)
