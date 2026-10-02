"""Consistent baseline/after eye-level and overhead comparisons, no source edits."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];revision='v74' if '--dense' in sys.argv else 'v73';O=R/('outputs/quality-'+revision);O.mkdir(parents=True,exist_ok=True)
after='--after' in sys.argv;label='after' if after else 'before'
path=O/('naju-arboretum-tree-crowns-'+revision+'.blend') if after else R/'outputs/quality-v66/naju-arboretum-juniper-budget-v66.blend'
bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene
def pt(s,y,t):return Vector((-475+.98*s-.2*t,50-.2*s-.98*t,y))
for o in list(scene.objects):
 if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.3;sun.data.angle=.15;sun.rotation_euler=(.6,-.5,-.8)
scene.world=bpy.data.worlds.new('Tree comparison daylight');scene.world.use_nodes=True;bg=scene.world.node_tree.nodes['Background'];bg.inputs[0].default_value=(.56,.68,.81,1);bg.inputs[1].default_value=.6
scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=24;scene.render.resolution_x=1100;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.3
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.clip_end=2000
for name,loc,aim,lens in [('avenue',(110,1.7,0),(170,8,0),27),('forest',(239,1.7,-37),(255,5,-37),30),('crowns',(235,20,-10),(230,5,-60),32)]:
 cam.location=pt(*loc);cam.rotation_euler=(pt(*aim)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
 scene.render.filepath=str(O/(name+'-'+label+'.png'));bpy.ops.render.render(write_still=True);print('TREE RENDER',name,label,flush=True)
