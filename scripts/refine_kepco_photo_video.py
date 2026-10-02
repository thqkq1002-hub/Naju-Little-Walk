"""Refine KEPCO finishes from press photographs and the 2022 Bloomberg preview."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
root=Path(__file__).resolve().parents[1];out=root/'outputs/bitgaram/bitgaram-kepco-photo-video.blend'
if out.exists():raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-kepco-campus-detail.blend'))
g=MuseumGeometry(bpy.context.scene,(0,0),0)
# Thin horizontal joints and broad light vertical piers seen in the front elevation footage.
for o in list(bpy.data.objects):
    if o.name.startswith(('tower_vertical_fin','tower_storey','campus_tower_side_mullion','campus_tower_side_storey')):bpy.data.objects.remove(o,do_unlink=True)
for side in [-24.25,14.25]:
    for i in range(15):
        x=-15+3.4*i
        g.box('video_vertical_pier',x,85.5,side,.7 if i%3==0 else .28,137,.45,'#dce0d7',record=False)
    for y in range(20,153,4):g.box('video_floor_joint',9,y,side,49,.105,.10,'#a8b8b8',record=False)
    for x in [-13.4,-3.2,7,17.2,27.4]:
        for y in range(22,145,8):g.box('video_spandrel',x,y,side,2.8,.55,.05,'#6b868d',record=False)
for side in [-15.75,33.75]:
    for z in range(-23,15,3):g.box('video_side_pier',side,85.5,z,.28,137,.44,'#d0d8d2',record=False)
    for y in range(20,153,4):g.box('video_side_joint',side,y,-5,.10,.10,38,'#a8b8b8',record=False)
# Dark rooftop louver cap and parapet detailing, without changing the tower collision volume.
for x in range(-14,34,2):g.box('video_crown_louver',x,155.1,-23.98,.08,2.1,.13,'#667c80',record=False)
for z in range(-23,15,2):g.box('video_crown_side_louver',-15.48,157,z,.12,4.7,.08,'#667c80',record=False)
# Circular red brand marker beside existing lettering, modeled rather than using a photograph.
o=g.mesh('video_brand_mark',[(1.7*math.cos(i*math.tau/48),146+1.7*math.sin(i*math.tau/48),14.65) for i in range(48)],[tuple(range(48))],'#bd443e')
o.location.x=-11
for o in bpy.data.objects:
    if o.name=='central_tower':o.data.materials[0]=g.mat('#76969e')
# Existing lobby back wall receives the tall, light panels and dark joints visible at 00:09.
wpath=root/'public/bitgaram-kepco-world.json';world=json.loads(wpath.read_text(encoding='utf-8'))
wall=next(s for s in world['solids'] if s['name']=='public_lobby_back_wall');p=wall['footprint'];back=max(q[1] for q in p)
for x in range(-45,46,6):g.box('video_lobby_wall_joint',x,3.7,back+.012,.045,7.25,.02,'#626b69',record=False)
for x in [-15,-9]:
    g.box('video_lobby_display_frame',x,1.9,back+.10,4.8,2.8,.13,'#73817b',record=False)
    g.box('video_lobby_display_panel',x,1.9,back+.18,4.5,2.55,.04,'#dfdfd2',record=False)
g.label('KEPCO Smart Grid',-12,3.65,back+.20,10,.4,color='#466777')
g.label('스마트 에너지',-15,2.55,back+.22,4,.28,color='#42666a')
g.label('전력과 일상',-9,2.55,back+.22,4,.28,color='#42666a')
for x in [-16.3,-15.4,-14.5,-13.6]:
    g.box('video_exhibit_diagram',x,1.65,back+.23,.35,.55+(x+16.3)*.15,.025,'#7d9f92',record=False)
# Entrance metal reveals and canopy seams, no reduction of the existing doorway.
ex,ez=world['spawn']['x'],world['spawn']['z']-9
for dx in [-3.2,3.2]:g.box('video_entry_trim',ex+dx,2.9,ez+.10,.18,5.8,.25,'#cad0c7',record=False)
for dx in [-2,-1,0,1,2]:g.box('video_canopy_seam',ex+dx,3.625,ez+1.6,.02,.015,3.5,'#596f72',record=False)
# Three flagstaffs are visible at 00:26. Their location here is estimated beside the entry.
for i in range(3):
    x,z=ex+24+i*3,ez+15
    g.tube('video_flagstaff',(x,0,z),(x,10-i*.5,z),.055,'#aebbb4',n=10)
    g.box('video_flagstaff_base',x,.12,z,.45,.24,.45,'#c4c6b9',record=False)
    g.collider('video_flagstaff',[(x-.22,z-.22),(x+.22,z-.22),(x+.22,z+.22),(x-.22,z+.22)],0,10)
    if i==0:
        g.mesh('video_kepco_flag',[(x,9.5,z),(x+2.1,9.35,z+.2),(x+2.1,8.1,z+.2),(x,8.3,z)],[(0,1,2,3)],'#ebece3')
        g.label('KEPCO',x+1,8.85,z+.25,1.7,.26,color='#3b6075')
world['solids']+=g.solids
world['provenance']['videoReference']='Bloomberg / Getty 1439937245, filmed 2022-11-07; front, lobby at 00:09 and podium/flagstaffs at 00:26 observed.'
wpath.write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
s=bpy.context.scene;s.camera.location=g.bp(155,130,300);s.camera.rotation_euler=(Vector(g.bp(5,72,0))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=40
bpy.ops.wm.save_as_mainfile(filepath=str(out))
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/bitgaram-kepco.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
s.render.filepath=str(root/'outputs/bitgaram/kepco-photo-video-review.png');bpy.ops.render.render(write_still=True)
