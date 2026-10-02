"""Matched cameras before/after the pine crown and background revision."""
import bpy,math,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];revision='v72' if '--surfaces' in sys.argv else 'v71' if '--fine' in sys.argv else 'v70';O=R/('outputs/quality-'+revision)
after=O/('deudeulgang-surfaces-v72.blend' if revision=='v72' else 'deudeulgang-pine-crowns-'+revision+'.blend')
for label,path in [('before',R/'outputs/deudeulgang/deudeulgang-pine-grove-v55-finished.blend'),('after',after)]:
    if label=='before' and revision!='v70':continue
    bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene;cam=scene.camera
    scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=16
    scene.render.resolution_x=1100;scene.render.resolution_y=720;scene.render.resolution_percentage=100
    for name,pos,aim,lens in [('grove',(34,1.72,-120),(12,9,-25),25),('river',(-28,1.72,15),(-290,36,70),26),('overview',(115,94,340),(-70,4,20),34)]:
        cam.location=(pos[0],-pos[2],pos[1]);target=Vector((aim[0],-aim[2],aim[1]))
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
        scene.render.filepath=str(O/(name+'-'+label+'.png'));bpy.ops.render.render(write_still=True)
