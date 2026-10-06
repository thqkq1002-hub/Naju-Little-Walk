"""Preserved Blender revisions: photographed riverfront finishes and small joinery.

All surface maps are original. Mapped footprints, stairs, doors and boat navigation
envelopes remain unchanged. The unmeasured fixtures are documented interpretations.
"""
import bpy,bmesh,math,json,struct,gzip,hashlib,random,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/yeongsanpo-v79';O.mkdir(exist_ok=True)
T=R/'assets/yeongsanpo-v79/materials'
keys=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['yeongsanpo','yeongsanpo-history','yeongsanpo-literature','najuho','wanggeonho']
def linear(rgb):return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb)
def srgb(rgb):return tuple(12.92*v if v<.0031308 else 1.055*v**(1/2.4)-.055 for v in rgb)
class Frame:
    def __init__(self,x=0,z=0,a=0):self.x=x;self.z=z;self.a=a
    def bp(self,x,y,z):c,s=math.cos(self.a),math.sin(self.a);return (self.x+x*c-z*s,-self.z-x*s-z*c,y)
class Batch:
    def __init__(self,name,mat):self.name=name;self.mat=mat;self.v=[];self.f=[];self.uv=[]
    def add(self,v,f,uv=None):
        n=len(self.v);self.v.extend(v);self.f.extend(tuple(n+i for i in p) for p in f)
        self.uv.extend(uv or [(0,0)]*len(v))
    def box(self,fr,x,y,z,w,h,d):
        v=[fr.bp(xx,yy,zz) for yy in [y-h/2,y+h/2] for xx,zz in [(x-w/2,z-d/2),(x+w/2,z-d/2),(x+w/2,z+d/2),(x-w/2,z+d/2)]]
        self.add(v,[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])
    def tube(self,fr,a,b,r,n=8):
        a,b=Vector(fr.bp(*a)),Vector(fr.bp(*b));axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
        if u.length<.001:u=axis.cross(Vector((1,0,0)))
        u.normalize();v=axis.cross(u)
        self.add([tuple(p+r*(math.cos(i*math.tau/n)*u+math.sin(i*math.tau/n)*v)) for p in [a,b] for i in range(n)],[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]+[tuple(reversed(range(n))),tuple(range(n,2*n))])
    def finish(self,leaf=False,shadow=True):
        if not self.v:return
        m=bpy.data.meshes.new(self.name);m.from_pydata(self.v,[],self.f);m.materials.append(self.mat);m.update()
        bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
        ob=bpy.data.objects.new(self.name,m);bpy.context.scene.collection.objects.link(ob)
        ob['source_class']='Photo-observed feature; original geometry and surface maps; detailed dimensions inferred'
        ob['no_shadow']=not shadow
        if leaf:
            lay=m.uv_layers.new(name='LeafUV')
            for p in m.polygons:
                p.use_smooth=True
                for i in p.loop_indices:lay.data[i].uv=self.uv[m.loops[i].vertex_index]
            ob['no_receive_shadow']=True
        else:uv(ob,1)
        return ob
def uv(ob,scale=1):
    m=ob.data;lay=m.uv_layers.active or m.uv_layers.new(name='PhysicalUV_v79')
    for p in m.polygons:
        axis=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=axis]
        for i in p.loop_indices:
            pt=ob.matrix_world@m.vertices[m.loops[i].vertex_index].co;lay.data[i].uv=(pt[axes[0]]*scale,pt[axes[1]]*scale)
def kind_for(name):
    n=name.lower()
    if n=='mapped_river_water':return 'water'
    if any(v in n for v in ['tatami_mat','tatami_cloth','tatami_edge']):return 'tatami'
    if any(v in n for v in ['sail','rope','halyard','straw','canopy','awning']):return 'canvas'
    if any(v in n for v in ['wood','timber','plank','deck','handrail','mast','boat_hull','cabin_wall','beam','rafter','lattice','door_panel','door_leaf','window_stile','window_rail','case_shelf','bookcase','chair','stair_tread','balcony_floor','veranda']):return 'wood'
    if any(v in n for v in ['brick','samhwa_front_wall','samhwa_alley_wall']):return 'brick'
    if any(v in n for v in ['roof','tile_rib','tile_course']):return 'roof'
    if any(v in n for v in ['paving','paver','stepping','gravel']):return 'pavers'
    if any(v in n for v in ['road','parking','apron']):return 'asphalt'
    if any(v in n for v in ['concrete','masonry','retaining','lighthouse','kerb','curb','slab','granite','memorial','stone','floor_dock_stair']):return 'concrete'
    if any(v in n for v in ['photo-building','osm-building','wall','plaster','warehouse','house','pillar']):return 'plaster'
    if any(v in n for v in ['pane','glass','window_recess','reflection']):return 'glass'
    return None
