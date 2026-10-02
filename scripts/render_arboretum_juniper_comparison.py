"""Same eye-level comparison with consistent daylight and source palette."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v62'
report=json.loads((R/'knowledge/sources/arboretum/juniper-quality-v62.json').read_text(encoding='utf-8'))
def pt(s,y,t):return Vector((-475+.98*s-.2*t,50-.2*s-.98*t,y))
for label,path in [('before',R/report['source']),('after',R/report['output'])]:
 bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene
 for o in list(scene.objects):
  if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.3;sun.data.angle=.15;sun.rotation_euler=(.6,-.5,-.8)
 scene.world=bpy.data.worlds.new('Juniper comparison daylight');scene.world.use_nodes=True;bg=scene.world.node_tree.nodes['Background'];bg.inputs[0].default_value=(.56,.68,.81,1);bg.inputs[1].default_value=.6
 scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=24;scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
 scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.3
 bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.clip_end=2000
 for name,loc,aim,lens in [('juniper',(120,1.7,-175),(205,2.5,-175),35),('oval',(245,1.7,-175),(270,3.4,-169),45),('garden',(181,1.7,54),(164,.75,42),38)]:
  cam.location=pt(*loc);cam.rotation_euler=(pt(*aim)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
  scene.render.filepath=str(O/(name+'-'+label+'.png'));bpy.ops.render.render(write_still=True);print('JUNIPER COMPARISON',label,name,flush=True)
