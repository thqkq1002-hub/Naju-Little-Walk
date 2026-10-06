"""Render the actual rigged model in an authored animation pose, without editing source."""
from pathlib import Path
from mathutils import Vector
import bpy, sys

root = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--') + 1:]
character, clip = args[0], args[1] if len(args) > 1 else 'Idle'
version = args[2] if len(args)>2 and args[2].startswith('v') else 'v5'
base = root / 'assets/npc/meshy71-baedoli-clean-20261002' if character=='baedoli' and version=='v6' else root / 'assets/npc/meshy71-rigged-20261002' / character
bpy.ops.wm.open_mainfile(filepath=str(base / f'{character}-rigged-{version}.blend'))
rig = bpy.data.objects[character + '_GuideRig']
for track in rig.animation_data.nla_tracks: track.mute = True
rig.animation_data.action = None if clip=='Rest' else bpy.data.actions[clip]
if clip=='Rest':
    for pb in rig.pose.bones:pb.rotation_quaternion=(1,0,0,0)
scene = bpy.context.scene
if len(args) > 2 and args[2] == 'auto-normals':
    data = bpy.data.objects[character+'_Body'].data
    data.normals_split_custom_set([(0,0,0)] * len(data.loops))
scene.frame_set(40 if clip != 'Greeting' else 38)
height = {'baedoli':1.2,'beodeuri':1.65,'hongdoli':1.05,'teacher':1.72}[character]
target = Vector((0, 0, height * .51))
scene.render.engine = 'BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples = 32
scene.render.resolution_x = 800;scene.render.resolution_y = 1000;scene.render.resolution_percentage = 100
scene.world = bpy.data.worlds.new('ReviewWorld');scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.75,.79,.83,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .6
scene.view_settings.view_transform = 'AgX'
for name, position, energy in [('Key',(-3,-4,4),600),('Fill',(3,-2,3),350),('Rim',(1,3,4),400)]:
    light = bpy.data.lights.new(name,'AREA');light.energy = energy;light.size = 4
    ob = bpy.data.objects.new(name,light);scene.collection.objects.link(ob);ob.location = position
    ob.rotation_euler = (target-ob.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.005))
floor = bpy.context.object
material = bpy.data.materials.new('NeutralFloor');material.diffuse_color = (.74,.76,.78,1);floor.data.materials.append(material)
camera = bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));scene.collection.objects.link(camera)
camera.location = (.2*height,-4*height,1.1*height);camera.rotation_euler = (target-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type = 'ORTHO'
mesh = bpy.data.objects[character+'_Body']
width = mesh.dimensions.x
camera.data.ortho_scale = max(height*1.18,width*1.5)
scene.camera = camera
scene.render.image_settings.file_format = 'PNG';scene.render.filepath = str(base/f'{character}-{clip.lower()}-preview.png')
bpy.ops.render.render(write_still=True)
print('RIGGED_PREVIEW_COMPLETE '+character+' '+clip)
