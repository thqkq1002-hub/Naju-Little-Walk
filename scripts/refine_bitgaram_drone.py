"""Drone-informed skyline and planting, with mapped footprints retained."""
import bpy,bmesh,json,math,random,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
root=Path(__file__).resolve().parents[1];out=root/'outputs/bitgaram/bitgaram-drone-detail.blend'
if out.exists():raise RuntimeError('Existing artist revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-district-detail.blend'))
ways=json.loads((root/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf-8'))['ways'];rng=random.Random(3616)
def inside(x,z,p):
    hit=False
    for a,b in zip(p,p[1:]+p[:1]):
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:hit=not hit
    return hit
class Batch(MuseumGeometry):
    def __init__(self):super().__init__(bpy.context.scene,(0,0),0);self.parts={}
    def mesh(self,name,verts,faces,color,group=None,smooth=False):
        vs,fs=self.parts.setdefault(color,([],[]));n=len(vs);vs.extend(self.bp(*p) for p in verts);fs.extend(tuple(i+n for i in f) for f in faces)
    def finish(self):
        for color,(vs,fs) in self.parts.items():
            m=bpy.data.meshes.new('drone_'+color);m.from_pydata(vs,[],fs);m.update();bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
            o=bpy.data.objects.new('drone_'+color,m);bpy.context.scene.collection.objects.link(o);m.materials.append(self.mat(color))
g=Batch();changes=[];trees=0
for w in ways:
    t=w['tags'];o=bpy.data.objects.get('building_'+w['id'])
    if not o or t.get('building')!='apartments' or t.get('height') or t.get('building:levels'):continue
    old=max((o.matrix_world@v.co).z for v in o.data.vertices)
    if old>30:continue
    p=w['points'];new=54.;delta=new-old
    for v in o.data.vertices:
        if v.co.z>1:v.co.z*=new/old
    # Move earlier roof finishes to the new roof; retain lower facade bands.
    for detail in [q for q in bpy.data.objects if q.type=='MESH' and q.name.startswith('district_')]:
        for v in detail.data.vertices:
            if old-.1<=v.co.z<=old+3 and inside(v.co.x,-v.co.y,p):v.co.z+=delta
    for a,b in zip(p,p[1:]):
        length=math.dist(a,b)
        if length<5:continue
        ux,uz=(b[0]-a[0])/length,(b[1]-a[1])/length
        for y in range(math.ceil(old)+2,int(new)-1,3):g.segment('upper_window',(a[0]+ux,a[1]+uz),(b[0]-ux,b[1]-uz),.25,1.35,'#78949e',base=y,record=False)
        for d in range(5,int(length)-2,8):g.box('upper_pier',a[0]+ux*d,(old+new)/2,a[1]+uz*d,.55,new-old,.55,'#e4e3d9',record=False)
    changes.append(dict(id=w['id'],old=old,estimatedHeight=new))
blocked=[w['points'] for w in ways if w['tags'].get('building') or w['tags'].get('natural')=='water']
roads=[(a,b) for w in ways if w['tags'].get('highway') in ['primary','secondary','tertiary','residential','service'] for a,b in zip(w['points'],w['points'][1:])]
def road_distance(x,z,a,b):
    dx,dz=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(z-a[1])*dz)/max(dx*dx+dz*dz,.001)));return math.hypot(x-a[0]-t*dx,z-a[1]-t*dz)
def tree(x,z):
    global trees
    h=rng.uniform(4,7);r=rng.uniform(2,3.7)
    g.box('trunk',x,h*.3,z,.42,h*.6,.42,'#796d53',record=False)
    vs=[(x,h+r*.8,z),(x,h-r*.8,z)]+[(x+math.cos(i*math.tau/8)*r,h,z+math.sin(i*math.tau/8)*r) for i in range(8)]
    g.mesh('crown',vs,[(0,2+i,2+(i+1)%8) for i in range(8)]+[(1,2+(i+1)%8,2+i) for i in range(8)],['#54744d','#6e8754','#82935f'][trees%3]);trees+=1
for w in ways:
    p=w['points'];t=w['tags'];cx=sum(q[0] for q in p)/len(p);cz=sum(q[1] for q in p)/len(p)
    if p[0]!=p[-1] or abs(cx)>1700 or not -1600<cz<1100:continue
    if t.get('landuse')=='residential':
        xmin,xmax=min(q[0] for q in p),max(q[0] for q in p);zmin,zmax=min(q[1] for q in p),max(q[1] for q in p)
        for _ in range(min(700,int((xmax-xmin)*(zmax-zmin)/170))):
            x,z=rng.uniform(xmin,xmax),rng.uniform(zmin,zmax)
            if inside(x,z,p) and not any(inside(x,z,b) for b in blocked) and not any(road_distance(x,z,a,b)<10 for a,b in roads):tree(x,z)
    if t.get('natural')=='water' and math.hypot(cx,cz)<850:
        # Small shoreline clumps stay on the land side of the mapped water outline.
        for a,b in zip(p,p[1:]):
            length=math.dist(a,b)
            if length<4:continue
            ux,uz=(b[0]-a[0])/length,(b[1]-a[1])/length
            for d in range(4,int(length),14):
                for side in [-1,1]:
                    x,z=a[0]+ux*d-uz*5*side,a[1]+uz*d+ux*5*side
                    if not any(inside(x,z,b) for b in blocked) and not any(road_distance(x,z,a,b)<8 for a,b in roads):tree(x,z);break
g.finish();s=bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=str(out))
s.render.filepath=str(root/'outputs/bitgaram/drone-detail-review.png');bpy.ops.render.render(write_still=True)
groups={}
for o in list(s.objects):
    if o.type=='MESH' and not o.parent and len(o.data.materials)==1 and not o.modifiers:groups.setdefault(o.data.materials[0].name,[]).append(o)
for mat,objects in groups.items():
    if len(objects)<2:continue
    with bpy.context.temp_override(active_object=objects[0],object=objects[0],selected_objects=objects,selected_editable_objects=objects):bpy.ops.object.join()
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/bitgaram-overview.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
(root/'work/drone-detail-counts.json').write_text(json.dumps(dict(heightEstimates=changes,trees=trees)),encoding='utf-8');print('DONE',len(changes),trees,flush=True)
