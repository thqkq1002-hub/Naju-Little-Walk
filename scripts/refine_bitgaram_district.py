"""OSM-aligned district finish; preserve earlier editable Blender revisions."""
import bpy,bmesh,sys,json,math,random
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/bitgaram/bitgaram-district-detail.blend'
if OUT.exists():raise RuntimeError('Existing artist revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/bitgaram/bitgaram-overview-kepco.blend'))
ways=json.loads((ROOT/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf-8'))['ways']
class Batch(MuseumGeometry):
    def __init__(self):super().__init__(bpy.context.scene,(0,0),0);self.parts={}
    def mesh(self,name,verts,faces,color,group=None,smooth=False):
        vs,fs=self.parts.setdefault(color,([],[]));offset=len(vs)
        vs.extend(self.bp(*p) for p in verts);fs.extend(tuple(i+offset for i in f) for f in faces)
    def finish(self):
        for color,(vs,fs) in self.parts.items():
            m=bpy.data.meshes.new('district_'+color);m.from_pydata(vs,[],fs);m.update()
            bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
            o=bpy.data.objects.new('district_'+color,m);bpy.context.scene.collection.objects.link(o);m.materials.append(self.mat(color))
g=Batch();rng=random.Random(3391)
def inside(p,poly):
    x,z=p;hit=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:hit=not hit
    return hit
def centroid(p):return [sum(q[i] for q in p)/len(p) for i in [0,1]]
blocked=[w['points'] for w in ways if w['tags'].get('building') or w['tags'].get('natural')=='water']
campus=next(w['points'] for w in ways if w['id']=='508052678')
counts={'buildings':0,'trees':0,'roadSegments':0,'greenAreas':0}
for w in ways:
    t=w['tags'];p=w['points'];cx,cz=centroid(p)
    if abs(cx)>1800 or cz>1200 or cz<-1700:continue
    obj=bpy.data.objects.get('building_'+w['id'])
    if t.get('building') and obj:
        # Existing mapped heights and footprints remain unchanged.
        h=max((obj.matrix_world@v.co).z for v in obj.data.vertices)
        kind=t['building'];palette=['#d5d7cc','#d9d3c3','#c4cec9'] if kind=='apartments' else ['#c7c5b9','#b9c6c6','#d3ccbb']
        obj.data.materials.clear();obj.data.materials.append(g.mat(palette[int(w['id'])%len(palette)]))
        for a,b in zip(p,p[1:]):
            length=math.dist(a,b)
            if length<5:continue
            ux,uz=(b[0]-a[0])/length,(b[1]-a[1])/length
            # Windows stop short of corners. A facade band is schematic, not a surveyed window count.
            aa=(a[0]+ux*1.2,a[1]+uz*1.2);bb=(b[0]-ux*1.2,b[1]-uz*1.2)
            for y in range(3,int(h)-1,4):g.segment('window',aa,bb,.24,1.5,'#66838b',base=y,record=False)
            g.segment('parapet',a,b,.38,.5,'#a4afa9',base=h,record=False)
            if length>18:
                for d in range(7,int(length)-3,9):
                    x,z=a[0]+ux*d,a[1]+uz*d
                    g.box('pier',x,h/2,z,.48,h,.48,'#e0dfd3',record=False)
        if inside((cx,cz),p):g.box('roof_plant',cx,h+1.2,cz,3,2.4,3,'#949f9c',record=False)
        counts['buildings']+=1
    if t.get('highway') in ['secondary','tertiary','residential'] and not inside((cx,cz),campus):
        width=22 if t['highway']=='secondary' else 16 if t['highway']=='tertiary' else 9
        for a,b in zip(p,p[1:]):
            length=math.dist(a,b)
            if length<3:continue
            ux,uz=(b[0]-a[0])/length,(b[1]-a[1])/length
            g.segment('asphalt',a,b,width,.018,'#8e9a97',base=.055,record=False)
            for side in [-1,1]:
                aa=(a[0]-uz*(width/2+1)*side,a[1]+ux*(width/2+1)*side);bb=(b[0]-uz*(width/2+1)*side,b[1]+ux*(width/2+1)*side)
                g.segment('sidewalk',aa,bb,1.8,.024,'#c8c6b4',base=.078,record=False)
            if width>=16:
                for d in range(4,int(length)-3,14):
                    g.segment('lane',(a[0]+ux*d,a[1]+uz*d),(a[0]+ux*(d+5),a[1]+uz*(d+5)),.32,.006,'#eee2b4',base=.078,record=False)
                for d in range(15,int(length)-12,36):
                    for side in [-1,1]:
                        x,z=a[0]+ux*d-uz*(width/2+3)*side,a[1]+uz*d+ux*(width/2+3)*side
                        if any(inside((x,z),poly) for poly in blocked) or inside((x,z),campus):continue
                        h=rng.uniform(4.5,7);r=rng.uniform(2.3,3.3)
                        g.box('trunk',x,h/3,z,.5,h*.66,.5,'#837d62',record=False)
                        verts=[(x,h+r,z),(x,h-r*.7,z)]+[(x+math.cos(i*math.tau/8)*r,h,z+math.sin(i*math.tau/8)*r) for i in range(8)]
                        faces=[(0,2+i,2+(i+1)%8) for i in range(8)]+[(1,2+(i+1)%8,2+i) for i in range(8)]
                        g.mesh('tree',verts,faces,['#6b8551','#7a915b','#60815b'][counts['trees']%3]);counts['trees']+=1
            counts['roadSegments']+=1
    if p[0]==p[-1] and math.hypot(cx,cz)>650 and (t.get('leisure') in ['park','garden','pitch']):
        # Use the mapped polygons, not arbitrary rectangular lawns.
        color='#93aa79' if t.get('leisure')!='pitch' else '#88a388'
        g.polygon('mapped_green',p[:-1],.032,.005,color);counts['greenAreas']+=1
g.finish()
sc=bpy.context.scene;sc.camera.location=g.bp(1350,2050,2250);sc.camera.rotation_euler=(Vector(g.bp(180,0,-60))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=3200
sc.render.resolution_x=1500;sc.render.resolution_y=1100;sc.render.resolution_percentage=80
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
sc.render.filepath=str(ROOT/'outputs/bitgaram/district-detail-review.png');bpy.ops.render.render(write_still=True)
# Join static meshes for transport only. The saved artist file retains individual editable objects.
groups={}
for o in list(sc.objects):
    if o.type=='MESH' and not o.parent and len(o.data.materials)==1 and not o.modifiers:
        groups.setdefault(o.data.materials[0].name,[]).append(o)
for material,objects in groups.items():
    if len(objects)<2:continue
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join()
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/bitgaram-overview.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
(ROOT/'work/district-counts.json').write_text(json.dumps(counts),encoding='utf-8');print(counts,flush=True)
