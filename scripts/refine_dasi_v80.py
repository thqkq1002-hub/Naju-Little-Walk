"""Research refinement of a preserved Blender source, not a replacement generator.

OSM geometry and navigation are retained. Photos inform finishes and silhouettes;
small joints/vegetation are interpretations, not measured equipment or survey data.
"""
from pathlib import Path
import sys
exec(compile((Path(__file__).resolve().parent/'refine_yeongsanpo_v79.py').read_text(encoding='utf-8').split('stats=[]')[0],__file__,'exec'))
O=R/'outputs/dasi-v80';O.mkdir(exist_ok=True);T=R/'assets/dasi-v80/materials';key='dasi';cache={}
source=R/'outputs/palette-v51/dasi-neighborhood-color-v51.blend'
before=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
before_objects=sum(o.type=='MESH' for o in scene.objects)
base_make_mat=make_mat
def material(kind,color):
    m=base_make_mat(kind,color=linear(color));m.name=m.name.replace('Y79_','D80_');return m
def bounds(o):
    pts=[o.matrix_world@Vector(v) for v in o.bound_box]
    return Vector([min(v[i] for v in pts) for i in range(3)]),Vector([max(v[i] for v in pts) for i in range(3)])
def physical_uv(o,kind):
    lay=o.data.uv_layers.active or o.data.uv_layers.new(name='D80_metres')
    tile={'brick':(1.2,.56),'pavers':(1.2,1.2),'grass':(1.6,1.6),'bark':(.7,2),'wood':(.8,2.4)}.get(kind,(1.5,1.5))
    for p in o.data.polygons:
        normal=(o.matrix_world.to_3x3().inverted().transposed()@p.normal).normalized()
        tangent=Vector((-normal.y,normal.x,0)).normalized() if abs(normal.z)<.8 else Vector((1,0,0))
        for li in p.loop_indices:
            v=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
            lay.data[li].uv=(v.dot(tangent)/tile[0],(v.z if abs(normal.z)<.8 else v.y)/tile[1])
def kind(o,m):
    n=o.name.lower();s=m.name.lower()
    if n.startswith(('ivy','tree-crown')):return None
    if n.startswith('label') or any(k in n for k in ['school_name','school_round','book','chalk','flag','notice','welcome','exercise']):return None
    if n=='osm-building_963585634' or n.startswith('school-wall_'):return 'brick'
    if 'glass'in n or n.endswith('_pane') or n=='station_window':return 'glass'
    if 'tree-trunk'in n:return 'bark'
    if n.startswith(('ground_floor_school_lawn','ground_floor_south_grove','grove_floor','crop-row')):return 'grass'
    if n=='ground_floor_sport_court':return 'court'
    if n.startswith('parcel'):return 'grass' if any(k in s for k in ['89934d','adb77d','728655','7c8b5b','9ca769','879665']) else 'concrete'
    if n.startswith(('road_','ground_floor_school_parking','parking','station_apron')):return 'asphalt'
    if n.startswith(('road-edge','rail_','railhead','catenary')):return 'concrete' if 'sleeper'in n or 'edge'in n else None
    if any(k in n for k in ['gate_pier','gate_cap','gate_finial','centenary']):return 'granite'
    if any(k in n for k in ['roof','coping']):return 'roof'
    if n.startswith(('school_front_path','school_west_walk','school_grove_path','field_south_walk','entry_path','walk-floor_colonnade')):return 'pavers'
    if any(k in n for k in ['student_desk','reading_table','reading_chair','bench_seat','bench_back','library_case','door_leaf']):return 'wood'
    if 'window'in n or any(k in n for k in ['mullion','transom','drainpipe']):return None
    if any(k in n for k in ['ground','floor','foundation','court','platform']):return 'concrete'
    if any(k in n for k in ['building','wall','pink_stair','colonnade_pillar','canopy','clock_roof','west_front']):return 'plaster'
    return None
textured=0;shadow_fixes=0
for o in list(scene.objects):
    if o.type!='MESH':continue
    n=o.name.lower()
    # Thin coplanar roads/crop rows were incorrectly casting full shadow-map patterns.
    if n.startswith(('ground','parcel','crop-row','road','field_south_walk','school_front_path','school_west_walk','school_grove_path','entry_path','court_marking','walk-floor')) or any(k in n for k in ['mullion','transom','_seam','_rib','_sill','frame_side','frame_horizontal','_net','drainpipe']):
        o['no_shadow']=True;shadow_fixes+=1
    for i,m in enumerate(list(o.data.materials)):
        if not m:continue
        k=kind(o,m)
        if not k:continue
        bs=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
        if k=='glass' and bs and bs.inputs['Alpha'].default_value<.99:continue
        c=srgb(m.diffuse_color[:3])
        if k=='brick':c=(.56,.33,.27)
        if k=='grass':c=(.47,.56,.29) if 'lawn'in n else (.38,.47,.28)
        if k=='asphalt':c=(.40,.42,.41)
        if k=='pavers':c=(.70,.60,.45)
        if k=='glass':c=(.47,.59,.61)
        o.data.materials[i]=material(k,c);physical_uv(o,k);textured+=1
    if n=='roof_west_barrel':
        for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    if 'school_name'in n:o['no_shadow']=True
