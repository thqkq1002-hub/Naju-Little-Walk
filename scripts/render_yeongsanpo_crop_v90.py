"""Review the saved crop from the south, showing the removed background boundary."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];O=R/'outputs/yeongsanpo-crop-v90'
report=json.loads((R/'knowledge/sources/yeongsanpo-crop-v90.json').read_text(encoding='utf8'))
bpy.ops.wm.open_mainfile(filepath=str(R/report['editedBlend']));s=bpy.context.scene
for o in list(s.objects):
 if o.type in ('CAMERA','LIGHT'):bpy.data.objects.remove(o,do_unlink=True)
w=json.loads((R/'public/yeongsanpo-world.json').read_text(encoding='utf8'))
for boat in w['boats']:
 with bpy.data.libraries.load(str(R/f'outputs/yeongsanpo-v79/{boat["id"]}-detail-v79.blend'),link=False) as (a,b):
  b.objects=[n for n in a.objects if not n.startswith(('Camera','Sun','Fill'))]
 h=boat['home'];transform=Matrix.Translation((h['x'],-h['z'],boat['waterY']))@Matrix.Rotation(h['yaw'],4,'Z')
 for o in b.objects:
  if o and o.type=='MESH':s.collection.objects.link(o);o.matrix_world=transform@o.matrix_world
s.world=bpy.data.worlds.new('Crop review daylight');s.world.use_nodes=True
s.world.node_tree.nodes['Background'].inputs[0].default_value=(.6,.76,.84,1)
s.world.node_tree.nodes['Background'].inputs[1].default_value=.65
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.2;sun.rotation_euler=(.4,-.42,-.7);sun.data.angle=.09
bpy.ops.object.camera_add();camera=bpy.context.object;s.camera=camera;camera.data.lens=35;camera.data.clip_end=2500
camera.location=(100,-620,510);camera.rotation_euler=(Vector((0,-40,0))-camera.location).to_track_quat('-Z','Y').to_euler()
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=16;s.view_settings.view_transform='AgX'
s.render.resolution_x=1280;s.render.resolution_y=820;s.render.resolution_percentage=100
s.render.filepath=str(O/'yeongsanpo-crop-review.png');bpy.ops.render.render(write_still=True)
print('CROP_REVIEW_COMPLETE',flush=True)
