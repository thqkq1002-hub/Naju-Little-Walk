"""Read-only review renders from the separate Dasi revision."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/dasi-v80'
bpy.ops.wm.open_mainfile(filepath=str(O/'dasi-neighborhood-detail-v80.blend'));s=bpy.context.scene
for o in list(s.objects):
    if o.type in ['LIGHT','CAMERA']:bpy.data.objects.remove(o,do_unlink=True)
s.world=bpy.data.worlds.new('Dasi_review_sky');s.world.use_nodes=True
bg=s.world.node_tree.nodes['Background'];bg.inputs['Color'].default_value=(.63,.76,.85,1);bg.inputs['Strength'].default_value=.7
sun=bpy.data.lights.new('Review_sun','SUN');sun.energy=2.1;sun.angle=.075
ob=bpy.data.objects.new('Review_sun',sun);s.collection.objects.link(ob);ob.rotation_euler=(.5,-.4,-.6)
cam=bpy.data.cameras.new('Review_camera');co=bpy.data.objects.new('Review_camera',cam);s.collection.objects.link(co);s.camera=co;cam.lens=35;cam.clip_end=2000
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16;s.cycles.use_denoising=True
s.render.resolution_x=1200;s.render.resolution_y=780;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
views=[('front-blender-v80',[-45,8,32],[-17,3.6,-13]),('courtyard-blender-v80',[66,10,37],[0,1.8,12])]
for name,eye,target in views:
    co.location=(eye[0],-eye[2],eye[1]);co.rotation_euler=(Vector((target[0],-target[2],target[1]))-co.location).to_track_quat('-Z','Y').to_euler()
    for o in s.objects:
        if o.get('vegetation_lod'):
            near=(o.location-co.location).length<o.get('vegetation_distance',90)
            o.hide_render=not(near if o['vegetation_lod']=='near' else not near)
    s.render.filepath=str(O/f'{name}.png');bpy.ops.render.render(write_still=True)
