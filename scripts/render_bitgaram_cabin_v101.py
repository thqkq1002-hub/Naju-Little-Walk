import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/bitgaram-v101'
bpy.ops.wm.open_mainfile(filepath=str(O/'bitgaram-monorail-v101.blend'));s=bpy.context.scene
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1100;s.render.resolution_y=800;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('Cabin daylight');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.60,.70,.78,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.75
bpy.ops.object.light_add(type='AREA',location=(4,-4,7));light=bpy.context.object;light.data.energy=950;light.data.shape='DISK';light.data.size=5
bpy.ops.object.camera_add(location=(5,-7,4));c=bpy.context.object;s.camera=c;c.data.lens=48;c.rotation_euler=(Vector((0,0,1.3))-c.location).to_track_quat('-Z','Y').to_euler()
s.view_settings.view_transform='AgX';s.render.filepath=str(O/'cabin-after.png');bpy.ops.render.render(write_still=True)
