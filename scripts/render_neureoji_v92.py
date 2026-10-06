"""Review current tower silhouette and panorama at 1.72m eye height above the deck."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/neureoji-v92';rev='e' if '--final' in sys.argv else 'b' if '--second' in sys.argv else 'a'
bpy.ops.wm.open_mainfile(filepath=str(O/('neureoji-v92'+rev+'.blend')));s=bpy.context.scene
w=json.loads((R/'public/neureoji-world.json').read_text(encoding='utf8'));B=w['spawn']['height'];top=w['topDeckHeightMetres']
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=32;s.view_settings.view_transform='AgX';s.render.resolution_x=1440;s.render.resolution_y=900;s.render.resolution_percentage=100
world=bpy.data.worlds.new('Reference daylight');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.67,.76,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7;s.world=world
data=bpy.data.lights.new('Review sun','SUN');data.energy=3;ob=bpy.data.objects.new('Review sun',data);s.collection.objects.link(ob);ob.rotation_euler=(.45,-.4,-.5)
bpy.ops.object.camera_add();c=bpy.context.object;s.camera=c;c.data.clip_end=7000
def render(name,eye,target,lens):
    c.location=(eye[0],-eye[2],eye[1]);c.rotation_euler=(Vector((target[0],-target[2],target[1]))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=lens
    s.render.filepath=str(O/(name+'-'+rev+'.png'));bpy.ops.render.render(write_still=True)
render('tower',[-22,B+15,28],[1,B+7,1],31)
render('entry',[3.2,B+1.72,14],[3.2,B+8,-2.4],22)
render('panorama',[-1.6,top+1.72,-3],[-1200,0,-1300],22)
print('NEUREOJI_REVIEW_'+rev,flush=True)
