import bpy,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];revision='v69' if '--final' in sys.argv else 'v67';O=R/('outputs/quality-'+revision)
for label,path in [('before',R/'outputs/quality-v58/bitgaram-park-crowns-v58.blend'),('after',O/('bitgaram-access-'+revision+'.blend'))]:
 if revision=='v69' and label=='before':continue
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene
 for o in list(s.objects):
  if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.2;sun.data.angle=.16;sun.rotation_euler=(.5,-.6,-.8)
 s.world=bpy.data.worlds.new('Access review daylight');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.56,.68,.81,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.6
 s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=24;s.render.resolution_x=1200;s.render.resolution_y=800;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.view_settings.exposure=.3
 bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.lens=42;cam.data.clip_end=2000
 for name,position,aim in [('access-overview',(95,-190,100),(5,-50,15)),('slide-gallery',(8,-59,15.6),(-2,-35,15))]:
  if label=='before' and name=='slide-gallery':continue
  out=O/(name+'-'+label+'.png')
  if out.exists():raise RuntimeError('Review image preserved')
  cam.location=position;cam.rotation_euler=(Vector(aim)-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(out);bpy.ops.render.render(write_still=True);print('RENDER',out.name,flush=True)
