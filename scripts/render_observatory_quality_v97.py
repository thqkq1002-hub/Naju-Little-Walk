"""Fixed-camera before/after reviews and normal 1.72m eye-height panorama."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/relief-v96'
def setup():
    s=bpy.context.scene
    for engine in ['BLENDER_EEVEE','BLENDER_EEVEE_NEXT']:
        try:s.render.engine=engine;break
        except TypeError:pass
    s.render.resolution_x=1200;s.render.resolution_y=760;s.render.resolution_percentage=100
    s.view_settings.view_transform='AgX'
    w=bpy.data.worlds.new('Relief review daylight');w.use_nodes=True
    bg=next(n for n in w.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.55,.70,.8,1);bg.inputs[1].default_value=.7;s.world=w
    sky=s.objects.get('Neureoji93_original_sky_dome')
    if sky:sky.hide_render=True
    bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.3;sun.rotation_euler=(.5,-.6,-.7)
    bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.clip_end=30000
    return s,cam
def render(s,cam,file,eye,aim,lens=36):
    cam.location=(eye[0],-eye[2],eye[1]);target=Vector((aim[0],-aim[2],aim[1]))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
    for ob in s.objects:
        lod=ob.get('vegetation_lod')
        if lod:
            near=(ob.location-cam.location).length<ob.get('vegetation_distance',64)
            ob.hide_render=(lod=='near')!=near
    s.render.filepath=str(O/file);bpy.ops.render.render(write_still=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/quality-v97/neureoji-canopy-v97b.blend'))
s,c=setup();O=R/'outputs/quality-v97'
w=json.loads((R/'public/neureoji-world.json').read_text(encoding='utf8'))
render(s,c,'canopy-review.png',[-85,65,-105],[0,45,0],40)
a=w['arrivals']['top'];eye=[a['x'],a['height']+1.72,a['z']]
aim=[eye[0]-math.sin(a['yaw'])*1000,eye[1]+math.tan(a['pitch'])*1000,eye[2]-math.cos(a['yaw'])*1000]
render(s,c,'panorama-review.png',eye,aim,31)
