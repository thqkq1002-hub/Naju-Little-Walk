"""Ground-level and attic views for the independently saved interior revision."""
import bpy, sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/yeongsanpo-literature-interior.blend'))
scene=bpy.context.scene;cam=scene.camera;scene.render.resolution_x=1440;scene.render.resolution_y=1000
scene.view_settings.exposure=.45
def p(x,y,z):return (x,-z,y)
views=[('reading',(-7.6,5.08,2.15),(-5.2,4.90,-6),22),('reading-window',(-4,5.08,-7.6),(-8.0,5.13,-1.2),23),('library',(-4.0,1.75,3.0),(-5.7,1.65,-6.5),24),('exhibit',(5.8,1.75,4.5),(3.7,1.8,-5.5),23)]
for name,eye,target,lens in views:
    if '--only' in sys.argv and name!=sys.argv[sys.argv.index('--only')+1]:continue
    cam.data.lens=lens;cam.location=p(*eye);cam.rotation_euler=(Vector(p(*target))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(root/f'outputs/literature-{name}-detail.png');bpy.ops.render.render(write_still=True)
