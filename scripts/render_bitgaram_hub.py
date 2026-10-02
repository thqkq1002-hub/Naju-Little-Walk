"""A static Blender aerial with projected clickable sign positions, not a giant walkable city."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/bitgaram'
data=json.loads((ROOT/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf-8'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;g=MuseumGeometry(s,(0,0),0)
g.box('ground',0,-1,0,4300,1,3700,'#aab79b',record=False)
pins=[]
landmarks={'656235304':('bitgaram-park','호수공원 · 전망대',34),'594386007':('bitgaram-kepco','한국전력 본사',154),'1065747586':('bitgaram-kentech','KENTECH',18)}
for way in data['ways']:
    t=way['tags'];pts=way['points'];x=sum(p[0] for p in pts)/len(pts);z=sum(p[1] for p in pts)/len(pts)
    if abs(x)>1800 or z>1200 or z<-1700:continue
    if t.get('natural')=='water' and pts[0]==pts[-1]:g.polygon('lake_'+way['id'],pts,-.2,.2,'#467f87')
    if t.get('building'):
        mark=landmarks.get(way['id']);level=t.get('building:levels','');hh=float(t.get('height',0)) if t.get('height','').replace('.','').isdigit() else 0
        h=mark[2] if mark else hh or (float(level)*3 if level.replace('.','').isdigit() else 18)
        g.polygon('building_'+way['id'],pts,0,17 if way['id']=='594386007' else h,'#d9ddcf' if mark else '#a6b3b1')
        if mark:pins.append(dict(id=mark[0],label=mark[1],position=[x,h,z]))
        if mark and mark[0]=='bitgaram-kepco':
            g.box('narrow_tower',x,85,z,49,137,38,'#a9bcc1',record=False)
            for y in range(5,151,7):
                g.box('tower_window_band',x,y,z+19,49,3.8,.2,'#557f89',record=False)
    elif t.get('highway') in ['primary','secondary','tertiary','residential','service']:
        for a,b in zip(pts,pts[1:]):g.segment('road',a,b,14 if t['highway']!='service' else 6,.035,'#d4d7cf',record=False)
    elif t.get('highway') in ['footway','path'] and abs(x)<250 and abs(z)<250:
        for a,b in zip(pts,pts[1:]):g.segment('park_path',a,b,2,.04,'#e0d4b5',record=False)
# A low hill and readable circular tower distinguish the park at overview scale.
bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=1,location=g.bp(0,0,0));o=bpy.context.object;o.name='Baemesan_estimated';o.scale=(110,125,17);o.data.materials.append(g.mat('#67814c'))
g.polygon('tower_disc',[(15*math.cos(i*math.tau/48),12*math.sin(i*math.tau/48)) for i in range(48)],30,5,'#eceddb')
bpy.ops.object.light_add(type='SUN',location=(0,0,1800));o=bpy.context.object;o.data.energy=2.5;o.rotation_euler=(.55,-.35,-.5)
s.world=bpy.data.worlds.new('Map daylight');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[1].default_value=.65
bpy.ops.object.camera_add(location=g.bp(1500,2450,2700));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=3700;cam.data.clip_end=7000;cam.rotation_euler=(Vector(g.bp(200,0,-50))-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
s.render.engine='BLENDER_EEVEE_NEXT';s.render.resolution_x=1800;s.render.resolution_y=1400;s.render.resolution_percentage=100
bpy.context.view_layer.update()
for pin in pins:
    p=world_to_camera_view(s,cam,Vector(g.bp(*pin.pop('position'))));pin['x']=round(p.x*100,3);pin['y']=round((1-p.y)*100,3)
(ROOT/'public/bitgaram-overview.json').write_text(json.dumps(dict(pins=pins,source=data['source']),ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'bitgaram-overview.blend'))
s.render.filepath=str(ROOT/'public/bitgaram-overview.png');bpy.ops.render.render(write_still=True)
print(pins)