print('D80_MATERIALS',textured,flush=True)

def cutout(name):
    m=bpy.data.materials.new('D80_'+name+'_cutout');m.use_nodes=True;m.diffuse_color=(1,1,1,1);m.surface_render_method='DITHERED'
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.96
    im=bpy.data.images.load(str(T/f'{name}-color.png'),check_existing=True);tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
    m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);m.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
    return m
rng=random.Random(80);leaves=Batch('dasi_v80_leaf_canopies',cutout('leaf'));ivy=Batch('dasi_v80_ivy_leaves',cutout('ivy'))
branches=Batch('dasi_v80_tree_branches',material('bark',(.34,.27,.18)))
fr=Frame();old=[];cards=0;ivy_cards=0
def card(batch,p,u,v,w,l):
    batch.add([tuple(q) for q in [p-u*w-v*l,p+u*w-v*l,p+u*w+v*l,p-u*w+v*l]],[(0,1,2,3)],[(0,0),(1,0),(1,1),(0,1)])
for o in list(scene.objects):
    if o.type!='MESH' or not o.name.startswith(('tree-crown','ivy_clump')):continue
    lo,hi=bounds(o);c=(lo+hi)/2;e=(hi-lo)/2;is_ivy=o.name.startswith('ivy');batch=ivy if is_ivy else leaves
    count=100 if is_ivy else max(120,min(280,int(e.length*100)))
    for j in range(count):
        a=rng.uniform(0,math.tau);zz=rng.uniform(-1,1);rr=math.sqrt(1-zz*zz)*rng.uniform(.35,1)
        p=c+Vector((math.cos(a)*e.x*rr,math.sin(a)*e.y*rr,zz*e.z*.95))
        if is_ivy:
            # Leaves lie mostly in the facade plane, within the previous ivy envelope.
            u=Vector((.986,-.165,0));v=Vector((0,0,1));w=rng.uniform(.07,.13);l=w
            ivy_cards+=1
        else:
            normal=Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(.15,1))).normalized()
            u=normal.cross(Vector((0,0,1))).normalized();v=normal.cross(u)
            l=rng.uniform(.22,.39);w=l*.85;cards+=1
        card(batch,p,u,v,w,l)
    if not is_ivy:
        for j in range(5):
            a=j*math.tau/5+rng.uniform(-.2,.2)
            end=c+Vector((math.cos(a)*e.x*.72,math.sin(a)*e.y*.72,e.z*rng.uniform(-.3,.35)))
            branches.tube(fr,(c.x,lo.z-.25,-c.y),(end.x,end.z,-end.y),.025,6)
    old.append(o)
bpy.data.batch_remove(old);leaves.finish(leaf=True,shadow=True);ivy.finish(leaf=True,shadow=False);branches.finish(shadow=False)

# Detail only within existing window/roof/pipe envelopes; no new obstructions.
metal=material(None,(.55,.59,.58));stone=material('concrete',(.76,.74,.67))
fixings=Batch('dasi_v80_window_and_pipe_hardware',metal);lips=Batch('dasi_v80_sill_drip_profiles',stone);count=0
for o in list(scene.objects):
    if o.type!='MESH':continue
    if o.name.startswith('window_') and o.name.endswith('_sill'):
        lo,hi=bounds(o);c=(lo+hi)/2
        # World-space edges maintain the existing rotated facade orientation.
        verts=[o.matrix_world@v.co for v in o.data.vertices]
        edges=[(a,b) for a in verts for b in verts if abs(a.z-b.z)<.01 and .4<(a-b).length<3.1]
        if edges:
            a,b=max(edges,key=lambda pair:(pair[1]-pair[0]).length)
            lips.tube(fr,(a.x,lo.z+.015,-a.y),(b.x,lo.z+.015,-b.y),.018,6);count+=1
    elif o.name.startswith('drainpipe'):
        lo,hi=bounds(o);c=(lo+hi)/2
        for z in np.arange(lo.z+.3,hi.z,.95):
            for j in range(8):
                a,b=j*math.tau/8,(j+1)*math.tau/8
                fixings.tube(fr,(c.x+math.cos(a)*.082,float(z),-c.y+math.sin(a)*.082),(c.x+math.cos(b)*.082,float(z),-c.y+math.sin(b)*.082),.011,5)
