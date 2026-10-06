"""Same cameras/light for v74 and v87; no saved scene changes."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v87'
after='--after' in sys.argv;label='after' if after else 'before'
source=O/'naju-arboretum-canopy-v87-r4.blend' if after else R/'outputs/quality-v74/naju-arboretum-tree-crowns-v74.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
def pt(s,y,t):return Vector((-475+.98*s-.2*t,50-.2*s-.98*t,y))
for o in list(scene.objects):
 if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.3;sun.data.angle=.15;sun.rotation_euler=(.6,-.5,-.8)
scene.world=bpy.data.worlds.new('Canopy comparison daylight');scene.world.use_nodes=True;bg=scene.world.node_tree.nodes['Background'];bg.inputs[0].default_value=(.56,.68,.81,1);bg.inputs[1].default_value=.6
scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=24;scene.render.resolution_x=1100;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.3
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.clip_end=2000
shots=[('avenue',(75,1.7,0),(125,4,0),27),('forest',(239,1.7,-37),(255,5,-37),30),('crowns',(235,24,-10),(230,5,-60),32)]
for name,loc,aim,lens in shots:
 cam.location=pt(*loc);cam.rotation_euler=(pt(*aim)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
 scene.render.filepath=str(O/(name+'-'+label+'.png'));bpy.ops.render.render(write_still=True);print('CANOPY RENDER',name,label,flush=True)
