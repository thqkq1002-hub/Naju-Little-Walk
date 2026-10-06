"""Eye-level, scene-authored validation views; no borrowed exhibit photographs."""
import bpy,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/history-gallery-v91'
bpy.ops.wm.open_mainfile(filepath=str(O/'yeongsanpo-history-complete-v91c.blend'));s=bpy.context.scene
for o in list(s.objects):
    if o.type=='CAMERA':bpy.data.objects.remove(o,do_unlink=True)
s.world=bpy.data.worlds.new('Gallery review ambient');s.world.use_nodes=True
s.world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.40,.42,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.17
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=32;s.view_settings.view_transform='AgX'
s.render.resolution_x=1200;s.render.resolution_y=780;s.render.resolution_percentage=100
bpy.ops.object.camera_add();c=bpy.context.object;s.camera=c;c.data.lens=23;c.data.clip_end=100
views=[('entry',(-3,-7.1,1.68),(0,5,1.6)),('crafts',(-1,-5.9,1.65),(1.4,-8.3,1.25)),('food',(1.6,-2.3,1.68),(4.85,-3.8,1.26)),('boat',(-2,4.8,1.65),(0,8,1.65))]
for name,eye,target in views:
    c.location=eye;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(O/(name+'-review.png'));bpy.ops.render.render(write_still=True)
print('GALLERY_REVIEW_DONE',flush=True)