def make_mat(kind,old=None,color=None):
    if color is None:
        if old.name.startswith('Museum_') and old.name[7:13] and any(n.type=='TEX_IMAGE' for n in old.node_tree.nodes):
            try:rgb=tuple(int(old.name[7+i:9+i],16)/255 for i in [0,2,4]);color=linear(rgb)
            except ValueError:color=old.diffuse_color[:3]
        else:color=old.diffuse_color[:3]
    if kind=='water':color=linear((.27,.36,.25))
    key=(kind,tuple(round(v/.018)*.018 for v in color))
    if key in cache:return cache[key]
    m=bpy.data.materials.new('Y79_'+str(kind)+'_'+str(len(cache)));cache[key]=m;m.use_nodes=True
    m.diffuse_color=(*color,1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=m.diffuse_color
    bs.inputs['Roughness'].default_value=.84;bs.inputs['Metallic'].default_value=0
    if kind=='glass':
        bs.inputs['Roughness'].default_value=.17;bs.inputs['Metallic'].default_value=.20
        bs.inputs['Coat Weight'].default_value=.35
    elif kind:
        for suffix,target in [('color','Base Color'),('roughness','Roughness'),('normal','Normal')]:
            im=bpy.data.images.load(str(T/f'{kind}-{suffix}.png'),check_existing=True);im.colorspace_settings.name='sRGB' if suffix=='color' else 'Non-Color'
            node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=im
            if suffix=='color':
                mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*color,1)
                m.node_tree.links.new(node.outputs['Color'],mix.inputs[1]);m.node_tree.links.new(mix.outputs['Color'],bs.inputs[target])
            elif suffix=='normal':
                normal=m.node_tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.8 if kind=='water' else .45
                m.node_tree.links.new(node.outputs['Color'],normal.inputs['Color']);m.node_tree.links.new(normal.outputs['Normal'],bs.inputs[target])
            else:m.node_tree.links.new(node.outputs['Color'],bs.inputs[target])
    if kind=='water':m['no_shadow']=True;bs.inputs['Coat Weight'].default_value=.35
    return m
def smooth_tower(ob):
    for p in ob.data.polygons:p.use_smooth=abs(p.normal.z)<.7
