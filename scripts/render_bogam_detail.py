"""Review the saved museum detail model at visitor eye height, without editing it."""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bogam-museum-detailed.blend'))
scene=bpy.context.scene; cam=scene.camera
frame=json.loads((root/'knowledge/sources/bogam-museum-hall-frame.json').read_text(encoding='utf-8'))['hallFrame']
def p(x,y,z):
    c,s=math.cos(frame['worldXZangle']),math.sin(frame['worldXZangle'])
    return (frame['center'][0]+x*c-z*s,-frame['center'][1]-x*s-z*c,y)
scene.render.resolution_x=1500;scene.render.resolution_y=1000
scene.render.resolution_percentage=100
cam.data.type='PERSP';cam.data.clip_start=.08
scene.view_settings.exposure=.4
burials=json.loads((root/'public/bogam-museum-world.json').read_text(encoding='utf-8'))['burials']
b=next(b for b in burials if b['id']=='S12');x,z=b['model_center'];y=b['replica_floor']
views=[('hall',(20.7,5.24,12),(-6,4,-10),20),
       ('stonework',(x+.4,y+4,z+3.8),(x,y+.5,z),32),
       ('exhibits',(20.3,1.85,12),(23,1.7,3),23),
       ('replica',(-17,1.85,27),(1,3.1,0),22)]
for name,eye,target,lens in views:
    if '--only' in sys.argv and name!=sys.argv[sys.argv.index('--only')+1]:continue
    cam.data.lens=lens;cam.location=p(*eye)
    cam.rotation_euler=(Vector(p(*target))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(root/f'outputs/bogam-museum-detailed-{name}.png')
    bpy.ops.render.render(write_still=True)
