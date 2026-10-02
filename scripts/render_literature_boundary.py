"""Pedestrian reviews of the entrance, fencing and newly finished house sides."""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/yeongsanpo-boundary.blend'))
scene=bpy.context.scene;cam=scene.camera
scene.render.resolution_x=1440;scene.render.resolution_y=1000;scene.view_settings.exposure=.4
def p(x,y,z):return (223.92+x*math.cos(.15)-z*math.sin(.15),-(115.07+x*math.sin(.15)+z*math.cos(.15)),y)
views=[('entrance',(-9.8,1.74,44),(-2,2.2,12),25),('side',(16,2.3,14),(7,2.4,-1),23),('rear',(10.4,1.72,-7.8),(-5,1.75,-6.4),22),('overview',(26,25,42),(-1,1,13),29)]
for name,eye,target,lens in views:
    if '--only' in sys.argv and name!=sys.argv[sys.argv.index('--only')+1]:continue
    cam.data.lens=lens;cam.location=p(*eye);cam.rotation_euler=(Vector(p(*target))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(root/f'outputs/literature-boundary-{name}.png');bpy.ops.render.render(write_still=True)
