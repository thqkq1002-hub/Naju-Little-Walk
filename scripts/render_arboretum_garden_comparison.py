"""Same eye-level cameras for the original and new garden revision."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v61'
report=json.loads((R/'knowledge/sources/arboretum/garden-quality-v61.json').read_text(encoding='utf-8'))
def pt(s,y,t):return Vector((-475+.98*s-.2*t,50-.2*s-.98*t,y))
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
inputs=[('before',R/report['source']),('after',R/report['output'])]
if args:inputs=[('rounded',R/args[0])]
for label,path in inputs:
 bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene
 for mat in bpy.data.materials:
  if mat.name not in report['palette_snapshot']:continue
  current=report['palette_snapshot'][mat.name];pbr=current.get('pbrMetallicRoughness',{});rgba=pbr.get('baseColorFactor',[1,1,1,1]);mat.diffuse_color=rgba
  bsdf=mat.node_tree.nodes.get('Principled BSDF') if mat.use_nodes else None
  if bsdf:bsdf.inputs['Base Color'].default_value=rgba;bsdf.inputs['Roughness'].default_value=pbr.get('roughnessFactor',1)
 for o in list(scene.objects):
  if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
 bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.0;sun.data.angle=.16;sun.rotation_euler=(.6,-.5,-.8)
 scene.world=bpy.data.worlds.new('Garden daylight comparison');scene.world.use_nodes=True;bg=scene.world.node_tree.nodes['Background'];bg.inputs[0].default_value=(.56,.68,.81,1);bg.inputs[1].default_value=.6
 scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=24;scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
 scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.3
 bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.clip_end=2000
 for name,loc,aim,lens in [('roses',(181,1.7,54),(164,.75,42),38),('blossom',(181,1.3,41),(175,.8,42),58),('playground',(248,3,-43),(234,1.7,-62),43)]:
  cam.location=pt(*loc);cam.rotation_euler=(pt(*aim)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
  scene.render.filepath=str(O/(name+'-'+label+'.png'));bpy.ops.render.render(write_still=True);print('GARDEN COMPARISON',label,name,flush=True)
