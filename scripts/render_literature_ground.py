"""Review the photographed ground-floor displays and veranda at eye height."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/yeongsanpo-literature-ground.blend'))
scene=bpy.context.scene;cam=scene.camera;scene.render.resolution_x=1440;scene.render.resolution_y=1000
scene.view_settings.exposure=.45
def p(x,y,z):return (x,-z,y)
views=[('exhibition',(5.9,1.73,4.5),(5.9,1.60,-6),23),('panels',(3.2,1.72,-3.9),(8.6,1.55,-1.9),23),('veranda',(-6.6,1.72,7.0),(4.8,1.66,7.7),23),('garden',(4.3,1.72,3.7),(3.5,1.4,15.0),24)]
for name,eye,target,lens in views:
    if '--only' in sys.argv and name!=sys.argv[sys.argv.index('--only')+1]:continue
    cam.data.lens=lens;cam.location=p(*eye);cam.rotation_euler=(Vector(p(*target))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(root/f'outputs/literature-ground-{name}.png');bpy.ops.render.render(write_still=True)