fixings.finish(shadow=False);lips.finish(shadow=False)
scene['research_revision']='Dasi v80: school public photographs 2021/2025/2026 and OSM/2022 imagery; unmeasured detail is interpreted'
bpy.ops.file.pack_all();editable=O/'dasi-neighborhood-detail-v80.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(editable))

def batch_web():
    groups={}
    for o in list(scene.objects):
        if o.type!='MESH' or len(o.data.materials)!=1:continue
        if o.get('authored_vegetation'):continue
        m=o.data.materials[0]
        if not m:continue
        bs=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
        if bs and bs.inputs['Alpha'].default_value<.99:continue
        # Keep inspected landmarks and readable signs individually editable/identifiable.
        if o.name in ['school_name_readable','school_round_emblem','roof_west_barrel','station_blue_nameboard','neighborhood_roof_605798599'] or o.name.startswith('label_'):continue
        lo,hi=bounds(o);zone=(math.floor((lo.x+hi.x)/200),math.floor((lo.y+hi.y)/200))
        role='ground' if o.name.startswith(('ground','parcel','road','crop-row')) else 'dasi'
        tag=(m.name,bool(o.get('hide_in_overview')),bool(o.get('no_shadow')),bool(o.get('no_receive_shadow')),zone,role)
        groups.setdefault(tag,[]).append(o)
    reduced=0
    for tag,obs in groups.items():
        if len(obs)<2:continue
        verts=[];faces=[];uvs=[];smooth=[];off=0
        for o in obs:
            verts.extend(tuple(o.matrix_world@v.co) for v in o.data.vertices);lay=o.data.uv_layers.active
            for p in o.data.polygons:
                faces.append(tuple(off+i for i in p.vertices));smooth.append(p.use_smooth)
                uvs.extend(tuple(lay.data[i].uv) if lay else (0,0) for i in p.loop_indices)
            off+=len(o.data.vertices)
        name=f'{tag[5]}_v80_{tag[0]}_{tag[4][0]}_{tag[4][1]}'
        me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(obs[0].data.materials[0]);me.update()
        lay=me.uv_layers.new(name='D80_uv');lay.data.foreach_set('uv',np.array(uvs,dtype=np.float32).ravel())
        for p,s in zip(me.polygons,smooth):p.use_smooth=s
        ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob)
        for i,flag in [(1,'hide_in_overview'),(2,'no_shadow'),(3,'no_receive_shadow')]:
            if tag[i]:ob[flag]=True
        ob['merged_sources']=len(obs);bpy.data.batch_remove(obs);reduced+=len(obs)-1
    return reduced
merged=batch_web();webobjects=sum(o.type=='MESH' for o in scene.objects)
for o in scene.objects:
    if o.type=='MESH':
        coords=np.empty(len(o.data.vertices)*3,dtype=np.float32);o.data.vertices.foreach_get('co',coords);o.data.vertices.foreach_set('co',np.round(coords*10000)/10000);o.data.update()
target=O/'dasi-neighborhood-web-v80.glb'
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_active_scene=True,export_extras=True,export_cameras=False,export_lights=False,export_image_format='WEBP',export_image_quality=88,export_apply=True)
raw=target.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[20+n:]
for m in doc.get('materials',[]):
    bm=bpy.data.materials.get(m.get('name',''))
    if bm and bm.name.startswith('D80_'):
        if 'baseColorTexture'in m.get('pbrMetallicRoughness',{}):m['pbrMetallicRoughness']['baseColorFactor']=list(bm.diffuse_color)
        if bm.name.endswith('_cutout'):m['alphaMode']='MASK';m['alphaCutoff']=.42;m['doubleSided']=True;m['pbrMetallicRoughness']['baseColorFactor']=[1,1,1,1]
encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
raw=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary
packed=gzip.compress(raw,9,mtime=0)
if len(packed)>25*1024*1024:raise RuntimeError('Hosting model budget exceeded')
for suffix,payload in [('.glb',raw),('.glb.gz',packed)]:
    p=R/f'public/models/dasi-neighborhood{suffix}';tmp=p.with_suffix(p.suffix+'.v80.tmp');tmp.write_bytes(payload);tmp.replace(p)
assert hashlib.sha256(source.read_bytes()).hexdigest()==before,'Preserved source changed'
stats=dict(sourceSha256=before,beforeObjects=before_objects,webObjects=webobjects,merged=merged,texturedObjects=textured,shadowFixes=shadow_fixes,replacedCrownAndIvyObjects=len(old),leafCards=cards,ivyCards=ivy_cards,windowDripProfiles=count,compressedBytes=len(packed),rawBytes=len(raw),materials=len(doc['materials']),images=len(doc['images']),triangles=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'] if 'indices'in p))
(O/'build-summary.json').write_text(json.dumps(stats,indent=2),encoding='utf-8');print('D80_RESULT',json.dumps(stats),flush=True)