def details_outdoor():
    fr=Frame(-143,130,-.337);metal=make_mat(None,color=linear((.31,.33,.30)));wood=make_mat('wood',color=linear((.39,.30,.20)));stone=make_mat('concrete',color=linear((.76,.75,.65)))
    detail=Batch('v79_wharf_joinery_and_fasteners',metal);coping=Batch('v79_wharf_coping_and_gauge',stone)
    # Formwork seams on the photographed cast concrete body; no added beacon.
    for yy in np.arange(-5.95,-1.05,.45):
        for j in range(64):
            a,b=j*math.tau/64,(j+1)*math.tau/64
            detail.tube(fr,(math.cos(a)*1.005,yy,-2.3+math.sin(a)*1.005),(math.cos(b)*1.005,yy,-2.3+math.sin(b)*1.005),.006,5)
    for xx in [-.28,.28]:coping.box(fr,xx,1.20,-3.923,.065,.86,.06)
    for yy in [.78,1.62]:coping.box(fr,0,yy,-3.923,.62,.07,.06)
    # Small plate fixings follow existing rail posts; all stay within their footprints.
    for xx in range(-39,40,5):
        detail.tube(fr,(xx-.24,-6.02,-28.3),(xx+.24,-6.02,-28.3),.045)
        for dx in [-.12,.12]:detail.box(fr,xx+dx,-6.383,-28.3,.045,.03,.045)
    for xx in [30,42]:
        for j in range(12):
            yy=-j/11*6.4;zz=-j/11*14
            detail.box(fr,xx,yy+.015,zz,.17,.032,.17)
    for xx in np.arange(-42,29,1.8):detail.box(fr,xx,1.005,0,.085,.045,.085)
    # Deck screws at board crossings, batched and without expensive tiny shadows.
    for xx in np.arange(-40,40,.5):
        for zz in [-4,-14,-25]:detail.box(fr,float(xx),-6.390,zz,.023,.004,.023)
    coping.box(fr,-6,.026,0,73,.06,.52)
    for xx in np.arange(-42,30,.70):detail.box(fr,float(xx),.059,0,.009,.003,.50)
    detail.finish(shadow=False);coping.finish()
    # Sills, outward lips and hinges are placed on the already traced shop frontage.
    configs=json.loads((R/'knowledge/sources/yeongsanpo-riverfront-detail.json').read_text(encoding='utf-8'))
    # Shape refinements derive from the actual imported front-pane edges below.
    sill=Batch('v79_shop_sill_drip_edges',metal);hinge=Batch('v79_shop_door_hardware',metal)
    count=0
    for ob in list(bpy.context.scene.objects):
        if 'riverfront_' not in ob.name or not ('_pane' in ob.name or '_pull' in ob.name):continue
        pts=[ob.matrix_world@Vector(v) for v in ob.bound_box];lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)])
        if '_pane' in ob.name and hi.z-lo.z>.8:
            # Infer horizontal edge direction from the longest edge of the pane.
            vertices=[ob.matrix_world@v.co for v in ob.data.vertices];horizontal=[(a,b) for a in vertices for b in vertices if abs(a.z-b.z)<.01 and (a-b).length>.3]
            if not horizontal:continue
            a,b=max(horizontal,key=lambda e:(e[0]-e[1]).length);a=Vector((a.x,a.y,lo.z-.06));b=Vector((b.x,b.y,lo.z-.06))
            u=(b-a).normalized();normal=Vector((-u.y,u.x,0));sill.add([tuple(p) for p in [a+normal*.03,b+normal*.03,b+normal*.11,a+normal*.11]],[(0,1,2,3)]);count+=1
    sill.finish(shadow=False)
    return dict(deckFasteners=480,shopDripEdges=count,lighthouseFormworkCourses=11)
def vegetation():
    im=bpy.data.images.load(str(T/'leaf-color.png'),check_existing=True);m=bpy.data.materials.new('Y79_leaf_cutout');m.use_nodes=True
    m.diffuse_color=(.13,.27,.055,1);m.surface_render_method='DITHERED';bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.93
    tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);m.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
    leaf=Batch('v79_layered_leaf_canopies',m);rng=random.Random(79);old=[];cards=0
    for o in list(bpy.context.scene.objects):
        if o.type!='MESH' or not any(s in o.name for s in ['tree_foliage','tree_crown','small_leaf_cluster','pot_foliage','pruned_tree_crown','bamboo_crown']):continue
        pts=[o.matrix_world@Vector(v) for v in o.bound_box];lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)]);c=(lo+hi)/2;extent=(hi-lo)/2
        # Keep photographed planting envelopes; replace only the faceted green masses.
        n=max(18,min(210,int(extent.length*90)))
        for i in range(n):
            az=rng.uniform(0,math.tau);zz=rng.uniform(-1,1);r=math.sqrt(1-zz*zz)*rng.uniform(.3,1)
            p=c+Vector((math.cos(az)*extent.x*r,math.sin(az)*extent.y*r,zz*extent.z*.85))
            l=max(.06,min(.48,extent.length*.14))*rng.uniform(.8,1.5);w=l*.50
            normal=Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(.1,1))).normalized();u=normal.cross(Vector((0,0,1))).normalized();v=normal.cross(u)
            vv=[p-u*w-v*l,p+u*w-v*l,p+u*w+v*l,p-u*w+v*l]
            leaf.add([tuple(p) for p in vv],[(0,1,2,3)],[(0,0),(1,0),(1,1),(0,1)]);cards+=1
        old.append(o)
    bpy.data.batch_remove(old);leaf.finish(leaf=True,shadow=False)
    return dict(replacedCrownMasses=len(old),leafCards=cards)
