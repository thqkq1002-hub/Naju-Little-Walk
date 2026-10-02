"""Same cameras and daylight for an untouched source and the new facade revision."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v60'
report=json.loads((R/'knowledge/sources/bitgaram/district-facade-v60.json').read_text(encoding='utf-8'))
apt=min((b for b in report['apartments'] if b['height']>40),key=lambda b:math.hypot(sum(p[0] for p in b['polygon'])/len(b['polygon'])-650,sum(p[1] for p in b['polygon'])/len(b['polygon'])-450))
cx=sum(p[0] for p in apt['polygon'])/len(apt['polygon']);cy=-sum(p[1] for p in apt['polygon'])/len(apt['polygon'])
views=[('district', (1250,-2150,1950),(200,50,0),35),('apartments',(cx-160,cy-230,135),(cx,cy,apt['height']*.42),43)]
for label,path in [('before',R/report['source']),('after',R/report['output'])]:
 bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene
 for mat in bpy.data.materials:
  current=report['palette_snapshot'].get(mat.name)
  if not current:continue
  pbr=current.get('pbrMetallicRoughness',{});rgba=pbr.get('baseColorFactor',[1,1,1,1]);mat.diffuse_color=rgba
  bsdf=mat.node_tree.nodes.get('Principled BSDF') if mat.use_nodes else None
  if bsdf:
   bsdf.inputs['Base Color'].default_value=rgba;bsdf.inputs['Roughness'].default_value=pbr.get('roughnessFactor',1);bsdf.inputs['Metallic'].default_value=pbr.get('metallicFactor',1)
 for obj in list(scene.objects):
  if obj.type=='LIGHT':bpy.data.objects.remove(obj,do_unlink=True)
 bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.5;sun.data.angle=.12;sun.rotation_euler=(.6,-.5,-.8)
 scene.world=bpy.data.worlds.new('Facade comparison daylight');scene.world.use_nodes=True;bg=scene.world.node_tree.nodes['Background'];bg.inputs[0].default_value=(.56,.68,.81,1);bg.inputs[1].default_value=.7
 bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.clip_end=12000
 scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=32
 scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.6
 scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
 for name,position,aim,lens in views:
  cam.location=position;cam.rotation_euler=(Vector(aim)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
  scene.render.filepath=str(O/f'{name}-{label}.png');bpy.ops.render.render(write_still=True)
  print('FACADE COMPARISON',label,name,apt['id'],flush=True)
