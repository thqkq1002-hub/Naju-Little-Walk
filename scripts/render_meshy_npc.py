import bpy, json, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/npc-meshy-20261002'
for key in ['baedoli','beodeuri','hongdoli','teacher']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(OUT/key/'meshy-original.glb'))
    ob=next(o for o in bpy.context.scene.objects if o.type=='MESH')
    for p in ob.data.polygons:p.use_smooth=True
    mat=bpy.data.materials.new('Neutral');mat.diffuse_color=(.55,.63,.65,1);mat.roughness=.78
    ob.data.materials.append(mat)
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE_NEXT'
    scene.eevee.taa_render_samples=24
    scene.render.resolution_x=700;scene.render.resolution_y=700;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('World');scene.world.color=(.5,.5,.5)
    scene.view_settings.view_transform='Standard'
    for name,pos,power,size in [('Key',(-2,-3,4),300,4),('Fill',(2,-1,1),150,3),('Rim',(1,3,2),200,3)]:
        ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size
        lo=bpy.data.objects.new(name,ld);scene.collection.objects.link(lo);lo.location=pos
        lo.rotation_euler=(-lo.location).to_track_quat('-Z','Y').to_euler()
    cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));scene.collection.objects.link(cam);scene.camera=cam
    cam.data.type='ORTHO';cam.data.ortho_scale=1.25
    for view,pos in [('front',(0,-3,0)),('side',(3,-.05,0))]:
        cam.location=pos;cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(OUT/key/f'raw-{view}.png')
        bpy.ops.render.render(write_still=True)
print('NPC raw renders complete')