def small_joinery(key):
    wood=make_mat('wood',color=linear((.39,.28,.17)));metal=make_mat(None,color=linear((.33,.34,.32)))
    b=Batch('v79_joinery_pegs_and_fasteners',metal);trim=Batch('v79_wood_joint_insets',wood);fr=Frame();count=0
    for o in list(bpy.context.scene.objects):
        if o.type!='MESH' or not any(s in o.name for s in ['rail_post','timber_post','frame_post','mast','library_case_side','veranda_frame_post']):continue
        if any(s in o.name for s in ['seam','stay','rope','flag']):continue
        pts=[o.matrix_world@Vector(v) for v in o.bound_box];lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)])
        c=(lo+hi)/2
        if hi.z-lo.z<.5:continue
        for z in [lo.z+.15,hi.z-.13]:
            for x in [lo.x-.005,hi.x+.005]:b.tube(fr,(x,z,-c.y),(x+.01,z,-c.y),.019,8);count+=1
    b.finish(shadow=False)
    return dict(joineryFixings=count)
def group_scene():
    """Spatial/material batches keep editable objects, UVs and cutaway flags in source.

    Use numpy arrays rather than one operator join for 20,000 objects. Transparency
    is kept in individual panes; roof-hide flags and small-shadow flags stay separate.
    """
    groups={};keep=[]
    for o in list(bpy.context.scene.objects):
        if o.type!='MESH' or len(o.data.materials)!=1:continue
        if any(s in o.name for s in ['riverfront_pitched_roof_','yeongsanpo_lighthouse','_shop_pane','literature_sealed_upper_gable','literature_closed_side_clerestory','literature_clerestory_closed_wall','veranda_window_head_wall','veranda_transom_infill','window_garden_boundary_wall','cutaway_ceiling_mesh','timeline_lightbox_','boat_white_sail_screen','attic_white_bookshelf','onggi_straw_bundle','ceiling_projector']):continue
        m=o.data.materials[0]
        if not m:continue
        bs=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
        alpha=bs.inputs['Alpha'].default_value if bs else 1
        if alpha<.99 and m.name!='Y79_leaf_cutout':keep.append(o);continue
        # Two coarse spatial zones improve off-screen culling without thousands of draws.
        world=o.matrix_world@Vector(o.bound_box[0]);zone=(math.floor(world.x/160),math.floor(world.y/160)) if key=='yeongsanpo' else (0,0)
        role='walk-floor_street_pavers' if o.name.startswith('walk-floor_street_pavers') else ''
        tag=(m.name,bool(o.get('hide_in_overview')),bool(o.get('no_shadow')),bool(o.get('no_receive_shadow')),zone,role)
        groups.setdefault(tag,[]).append(o)
    reduced=0
    for tag,obs in groups.items():
        if len(obs)<2:continue
        verts=[];faces=[];loopsuv=[];smooth=[];offset=0
        for o in obs:
            data=o.data;verts.extend(tuple(o.matrix_world@v.co) for v in data.vertices)
            layer=data.uv_layers.active
            for p in data.polygons:
                faces.append(tuple(offset+i for i in p.vertices));smooth.append(p.use_smooth)
                loopsuv.extend(tuple(layer.data[i].uv) if layer else (0,0) for i in p.loop_indices)
            offset+=len(data.vertices)
        name=f'{tag[5] or "v79"}_batch_{tag[0]}_{tag[4][0]}_{tag[4][1]}'
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.materials.append(obs[0].data.materials[0]);mesh.update()
        lay=mesh.uv_layers.new(name='PhysicalUV_v79');lay.data.foreach_set('uv',np.array(loopsuv,dtype=np.float32).ravel())
        for p,s in zip(mesh.polygons,smooth):p.use_smooth=s
        ob=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(ob)
        if tag[1]:ob['hide_in_overview']=True
        if tag[2]:ob['no_shadow']=True
        if tag[3]:ob['no_receive_shadow']=True
        ob['merged_sources']=len(obs);bpy.data.batch_remove(obs);reduced+=len(obs)-1
    return reduced
