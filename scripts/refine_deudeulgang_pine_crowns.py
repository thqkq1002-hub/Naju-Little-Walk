"""Photo-informed pine crown layers and non-walkable wooded bank, guarded v70.

2025 Ohmynews photographs inform the habit, not measured dimensions or tree counts.
Existing roots, object transforms, mapped paths and collision JSON remain unchanged.
"""
import bpy, bmesh, math, random, json, hashlib, struct, sys, numpy as np
from pathlib import Path
from mathutils import Vector

R=Path(__file__).resolve().parents[1]
fine='--fine' in sys.argv;revision='v71' if fine else 'v70'
O=R/('outputs/quality-'+revision); O.mkdir(parents=True,exist_ok=True)
source=R/'outputs/deudeulgang/deudeulgang-pine-grove-v55-finished.blend'
target=O/('deudeulgang-pine-crowns-'+revision+'.blend')
if target.exists(): raise RuntimeError('Existing editable revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(source)); scene=bpy.context.scene

def fingerprint(o):
    m=o.data; v=np.empty(len(m.vertices)*3,np.float32); m.vertices.foreach_get('co',v)
    ids=np.empty(len(m.loops),np.int32); m.loops.foreach_get('vertex_index',ids)
    lengths=np.empty(len(m.polygons),np.int32); m.polygons.foreach_get('loop_total',lengths)
    return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()

changed={o.name for o in scene.objects if o.type=='MESH' and (o.name.startswith(('old_pine_','distant_pine_','background_wooded_ridge_')))}
protected={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o.name not in changed}
world_sha=hashlib.sha256((R/'public/deudeulgang-world.json').read_bytes()).hexdigest()

# An original opaque needle-grain texture keeps crowns visible at distance.
# Fine alpha sprays provide the fringes; they are never the sole canopy volume.
size=256; yy,xx=np.mgrid[0:size,0:size]; rr=np.random.default_rng(7001)
grain=.77+.22*rr.random((size,size))+.06*np.sin(xx*.43+yy*.69)
pixels=np.ones((size,size,4),np.float32)
for i,c in enumerate((.16,.285,.14) if fine else (.115,.235,.125)): pixels[:,:,i]=c*grain
im=bpy.data.images.new('Authored_pine_opaque_needle_grain_v70',width=size,height=size)
im.pixels.foreach_set(pixels.ravel()); im.pack()
mat=bpy.data.materials.new('Pine_layered_crown_opaque_v70'); mat.use_nodes=True
bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.94
tex=mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=im
mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])

