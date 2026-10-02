"""Guarded v72: original bark/forest-ground grain and curved grass ribbons.
Photo reference: shwkdrns5353.tistory.com/2035, visited 2025-06-25.
Materials and low vegetation only; mapped ground, facilities and world stay exact.
"""
import bpy,bmesh,math,random,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v72';O.mkdir(parents=True,exist_ok=True)
source=R/'outputs/quality-v71/deudeulgang-pine-crowns-v71.blend';target=O/'deudeulgang-surfaces-v72.blend'
if target.exists():raise RuntimeError('Editable revision already exists; preserved')
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
def fingerprint(o):
    m=o.data;v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v)
    ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids)
    lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
    return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
grass=[o for o in scene.objects if o.name.startswith('grass_tuft') and o.type=='MESH']
protected={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o not in grass}
transforms={o.name:[v for row in o.matrix_world for v in row] for o in grass}
def texture(name,pixels,base=None):
    n=pixels.shape[0];im=bpy.data.images.new(name,width=n,height=n,alpha=False);im.pixels.foreach_set(pixels.astype(np.float32).ravel());im.pack()
    mat=base.copy() if base else bpy.data.materials.new(name);mat.name=name;mat.use_nodes=True
    bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.96
    for link in list(mat.node_tree.links):
        if link.to_node==bs and link.to_socket.name in ['Base Color','Alpha']:mat.node_tree.links.remove(link)
    bs.inputs['Alpha'].default_value=1
    node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;mat.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
    return mat
def noise(n,g,seed):
    rng=np.random.default_rng(seed);cells=rng.random((g,g));axis=np.arange(n)*g/n;a=np.floor(axis).astype(int);t=axis-a;t=t*t*(3-2*t)
    x=a[None,:];y=a[:,None];tx=t[None,:];ty=t[:,None]
    return (cells[y,x]*(1-tx)+cells[y,(x+1)%g]*tx)*(1-ty)+(cells[(y+1)%g,x]*(1-tx)+cells[(y+1)%g,(x+1)%g]*tx)*ty
n=512;yy,xx=np.mgrid[0:n,0:n]
barks=[]
for i,base in enumerate([(.28,.255,.205),(.43,.29,.18)]):
    x=xx/n*28;y=yy/n*7;rng=np.random.default_rng(7200+i);jitter=rng.random((7,28,2))*.7+.15
    first=np.full((n,n),100.);second=first.copy()
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            gx=np.floor(x).astype(int)+dx;gy=np.floor(y).astype(int)+dy;shift=jitter[gy%7,gx%28]
            d=(x-gx-shift[:,:,0])**2+(y-gy-shift[:,:,1])**2
            second=np.where(d<first,first,np.minimum(second,d));first=np.minimum(first,d)
    fissure=np.clip((second-first)*8,.45,1);grain=.72+.33*noise(n,80,7300+i)+.12*noise(n,24,7400+i)
    pixels=np.ones((n,n,4));
    for k,c in enumerate(base):pixels[:,:,k]=c*grain*fissure
    barks.append(texture('Authored_pine_fine_bark_v72_'+str(i),pixels))
for me in {o.data for o in scene.objects if o.name.startswith(('old_pine_','distant_pine_')) and o.type=='MESH'}:
    me.materials[0]=barks[0];me.materials[1]=barks[1]

# One world-planar original soil/low-groundcover texture, continuous across the
# existing grove and former flat polygon litter patches. No photo is embedded.
mix=np.clip((noise(n,5,7211)-.40)*3,0,1);grain=.84+.2*noise(n,96,7212)
pixels=np.ones((n,n,4));earth=(.33,.295,.215);green=(.24,.34,.17)
for k in range(3):pixels[:,:,k]=(earth[k]*(1-mix)+green[k]*mix)*grain
floor=texture('Authored_forest_soil_groundcover_v72',pixels)
surfaces=[]
for o in scene.objects:
    if o.type!='MESH' or not o.name.startswith(('ground_floor_pine_grove','detail_forest_litter_#827052','detail_forest_litter_#877959','detail_forest_litter_#898064')):continue
    o.data.materials.clear();o.data.materials.append(floor)
    uv=o.data.uv_layers.active or o.data.uv_layers.new(name='Ground_UV')
    for p in o.data.polygons:
        for j in p.loop_indices:
            v=o.matrix_world@o.data.vertices[o.data.loops[j].vertex_index].co
            uv.data[j].uv=(v.x/7,v.y/7)
    surfaces.append(o.name)

old=grass[0].data;vs=[];fs=[];mis=[];rng=random.Random(7261)
for i in range(7):
    a=rng.random()*math.tau;h=rng.uniform(.16,.47);lean=rng.uniform(.08,.25);width=rng.uniform(.012,.026);origin=Vector((rng.uniform(-.12,.12),rng.uniform(-.12,.12),0));side=Vector((-math.sin(a),math.cos(a),0));rows=[]
    for t in [0,.33,.68,.91]:
        c=origin+Vector((math.cos(a)*lean*t*t,math.sin(a)*lean*t*t,h*t));w=width*(1-t)**.75
        rows.append((len(vs),len(vs)+1));vs.extend([tuple(c-side*w),tuple(c+side*w)])
    for p,q in zip(rows,rows[1:]):fs.append((p[0],p[1],q[1],q[0]));mis.append(i%2)
    tip=len(vs);vs.append(tuple(origin+Vector((math.cos(a)*lean,math.sin(a)*lean,h))));fs.append((rows[-1][0],rows[-1][1],tip));mis.append(i%2)
me=bpy.data.meshes.new('Curved_understory_grass_v72');me.from_pydata(vs,[],fs);me.update()
for mat in old.materials:me.materials.append(mat)
for p,mi in zip(me.polygons,mis):p.material_index=mi;p.use_smooth=True
for o in grass:o.data=me;o['surface_detail_revision']='Curved low-grass blades v72; original placement'
bpy.context.view_layer.update()
assert all(fingerprint(bpy.data.objects[name])==h for name,h in protected.items())
world_sha=hashlib.sha256((R/'public/deudeulgang-world.json').read_bytes()).hexdigest()
report={'source':str(source.relative_to(R)),'output':str(target.relative_to(R)),'protected_geometry_hashes':protected,'grass_transforms':transforms,'ground_surfaces':surfaces,'world_sha256':world_sha,'original_textures':3,'reference':'https://shwkdrns5353.tistory.com/2035','reference_visit':'2025-06-25','reference_published':'2025-06-26','limitation':'Bark grain, groundcover colours and grass geometry are photo-informed estimates, not copied imagery or surveyed plants.'}
(R/'knowledge/sources/deudeulgang/surfaces-v72.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(O/'deudeulgang-v72.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
print('SURFACES EXPORTED',len(protected),len(grass),surfaces,flush=True)
