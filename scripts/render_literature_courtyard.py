"""Review the editable courtyard at pedestrian and neighbourhood scales."""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/yeongsanpo-courtyard.blend'))
scene=bpy.context.scene;cam=scene.camera
scene.render.resolution_x=1440;scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.view_settings.exposure=.65
def p(x,y,z):return (x,-z,y)
def local(x,y,z):return p(223.92+x*math.cos(.15)-z*math.sin(.15),y,115.07+x*math.sin(.15)+z*math.cos(.15))
views=[('garden',local(-1.5,1.72,25),local(-.5,2.1,7.5),23),('courtyard',local(18,22,45),local(-3,0,17),32),('neighbourhood',p(313,165,310),p(136,0,146),34)]
for name,eye,target,lens in views:
    if '--only' in sys.argv and name!=sys.argv[sys.argv.index('--only')+1]:continue
    cam.data.lens=lens;cam.location=eye;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(root/f'outputs/yeongsanpo-{name}-review.png')
    bpy.ops.render.render(write_still=True)
