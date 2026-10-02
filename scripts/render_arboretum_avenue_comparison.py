"""Same mapped-road eye-level camera before and after planting correction."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];revision='v66' if '--budget' in sys.argv else 'v65' if '--road-finish' in sys.argv else 'v64' if '--clear-crossings' in sys.argv else 'v63';O=R/('outputs/quality-'+revision);name='juniper-budget-v66' if revision=='v66' else 'juniper-road-v65' if revision=='v65' else 'juniper-avenue-'+revision;report=json.loads((R/('knowledge/sources/arboretum/'+name+'.json')).read_text(encoding='utf-8'))
world=json.loads((R/report.get('world_output','outputs/quality-v65/naju-arboretum-world-v65.json')).read_text(encoding='utf-8'));arrival=world['arrivals']['juniper'];origin=Vector((arrival['x'],-arrival['z'],1.7));forward=Vector((-math.sin(arrival['yaw']),math.cos(arrival['yaw']),0))
for label,path in [('before',R/'outputs/quality-v61/naju-arboretum-garden-v61-soft.blend'),('after',R/report['output'])]:
 if revision=='v66' and label=='before':continue # v65 comparison already records the identical before view.
 bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene
 for o in list(scene.objects):
  if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.3;sun.data.angle=.15;sun.rotation_euler=(.6,-.5,-.8)
 scene.world=bpy.data.worlds.new('Mapped avenue daylight');scene.world.use_nodes=True;bg=scene.world.node_tree.nodes['Background'];bg.inputs[0].default_value=(.56,.68,.81,1);bg.inputs[1].default_value=.6
 scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=24;scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.3
 bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.clip_end=2000;cam.data.lens=35;cam.location=origin;cam.rotation_euler=(forward+Vector((0,0,.01))).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(O/('avenue-'+label+'.png'));bpy.ops.render.render(write_still=True);print('AVENUE COMPARISON',label,flush=True)
