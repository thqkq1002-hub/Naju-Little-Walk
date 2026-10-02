"""Same cameras for current source and candidate; no saved model mutations."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v75';after='--after' in sys.argv
path=O/'bitgaram-shore-v75.blend' if after else R/'outputs/quality-v69/bitgaram-access-v69.blend'
bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene
for o in list(s.objects):
 if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.2;sun.data.angle=.16;sun.rotation_euler=(.5,-.6,-.8)
s.world=bpy.data.worlds.new('Shore review daylight');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.56,.68,.81,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.6
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=24;s.render.resolution_x=1100;s.render.resolution_y=720;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.view_settings.exposure=.3
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.clip_end=2200
def point(x,y,z):return (x,-z,y)
for name,pos,aim,lens in [('shore-overview',(-420,310,460),(0,0,10),35),('west-bank',(-230,12,100),(-265,0,130),38),('east-bank',(180,10,175),(203,0,202),38)]:
 out=O/(name+('-after.png' if after else '-before.png'))
 if out.exists():raise RuntimeError('Review image preserved')
 cam.location=point(*pos);cam.rotation_euler=(Vector(point(*aim))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;s.render.filepath=str(out);bpy.ops.render.render(write_still=True);print('RENDER',out.name,flush=True)