meshes={o.data for o in scene.objects if o.name.startswith(('old_pine_','distant_pine_')) and o.type=='MESH'}
prototypes={}
for old in sorted(meshes,key=lambda m:m.name):
    far=old.name.endswith('_far'); seed=int(old.name.split('_')[1]); rng=random.Random(seed+7000)
    cards=[p for p in old.polygons if p.material_index==5]
    planes=2 if far else 3
    centers=[sum((old.vertices[i].co for i in cards[j].vertices),Vector())/4 for j in range(0,len(cards),planes)]
    assert len(centers)==228, (old.name,len(centers))
    mesh=old.copy(); mesh.name=old.name+'_layered_v70'
    bm=bmesh.new();bm.from_mesh(mesh)
    # Keep the authored wood and roots exactly. Replace the spherical spray silhouette.
    if not fine:bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index>=2],context='FACES')
    bm.to_mesh(mesh);bm.free()
    if fine:
        leafcards=[p for p in mesh.polygons if p.material_index==5]
        for j in range(0,len(leafcards),planes):
            center=centers[j//planes]
            for p in leafcards[j:j+planes]:
                for i in p.vertices:
                    v=mesh.vertices[i];d=v.co-center;v.co=center+Vector((d.x*1.10,d.y*1.10,d.z*.70))
    verts=[v.co[:] for v in mesh.vertices]; faces=[tuple(p.vertices) for p in mesh.polygons]
    mis=[p.material_index for p in mesh.polygons]; uvs=[]
    for p in mesh.polygons: uvs.append([tuple(mesh.uv_layers.active.data[i].uv) for i in p.loop_indices])
    mats=list(old.materials)+[mat]
    def face(ps,mi,uv=None):
        n=len(verts);verts.extend([tuple(p) for p in ps]);faces.append(tuple(range(n,n+len(ps))));mis.append(mi)
        uvs.append(uv or [(p[0]*.7,p[1]*.7) for p in ps])
    clumps=0
    for k,c in enumerate(centers):
        q=k%4
        if (far and q!=2) or (not far and q not in [1,3]): continue
        clumps+=1
        rx=rng.uniform(.77,1.26)*(1.2 if far else 1);ry=rng.uniform(.64,1.13)*(1.2 if far else 1);rz=rng.uniform(.22,.39)
        if fine:rx*=.40;ry*=.40;rz*=.52
        n=6 if far else 7; rings=[]
        for h,rad in [(-.55,.67),(0,1),(.55,.65)]:
            ring=[]
            for j in range(n):
                a=j*math.tau/n+seed*.1
                ring.append(c+Vector((math.cos(a)*rx*rad*rng.uniform(.9,1.10),math.sin(a)*ry*rad*rng.uniform(.9,1.10),h*rz+rng.uniform(-.045,.045))))
            rings.append(ring)
        for j in range(n):
            nxt=(j+1)%n
            face([c+Vector((0,0,-rz)),rings[0][nxt],rings[0][j]],6)
            for a,b in zip(rings,rings[1:]):face([a[j],a[nxt],b[nxt],b[j]],6)
            face([rings[-1][j],rings[-1][nxt],c+Vector((0,0,rz))],6)
        if not far and not fine:
            # Short frayed tips around the flattened volume, avoiding large crossed balls.
            for j in range(2):
                a=j*math.pi/2+seed*.31;u=Vector((math.cos(a)*rx*1.10,math.sin(a)*ry*1.10,0));v=Vector((0,0,rz*1.20))
                face([c-u-v,c+u-v,c+u+v,c-u+v],5,[(0,0),(1,0),(1,1),(0,1)])
    new=bpy.data.meshes.new(mesh.name+'_finished');new.from_pydata(verts,[],faces);new.update()
    for m in mats:new.materials.append(m)
    uv=new.uv_layers.new(name='Pine_UV')
    for p,mi,coords in zip(new.polygons,mis,uvs):
        p.material_index=mi;p.use_smooth=mi in [0,1,6]
        for i,co in zip(p.loop_indices,coords):uv.data[i].uv=co
    # Weld crown surface vertices for coherent smooth lighting, leaving wood untouched.
    bm=bmesh.new();bm.from_mesh(new)
    crownverts=set(v for f in bm.faces if f.material_index==6 for v in f.verts)
    bmesh.ops.remove_doubles(bm,verts=list(crownverts),dist=.00001)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(new);bm.free()
    new.calc_loop_triangles();prototypes[old]=new
    print('PINE PROTOTYPE',old.name,clumps,len(new.loop_triangles),flush=True)

for o in scene.objects:
    if o.type=='MESH' and o.data in prototypes:
        o.data=prototypes[o.data];o['pine_crown_revision']='Photo-informed upper branch layers '+revision

# Remove high-frequency height jitter responsible for the corrugated distant edge.
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def ridge_height(x,z):
    d=-x-194;edge=smooth(d/160)
    peaks=36+22*math.exp(-((z+220)/200)**2)+31*math.exp(-((z-270)/260)**2)
    rolls=5*math.sin(z/99+x/180)+2.5*math.cos(z/43-x/81)
    ends=1-smooth((abs(z)-585)/240);rear=1-smooth((d-400)/310)
    crowns=.36*math.sin(x*.15+math.sin(z*.12))*math.cos(z*.13)
    shore=math.exp(-((x+212)/14)**2)*(3.6+.4*math.sin(z*.11))
    return .15+ends*(edge*rear*(peaks+rolls+crowns)+shore)
for o in scene.objects:
    if o.name.startswith('background_wooded_ridge_'):
        for v in o.data.vertices:v.co.z=ridge_height(v.co.x,-v.co.y)
        o.data.update()

# A single opaque shoreline mesh joins the riverbank to the hillside.
# The west-bank collision boundary encloses this scenery; no new walking surface.
vs=[];fs=[];rng=random.Random(7040)
for j in range(120):
    z=-550+j*9.2+rng.uniform(-2.3,2.3);x=rng.uniform(-238,-206);c=Vector((x,-z,ridge_height(x,z)+rng.uniform(.3,1) if fine else ridge_height(x,z)+rng.uniform(1,2.2)))
    rx=rng.uniform(4,8);ry=rng.uniform(4,7);rz=rng.uniform(.7,1.4) if fine else rng.uniform(2,3.8);n=8;rows=[]
    for h,rad in [(-.7,.6),(0,1),(.6,.7)]:
        row=[]
        for k in range(n):
            a=k*math.tau/n;row.append(len(vs));vs.append(tuple(c+Vector((math.cos(a)*rx*rad,math.sin(a)*ry*rad,h*rz))))
        rows.append(row)
    top=len(vs);vs.append(tuple(c+Vector((0,0,rz))))
    for k in range(n):
        nxt=(k+1)%n
        for a,b in zip(rows,rows[1:]):fs.append((a[k],a[nxt],b[nxt],b[k]))
        fs.append((rows[-1][k],rows[-1][nxt],top))
me=bpy.data.meshes.new('West_bank_woodland_fringe_v70');me.from_pydata(vs,[],fs);me.update()
me.materials.append(bpy.data.materials['Background_mixed_woodland_texture'])
uv=me.uv_layers.new(name='Woodland_UV')
for p in me.polygons:
    p.use_smooth=True
    for i in p.loop_indices:
        v=me.vertices[me.loops[i].vertex_index].co;x,z=v.x,-v.y;uv.data[i].uv=((x*.94+z*.342)/145,(-x*.342+z*.94)/145)
o=bpy.data.objects.new('background_woodland_bank_fringe_v70',me);scene.collection.objects.link(o)
for k in ['background_only','no_shadow','no_receive_shadow','background_canopy']:o[k]=True

report={'source':str(source.relative_to(R)),'output':str(target.relative_to(R)),'changed_objects':sorted(changed),'protected_geometry_hashes':protected,'world_sha256':world_sha,'reference':'https://www.ohmynews.com/NWS_Web/View/at_pg.aspx?CNTN_CD=A0003156492','reference_visit':'2025-08-08','reference_published':'2025-08-18','shared_pine_prototypes':len(prototypes),'near_triangles':[len(m.loop_triangles) for old,m in prototypes.items() if old.name.endswith('_near')],'far_triangles':[len(m.loop_triangles) for old,m in prototypes.items() if old.name.endswith('_far')],'limitation':'Photo-informed crown habit and background only; tree positions, dimensions, bank shrubs and elevations are estimates; no source photographs embedded. v70 rejected as plate-like; v71 retains fine original needle sprays.'}
(R/('knowledge/sources/deudeulgang/pine-crowns-'+revision+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
bpy.context.view_layer.update();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(O/('deudeulgang-'+revision+'.glb')),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
print('PINE CROWNS EXPORTED',len(changed),len(protected),flush=True)