stats=[]
for key in keys:
    cache={};source=R/f'outputs/palette-v51/{key}-color-v51.blend';before=hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
    before_objects=sum(o.type=='MESH' for o in scene.objects);textured=0
    for o in list(scene.objects):
        if o.type!='MESH' or o.name.startswith('label_'):continue
        kind=kind_for(o.name)
        # Keep original exhibition graphics and photographic-floor interpretations.
        if any(s in o.name for s in ['original_port','interpretation','book_cover','book_spine','river_finish','food','onggi']):continue
        if not kind:continue
        if kind=='glass' and any(m.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value<.99 for m in o.data.materials if m and m.use_nodes):continue
        if o.name=='yeongsanpo_lighthouse':smooth_tower(o)
        for i,m in enumerate(list(o.data.materials)):
            if m:o.data.materials[i]=make_mat(kind,m)
        uv(o,{'wood':.65,'water':.38,'roof':.5,'plaster':.7,'tatami':1.0}.get(kind,1));textured+=1
        if kind=='water':o['no_shadow']=True;o['no_receive_shadow']=True
    detail=details_outdoor() if key=='yeongsanpo' else small_joinery(key)
    if key in ['yeongsanpo','yeongsanpo-literature']:detail.update(vegetation())
    scene['research_revision']='Yeongsanpo v79; MUCH 2018 photographs, KTO photographs, JNFC 2025 photographs; inferred fine dimensions'
    # Save the unmerged editable scene first; original sources are never overwritten.
    bpy.ops.file.pack_all();editable=O/f'{key}-detail-v79.blend';bpy.ops.wm.save_as_mainfile(filepath=str(editable))
    merged=group_scene();after_objects=sum(o.type=='MESH' for o in scene.objects)
    for o in scene.objects:
        if o.type=='MESH':
            coords=np.empty(len(o.data.vertices)*3,dtype=np.float32);o.data.vertices.foreach_get('co',coords);o.data.vertices.foreach_set('co',np.round(coords*10000)/10000);o.data.update()
    target=O/f'{key}-web-v79.glb'
    bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_active_scene=True,export_extras=True,export_cameras=False,export_lights=False,export_image_format='WEBP',export_image_quality=88,export_apply=True)
    raw=target.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[20+n:]
    for m in doc.get('materials',[]):
        bm=bpy.data.materials.get(m.get('name',''))
        if bm and bm.name.startswith('Y79_'):
            if 'baseColorTexture' in m.get('pbrMetallicRoughness',{}):m['pbrMetallicRoughness']['baseColorFactor']=list(bm.diffuse_color) if bm.name!='Y79_leaf_cutout' else [1,1,1,1]
            if bm.name=='Y79_leaf_cutout':m['alphaMode']='MASK';m['alphaCutoff']=.42;m['doubleSided']=True
    encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
    raw=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary;packed=gzip.compress(raw,9,mtime=0)
    if len(packed)>25*1024*1024:raise RuntimeError('Hosting model budget exceeded')
    for suffix,payload in [('.glb',raw),('.glb.gz',packed)]:
        p=R/f'public/models/{key}{suffix}';temp=p.with_suffix(p.suffix+'.v79.tmp');temp.write_bytes(payload);temp.replace(p)
    if hashlib.sha256(source.read_bytes()).hexdigest()!=before:raise RuntimeError('Original source unexpectedly changed')
    stats.append(dict(model=key,sourceSha256=before,beforeObjects=before_objects,webObjects=after_objects,merged=merged,texturedObjects=textured,compressedBytes=len(packed),triangles=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'] if 'indices'in p),materials=len(doc.get('materials',[])),images=len(doc.get('images',[])),detail=detail))
    (O/f'{key}-stats.json').write_text(json.dumps(stats[-1],indent=2),encoding='utf-8');print('V79_RESULT',json.dumps(stats[-1]),flush=True)
(O/'build-summary.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
