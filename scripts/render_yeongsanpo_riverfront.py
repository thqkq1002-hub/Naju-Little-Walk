"""Street-height and aerial review of the photo-referenced opposite bank row."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/yeongsanpo-riverfront.blend'))
scene=bpy.context.scene;cam=scene.camera
scene.render.resolution_x=1500;scene.render.resolution_y=1000
scene.view_settings.exposure=.4
def p(x,y,z):return (x,-z,y)
views=[('front',(-143,1.75,138.27),(-143,2.2,200),24),
       ('shops',(-154,2.0,138),(-105,3.6,155),25),
       ('warehouses',(-230,2.0,214),(-245,5.4,262),23),
       ('aerial',(-242,135,52),(-145,0,191),32)]
for name,eye,target,lens in views:
    if '--only' in sys.argv and name!=sys.argv[sys.argv.index('--only')+1]:continue
    cam.data.lens=lens;cam.location=p(*eye)
    cam.rotation_euler=(Vector(p(*target))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(root/f'outputs/yeongsanpo-riverfront-{name}.png')
    bpy.ops.render.render(write_still=True)
