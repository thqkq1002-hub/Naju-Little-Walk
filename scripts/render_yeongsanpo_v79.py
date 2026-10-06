"""Research review renders of saved copies; never save over the editable scene."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];O=R/'outputs/yeongsanpo-v79'
key=sys.argv[sys.argv.index('--')+1] if '--'in sys.argv else 'yeongsanpo'
bpy.ops.wm.open_mainfile(filepath=str(O/f'{key}-detail-v79.blend'));s=bpy.context.scene
for o in list(s.objects):
    if o.type in ['LIGHT','CAMERA']:bpy.data.objects.remove(o,do_unlink=True)
world=json.loads((R/f'public/{key}-world.json').read_text(encoding='utf-8'))
if key=='yeongsanpo':
    for boat in world['boats']:
        with bpy.data.libraries.load(str(O/f'{boat["id"]}-detail-v79.blend'),link=False) as (a,b):b.objects=[n for n in a.objects if not n.startswith(('Camera','Sun','Fill'))]
        h=boat['home'];transform=Matrix.Translation((h['x'],-h['z'],boat['waterY']))@Matrix.Rotation(h['yaw'],4,'Z')
        for o in b.objects:
            if o and o.type=='MESH':s.collection.objects.link(o);o.matrix_world=transform@o.matrix_world
s.world=bpy.data.worlds.new('Yeongsanpo_review_sky');s.world.use_nodes=True
bg=s.world.node_tree.nodes['Background'];bg.inputs['Color'].default_value=(.60,.74,.83,1);bg.inputs['Strength'].default_value=.65
sun=bpy.data.lights.new('Review_sun','SUN');sun.energy=2.2;sun.angle=.075;so=bpy.data.objects.new('Review_sun',sun);s.collection.objects.link(so);so.rotation_euler=(.40,-.42,-.7)
camera=bpy.data.cameras.new('Review_camera');co=bpy.data.objects.new('Review_camera',camera);s.collection.objects.link(co);s.camera=co;camera.lens=38;camera.clip_end=3000
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=20;s.cycles.use_denoising=True
s.render.resolution_x=1400;s.render.resolution_y=950;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.exposure=.1
def view(name,eye,target):
    co.location=(eye[0],-eye[2],eye[1]);v=Vector((target[0],-target[2],target[1]))-co.location;co.rotation_euler=v.to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(O/f'{name}.png');bpy.ops.render.render(write_still=True)
if key=='yeongsanpo':
    view('wharf-blender-v79',[-204,47,20],[-147,-1.5,125])
    view('frontage-blender-v79',[-166,5.5,113],[-137,2.2,156])
elif key.endswith('literature'):
    view('literature-blender-v79',[7,1.7,7],[-4,1.5,-4])
else:view('history-blender-v79',[-3,1.7,7],[1,1.4,-4])
