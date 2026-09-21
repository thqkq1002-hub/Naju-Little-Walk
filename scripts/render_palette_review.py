"""Visual review of representative Blender palette scenes, not a site thumbnail."""
import bpy,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/palette-v51'
views=[('bitgaram-kepco',(350,-430,300),(0,0,0)),('bitgaram-kentech',(95,-115,82),(0,0,0)),('bitgaram-park',(-310,-300,270),(0,-35,0)),('bogam-museum',(75,-90,70),(0,-8,0)),('dasi-neighborhood',(320,-350,290),(0,25,0)),('bitgaram-overview',(-900,-1500,2000),(0,0,0))]
for name,position,aim in views:
 bpy.ops.wm.open_mainfile(filepath=str(O/(name+'-color-v51.blend')));scene=bpy.context.scene
 # Actual palette values are read directly from the saved full-scene Blender revisions.
 for o in scene.objects:
  if o.get('vegetation_lod')=='far':o.hide_render=True
 bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.4;sun.rotation_euler=(.5,-.6,-.7);sun.data.angle=.12
 scene.world=bpy.data.worlds.new('Palette review daylight');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.56,.68,.81,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
 bpy.ops.object.camera_add(location=position);cam=bpy.context.object;scene.camera=cam;cam.rotation_euler=(Vector(aim)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=36;cam.data.clip_end=12000
 scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=16;scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.6
 scene.render.resolution_x=800;scene.render.resolution_y=540;scene.render.resolution_percentage=100;scene.render.filepath=str(O/(name+'-review.png'));bpy.ops.render.render(write_still=True)
 print('PALETTE REVIEW',name,flush=True)
