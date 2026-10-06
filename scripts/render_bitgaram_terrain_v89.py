"""Render the preserved v83 and new v89 sources for a terrain review."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/terrain-v89'
build=json.loads((R/'knowledge/sources/bitgaram/terrain-v89/build.json').read_text(encoding='utf8'))
for revision,source,upper,lower in [('before',R/'outputs/monorail-v83/bitgaram-park-monorail-v83.blend',16,6.22),('after',R/build['output'],build['upperModelHeight'],build['lowerModelHeight'])]:
 if '--after-only' in sys.argv and revision=='before':continue
 bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
 scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=24
 scene.world=bpy.data.worlds.new('Terrain review daylight');scene.world.use_nodes=True
 scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.58,.73,.80,1)
 scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
 bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.3;sun.rotation_euler=(.5,-.6,-.7);sun.data.angle=.10
 bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.lens=36;camera.data.clip_end=2500
 scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.2
 scene.render.resolution_x=1200;scene.render.resolution_y=760;scene.render.resolution_percentage=100
 # A fixed aerial camera reveals the changed relief without zoom exaggeration.
 views=[('aerial',(-150,-220,158),(0,-52,28))]
 if revision=='after':views.append(('walk',(0,-23,upper+1.72),(10,-115,lower+2)))
 for name,pos,aim in views:
  camera.location=pos;camera.rotation_euler=(Vector(aim)-camera.location).to_track_quat('-Z','Y').to_euler()
  for o in scene.objects:
   lod=o.get('vegetation_lod')
   if lod:
    near=(o.location-camera.location).length<o.get('vegetation_distance',64)
    o.hide_render=(lod=='near')!=near
  scene.render.filepath=str(O/(name+'-'+revision+'.png'));bpy.ops.render.render(write_still=True)
 print('REVIEW_RENDER',revision,flush=True)
