"""Same camera/light review of the untouched source; preserve all artist files."""
import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v58'
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/palette-v51/bitgaram-park-color-v51.blend'))
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=32
scene.world=bpy.data.worlds.new('Park review daylight');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.56,.68,.81,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.4;sun.rotation_euler=(.5,-.6,-.7);sun.data.angle=.14
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.lens=32;camera.data.clip_end=3000
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.5
scene.render.resolution_x=1280;scene.render.resolution_y=800;scene.render.resolution_percentage=100
for name,position,aim in [('park-woodland',(0,-68,10),(18,-60,13)),('park-aerial',(-230,-260,200),(0,-25,10))]:
    output=O/(name+'-before.png')
    if output.exists():raise RuntimeError('Existing review image preserved')
    camera.location=position;camera.rotation_euler=(Vector(aim)-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(output);bpy.ops.render.render(write_still=True)
